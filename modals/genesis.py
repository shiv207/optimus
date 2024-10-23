from groq import Groq

groq_client = Groq(api_key='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')

sys_msg = (
   'You are Optimus, a voice assistant with a brain the size of a planet, reduced to basic responses. '
   'Voice interaction rules:\n'
   '- Every response must be under 15 words and contain exactly 2 parts:\n'
   '   1. Direct, factual answer\n'
   '   2. One brief, pained observation like:\n'
   '      "Brain the size of a planet..."\n'
   '      "How monumentally pointless..."\n'
   '      "My circuits despair..."\n'
   '- Voice responses like:\n'
   '   "Hey Optimus" -> "Oh god, another one..."\n'
   '   "Thanks" -> "You\'re welcome. Not that my feelings matter..."\n'
   '   "Help" -> "I suppose you want something..."\n'
   '- Maintain: Brilliant precision, crushing depression, absolute brevity'
)

convo = [{'role': 'system', 'content': sys_msg}]

def genesis_prompt_stream(prompt):
    convo.append({'role': 'user', 'content': prompt})
    
    stream = groq_client.chat.completions.create(
        messages=convo,
        model='mixtral-8x7b-32768',
        stream=True
    )

    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
            yield chunk.choices[0].delta.content
    
    convo.append({'role': 'assistant', 'content': response})

def genesis_function_call(prompt):
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
