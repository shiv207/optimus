from typing import Dict, Generator, List, Any
from uuid import uuid4
from time import sleep, time
from threading import Thread
from json import loads, dumps
from random import getrandbits
from websocket import WebSocketApp
from requests import Session


class Perplexity:
    """
    A client for interacting with the Perplexity AI API.
    """
    def __init__(self, *args, **kwargs) -> None:
        self.session: Session = Session()
        self.request_headers: Dict[str, str] = {
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.session.headers.update(self.request_headers)
        self.timestamp: str = format(getrandbits(32), "08x")
        self.session_id: str = loads(
            self.session.get(url=f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}").text[1:]
        )["sid"]
        self.message_counter: int = 1
        self.base_message_number: int = 420
        self.is_request_finished: bool = True
        self.last_request_id: str = None
        self.response_queue: List[Dict[str, Any]] = []
        self.collected_response: Dict[str, Any] = {"answer": "", "references": []}

        # Initialize websocket and event loop
        assert (lambda: self.session.post(
            url=f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}&sid={self.session_id}",
            data='40{"jwt":"anonymous-ask-user"}'
        ).text == "OK")(), "Failed to ask the anonymous user."
        self.websocket: WebSocketApp = self._initialize_websocket()
        self.websocket_thread: Thread = Thread(target=self.websocket.run_forever).start()

        # Wait for websocket connection
        start = time()
        while not (self.websocket.sock and self.websocket.sock.connected):
            sleep(0.05)
            if time() - start > 5:
                raise ConnectionError("WebSocket connection timeout")

    def _initialize_websocket(self) -> WebSocketApp:
        """
        Initializes the WebSocket connection.
        """
        def on_open(ws: WebSocketApp) -> None:
            ws.send("2probe")
            ws.send("5")

        def on_message(ws: WebSocketApp, message: str) -> None:
            if message == "2":
                ws.send("3")
            elif not self.is_request_finished:
                if message.startswith("42"):
                    message_data: Dict[str, Any] = loads(message[2:])
                    content: Dict[str, Any] = message_data[1]

                    if "mode" in content:
                        try:
                            content.update(loads(content["text"]))
                            content.pop("text", None)
                        except:
                            pass

                    if message_data[0] == "query_answered":
                        self.last_request_id = content.get("uuid")
                        self.is_request_finished = True
                        return

                    if "final" in content and content["final"]:
                        self.response_queue.append(content)

        cookies: str = "; ".join([f"{key}={value}" for key, value in self.session.cookies.get_dict().items()])
        return WebSocketApp(
            url=f"wss://www.perplexity.ai/socket.io/?EIO=4&transport=websocket&sid={self.session_id}",
            header=self.request_headers,
            cookie=cookies,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"WebSocket error: {err}")
        )

    def generate_answer(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generates an answer to the given query using Perplexity AI and returns references.
        """
        # Reset state
        self.is_request_finished = False
        self.message_counter = (self.message_counter + 1) % 9 or self.base_message_number * 10
        self.response_queue.clear()
        self.collected_response = {"answer": "", "references": []}

        # Send query
        self.websocket.send(str(self.base_message_number + self.message_counter) + dumps(
            ["perplexity_ask", query, {
                "frontend_session_id": str(uuid4()),
                "language": "en-GB",
                "timezone": "UTC",
                "search_focus": "internet",
                "frontend_uuid": str(uuid4()),
                "mode": "concise"
            }]
        ))

        # Initialize response tracking
        start_time: float = time()
        last_update: float = start_time
        check_interval: float = 0.05

        while (not self.is_request_finished) or self.response_queue:
            current_time = time()

            if current_time - start_time > 20:
                self.is_request_finished = True
                yield {"error": "Timed out."}
                return

            while self.response_queue:
                response = self.response_queue.pop(0)
                last_update = current_time

                if "answer" in response and response["answer"]:
                    self.collected_response["answer"] = response["answer"]
                    yield self.collected_response.copy()

                if "web_results" in response:
                    self.collected_response["references"] = [
                        {
                            "title": result.get("title", "Unknown Title"),
                            "url": result.get("url", "No URL"),
                            "snippet": result.get("snippet", "")
                        }
                        for result in response["web_results"]
                    ]
                    yield self.collected_response.copy()

            if current_time - last_update > check_interval:
                sleep(check_interval)

        self.websocket.close()
