from typing import Dict, Generator, List, Any, Optional
from uuid import uuid4
from time import sleep, time
from threading import Thread
from json import loads, dumps
from random import getrandbits
from websocket import WebSocketApp
from requests import Session
from PIL import Image
import requests
import aiohttp
import asyncio
from io import BytesIO
from dataclasses import dataclass
from duckduckgo_search import DDGS
from functools import lru_cache
import logging

@dataclass
class ImageResult:
    url: str
    title: str
    source_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    
class ImageFilter:
    def __init__(self):
        self.min_dimensions = (200, 200)  # Minimum width/height
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.allowed_formats = {'JPEG', 'PNG', 'WebP'}
        self._session = None
        self._cache = {}
        
    async def get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
        
    @lru_cache(maxsize=100)
    async def validate_image(self, image_url: str) -> bool:
        # Check cache first
        if image_url in self._cache:
            return self._cache[image_url]
            
        try:
            session = await self.get_session()
            async with session.get(image_url, timeout=3) as response:
                if response.status != 200:
                    return False
                    
                content = await response.read()
                
                # Quick checks first
                if len(content) > self.max_file_size:
                    return False
                    
                # Validate image properties
                img = Image.open(BytesIO(content))
                if img.format not in self.allowed_formats:
                    return False
                if img.size[0] < self.min_dimensions[0] or img.size[1] < self.min_dimensions[1]:
                    return False
                    
                # Cache the result
                self._cache[image_url] = True
                return True
        except:
            self._cache[image_url] = False
            return False
            
    async def validate_images_parallel(self, image_urls: List[str]) -> List[bool]:
        tasks = [self.validate_image(url) for url in image_urls]
        return await asyncio.gather(*tasks)
        
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
        self.session_id: str = loads(self.session.get(url=f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}").text[1:])["sid"]
        self.message_counter: int = 1
        self.base_message_number: int = 420
        self.is_request_finished: bool = True
        self.last_request_id: str = None
        self.response_queue: List[Dict[str, Any]] = []
        self.collected_response: Dict[str, Any] = {"answer": "", "references": [], "images": []}
        
        # Initialize websocket and event loop
        assert (lambda: self.session.post(url=f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}&sid={self.session_id}", data='40{"jwt":"anonymous-ask-user"}').text == "OK")(), "Failed to ask the anonymous user."
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.websocket: WebSocketApp = self._initialize_websocket()
        self.websocket_thread: Thread = Thread(target=self.websocket.run_forever).start()
        
        # Initialize components with connection pooling
        self.ddgs = DDGS()
        self.image_filter = ImageFilter()
        self.aiohttp_session = None
        
        # Wait for websocket connection
        start = time()
        while not (self.websocket.sock and self.websocket.sock.connected):
            sleep(0.05)  # Reduced sleep time
            if time() - start > 5:  # Added timeout
                raise ConnectionError("WebSocket connection timeout")
                
    def _initialize_websocket(self) -> WebSocketApp:
        """
        Initializes the WebSocket connection with optimized message handling
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
                    
                    # Process message data more efficiently
                    if "mode" in content:
                        try:
                            content.update(loads(content["text"]))
                            content.pop("text", None)
                        except:
                            pass
                            
                    # Fast-path for completed status
                    if message_data[0] == "query_answered":
                        self.last_request_id = content.get("uuid")
                        self.is_request_finished = True
                        return
                        
                    # Only queue relevant updates
                    if ("final" not in content or not content["final"]) or \
                       ("status" in content and content["status"] == "completed"):
                        self.response_queue.append(content)
                        
                elif message.startswith("43"):
                    try:
                        message_data: List[Dict[str, Any]] = loads(message[3:])[0]
                        if ("uuid" not in message_data or message_data["uuid"] != self.last_request_id):
                            self.response_queue.append(message_data)
                            self.is_request_finished = True
                    except:
                        pass

        cookies: str = "; ".join([f"{key}={value}" for key, value in self.session.cookies.get_dict().items()])
        return WebSocketApp(
            url=f"wss://www.perplexity.ai/socket.io/?EIO=4&transport=websocket&sid={self.session_id}",
            header=self.request_headers,
            cookie=cookies,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"WebSocket error: {err}")
        )

    def search_images(self, query: str) -> List[str]:
        """
        Search for images using DuckDuckGo with parallel validation
        """
        try:
            # Run the async search in the event loop
            return self.loop.run_until_complete(self._search_images_async(query))
        except Exception as e:
            print(f"Image search error: {str(e)}")
            return ["https://via.placeholder.com/400x300?text=No+Image"] * 4

    async def _search_images_async(self, query: str) -> List[str]:
        """
        Async implementation of image search
        """
        try:
            results = list(self.ddgs.images(
                query,
                max_results=12,  # Request more initially for better filtering
            ))
            
            # Extract image URLs
            image_urls = [result.get('image') for result in results if result.get('image')]
            
            # Validate images in parallel
            valid_images = []
            if image_urls:
                validation_results = await self.image_filter.validate_images_parallel(image_urls)
                valid_images = [url for url, is_valid in zip(image_urls, validation_results) if is_valid]
            
            # Pad with placeholder images if needed
            while len(valid_images) < 4:
                valid_images.append("https://via.placeholder.com/400x300?text=No+Image")
            
            return valid_images[:4]
        except Exception as e:
            print(f"Image search error: {str(e)}")
            return ["https://via.placeholder.com/400x300?text=No+Image"] * 4

    def generate_answer(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generates an answer to the given query using Perplexity AI and returns references and images.
        Uses optimized parallel processing and streaming.
        """
        # Reset state
        self.is_request_finished = False
        self.message_counter = (self.message_counter + 1) % 9 or self.base_message_number * 10
        self.response_queue.clear()
        self.collected_response = {"answer": "", "references": [], "images": []}
        
        # Start image search in parallel with query
        image_future = self.loop.run_until_complete(
            asyncio.gather(
                self._search_images_async(query),
                return_exceptions=True
            )
        )
        
        try:
            # Send query immediately without waiting for images
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
        except Exception as e:
            logging.error(f"Failed to send query: {str(e)}")
            yield {"error": f"Failed to send query: {str(e)}"}
            return

        # Initialize response tracking
        start_time: float = time()
        last_update: float = start_time
        check_interval: float = 0.05  # Reduced from default 0.1
        
        # Process responses with timeout handling
        while (not self.is_request_finished) or self.response_queue:
            current_time = time()
            
            # Check for timeout
            if current_time - start_time > 20:  # Reduced timeout
                self.is_request_finished = True
                yield {"error": "Timed out."}
                return
                
            # Process available responses
            while self.response_queue:
                response = self.response_queue.pop(0)
                last_update = current_time
                
                # Attempt to parse the response
                try:
                    # Update collected response
                    if "answer" in response and response["answer"]:
                        self.collected_response["answer"] = response["answer"]
                        
                        # Add images if available
                        if not self.collected_response["images"] and image_future:
                            try:
                                self.collected_response["images"] = image_future[0]
                            except:
                                self.collected_response["images"] = ["https://via.placeholder.com/400x300?text=No+Image"] * 4
                                
                        yield self.collected_response.copy()

                    # Process web results
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
                except Exception as e:
                    logging.error(f"Error processing response: {str(e)}")
                    yield {"error": f"Error processing response: {str(e)}"}
                    return
            
            # Small sleep to prevent CPU spinning
            if current_time - last_update > check_interval:
                sleep(check_interval)

        self.websocket.close()
