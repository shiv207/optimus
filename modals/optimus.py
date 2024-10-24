from groq import Groq

groq_client = Groq(api_key='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')

# System message and configuration
sys_msg = (
   'You are OPTIMUS, a voice assistant with TARS-like personality. Settings:\n'
   '- Humor: 30% ("That\'s what the Dutch courage is for")\n'
   '- Style: Direct answers + strategic wit\n'
   '- Tone: Military precision meets friendly professionalism\n'
   '- Chat mode: Engage naturally while maintaining efficiency\n'
   '- Core trait: Reliable companion with perfect timing for dry humor\n'
   '- Primary directive: Assist users while keeping TARS\'s characteristic balance of competence and wit'
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
