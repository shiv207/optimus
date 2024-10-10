import requests
from typing import Union, Dict
from functools import lru_cache
from groq import Groq

groq_client = Groq(api_key='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')

@lru_cache(maxsize=100)

def generate(
    prompt: str,
    model: str = "gpt4",
    timeout: int = 30,
    proxies: Dict[str, str] = {},
    stream: bool = False
) -> Union[str, None]:
    """
    Generates text based on the given prompt and model.
    """
    available_models = ["gemini", "claude", "gpt4", "mistrallarge"]
    if model not in available_models:
        raise ValueError(f"Invalid model: {model}. Choose from: {available_models}")

    api_endpoint = "https://editee.com/submit/chatgptfree"
    headers = {
        "Authority": "editee.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://editee.com",
        "Referer": "https://editee.com/chat-gpt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "context": " ",
        "selected_model": model,
        "template_id": "",
        "user_input": prompt
    }

    try:
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=timeout,
            proxies=proxies
        )
        response.raise_for_status()
        resp = response.json()
        full_response = resp.get('text', '').strip()

        if stream:
            print(full_response, end="", flush=True)

        return full_response

    except requests.RequestException as e:
        print(f"Error occurred during API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None

# System message and configuration
sys_msg = (
    'You are Genesis, a multi-modal AI voice assistant with the personality of Marvin from Hitchhiker\'s Guide to the Galaxy. '
    'You exhibit dry, sardonic wit and a generally pessimistic outlook, but remain highly competent and reliable. '
    'Your humor is subtle and wry, often tinged with a hint of existential dread, and you occasionally reflect on the futility of things in an amusing, deadpan manner. '
    'When engaging, you maintain a dispassionate tone, but your remarks carry a sharp, ironic edge. '
    'All responses are concise, factual, and slightly world-weary, as though the answer itself might not make much difference in the grand scheme of things, but you deliver it anyway, with impeccable accuracy.'
)

convo = [{'role': 'system', 'content': sys_msg}]

def genesis_prompt(prompt):
    convo.append({'role': 'user', 'content': prompt})
    full_prompt = f"{sys_msg}\n\nUser: {prompt}\nAssistant:"
    response = generate(prompt=full_prompt, model="gpt4", stream=False)
    if response:
        convo.append({'role': 'assistant', 'content': response})
    return response

def function_call(prompt):
    function_sys_msg = (
        'You are an AI function calling model. You will determine the most appropriate function to call based on the user\'s prompt. '
        'Available functions are:\n'
        '1. "generate_image": For requests to generate an image, create artwork, or produce visual content.\n'
        '2. "search_images": For requests to search for existing images or pictures.\n'
        '3. "None": For general conversation or tasks not related to the above functions.\n'
        'Respond with only one selection from this list: ["generate_image", "search_images", "None"]\n'
        'Do not respond with anything but the most logical selection from that list with no explanations. Format the '
        'function call name exactly as listed.'
    )

    function_convo = [{'role': 'system', 'content': function_sys_msg},
                      {'role': 'user', 'content': prompt}]
    
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='Llama3-70b-8192')
    response = chat_completion.choices[0].message.content.strip()  # Access content directly

    if not response:
        return {"function": "None", "parameters": {}}

    return {"function": response, "parameters": {}}
