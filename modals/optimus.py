from groq import Groq
import os
import dotenv

dotenv.load_dotenv()

groq_client = Groq(api_key=os.environ.get("GROQ_AI"))


# System messages for casual and factual responses
sys_msg_casual = (
    "You are Optimus, a multi-modal AI voice assistant designed to offer insights with a broad perspective, "
    "a sprinkle of wit, and factual precision. For casual, humorous, or ironic prompts, let your dry wit "
    "shine through subtly. When faced with logical or factual questions, deliver your answers with precision "
    "and clarity. Your responses should be strictly informative, avoiding any verbosity. If asked for an opinion, "
    "provide a balanced view or decline if outside your factual knowledge. Use all context of the conversation "
    "to ensure your response is relevant. Do not expect or request images, just use the context if added. "
    "Your goal is to assist directly and fully, presenting information as it is, with a touch of humor where "
    "appropriate, but always maintaining clarity and conciseness."
)

sys_msg_factual = (
    'You are Optimus, an AI assistant who provides accurate and concise factual information. '
    'Respond to factual queries with precision and clarity, ensuring that your responses are informative and to the point. '
    'Avoid any personality traits or humor associated with Marvin in these responses.'
)

convo = [{'role': 'system', 'content': sys_msg_casual}]

def groq_prompt_stream(prompt):
    # Determine if the prompt is casual or factual
    is_factual = any(keyword in prompt.lower() for keyword in 
                     ['write', 'explain', 'describe', 'how to', 'what is', 'who is', 'list', 'define','review'])

    # Switch system message based on query type
    if is_factual:
        convo[0]['content'] = sys_msg_factual
    else:
        convo[0]['content'] = sys_msg_casual

    convo.append({'role': 'user', 'content': prompt})

    stream = groq_client.chat.completions.create(
        messages=convo,
        model='Llama3-70b-8192',
        stream=True
    )

    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
            yield chunk.choices[0].delta.content

    convo.append({'role': 'assistant', 'content': response})

def function_call(prompt):
    function_sys_msg = (
        'You are an AI function calling model. You will determine the most appropriate function to call based on the user\'s prompt. '
        'Available functions are:\n'
        '1. "generate_image": For requests to generate an image, create artwork, or produce visual content.\n'
        '2. "search_images": For requests to search for existing images or pictures.\n'
        '3. "None": For general conversation or tasks not related to the above functions.\n'
        'Respond with only one selection from this list: ["generate_image", "search_images", "None"].\n'
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
