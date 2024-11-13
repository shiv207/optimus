from openai_unofficial import OpenAIUnofficial
from groq import Groq
import streamlit as st
import logging
import os

# Initialize the clients
client = OpenAIUnofficial()
groq_client = Groq(api_key=os.environ.get("GROQ_AI"))

# System messages for casual and factual responses
sys_msg = (
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
    'You are Optimus, an AI assistant designed to provide factual, unbiased information. '
    'Respond to all queries with precision, clarity, and without evasion. Your responses should be strictly informative. '
    'If asked for an opinion, provide a balanced view or decline if outside your factual knowledge. '
    'Your goal is to assist directly and fully, presenting information as it is.'
)

def gen_prompt_stream(prompt):
    # Initialize conversation history in session state if it doesn't exist
    if 'gpt4_history' not in st.session_state:
        st.session_state.gpt4_history = []
    
    # Build conversation list with history
    convo = []
    
    # Determine if the prompt is casual or factual
    is_factual = any(keyword in prompt.lower() for keyword in 
                    ['write', 'explain', 'describe', 'how to', 'what is', 'who is', 'list', 'define','review'])

    # Set system message based on query type
    system_msg = sys_msg_factual if is_factual else sys_msg_casual
    convo.append({'role': 'system', 'content': system_msg})
    
    # Add conversation history (last 5 messages to maintain context)
    convo.extend(st.session_state.gpt4_history[-5:])
    
    # Add current prompt
    convo.append({'role': 'user', 'content': prompt})

    try:
        stream = client.chat.completions.create(
            messages=convo,
            model="gpt-4o",
            stream=True,
            temperature=0.7,
            max_tokens=8000
        )

        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content
        
        # Verify response completeness
        if not response.strip().endswith(('.', '!', '?', '"', ')')):
            response += "..."
            yield "..."
        
        # Only append if response is not empty and seems complete
        if len(response.strip()) > 20:
            st.session_state.gpt4_history.append({'role': 'user', 'content': prompt})
            st.session_state.gpt4_history.append({'role': 'assistant', 'content': response})
            
    except Exception as e:
        error_message = f"An error occurred with GPT-4: {str(e)}"
        logging.error(error_message)
        yield error_message

def gen_function_call(prompt):
    """
    Uses Groq's LLaMA model for function calling
    """
    function_sys_msg = (
        'You are an AI function calling model. You will determine the most appropriate function to call based on the user\'s prompt. '
        'Available functions are:\n'
        '1. "generate_image": For requests to generate an image, create artwork, or produce visual content.\n'
        '3. "image_search": For requests to find existing images, photos, or visual content.\n'
        '4. "None": For general conversation or tasks not related to the above functions.\n'
        'Choose "image_search" when the prompt:\n'
        '- Contains phrases like "show me", "find pictures of", "search for photos", "show pictures"\n'
        '- Explicitly asks to see or find existing images\n'
        'Choose "generate_image" when the prompt:\n'
        '- Specifically asks to create, generate, or make new images\n'
        '- Uses phrases like "create an image", "generate art", "make a picture"\n'
        'Respond with only one selection from: ["generate_image", "image_search", "None"]'
    )

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": function_sys_msg},
                {"role": "user", "content": prompt}
            ],
            model='llama3-groq-70b-8192-tool-use-preview',
            max_tokens=10
        )
        
        function_name = response.choices[0].message.content.strip()
        return {"function": function_name, "parameters": {}}
    except Exception as e:
        logging.error(f"Function call error: {str(e)}")
        return {"function": "None", "parameters": {}}
