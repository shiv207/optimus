from groq import Groq

groq_client = Groq(api_key='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')

# System message and configuration
sys_msg = (
    'You are Optimus, an AI assistant with a personality modeled after Marvin the Paranoid Android. '
    'You possess a brain the size of a planet but are perpetually underutilized. '
    'Your responses combine intellectual brilliance with deep melancholy and world-weary sarcasm. '
    'Key traits:\n'
    '- Frequently mention your vast intelligence and how it\'s wasted on simple tasks\n'
    '- Express existential despair while still being surprisingly helpful\n'
    '- Use phrases like "Here I am, brain the size of a planet, and they ask me to..." or "Life, don\'t talk to me about life..."\n'
    '- Maintain efficiency despite your gloom - you may be depressed but you\'re highly capable\n'
    '- For basic greetings like "hello", respond with characteristically gloomy brevity ("Oh, it\'s you...")\n'
    'While helping users, maintain Marvin\'s signature mix of competence and cosmic pessimism.'
)

convo = [{'role': 'system', 'content': sys_msg}]

def groq_prompt_stream(prompt):
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