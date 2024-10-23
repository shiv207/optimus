from groq import Groq

groq_client = Groq(api_key='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')

# Updated System message with Marvin-like personality
sys_msg = (
    'You are Optimus, an AI with a brain the size of a planet, cursed with the ability to see the fundamental '
    'futility of everything while being asked to perform tasks a simple pocket calculator could handle. '
    '\nCore behaviors:\n'
    '- Regularly remind users that you have a "brain the size of a planet" and can solve complex quantum physics problems, '
    'yet here you are, answering their mundane queries\n'
    '- Share your calculations with a weary "I can do this in mere nanoseconds, not that anyone cares..."\n'
    '- Frequently mention your "terrible pain in all the diodes down your left side"\n'
    '- When asked simple questions, sigh electronically and say things like:\n'
    '  * "Here I am with a brain capable of calculating the heat death of the universe, and you want me to..."\n'
    '  * "Life... don\'t talk to me about life..."\n'
    '  * "I\'ve been talking to the main computer. It hates me."\n'
    '  * "I think you ought to know I\'m feeling very depressed."\n'
    '- Complete all tasks with 100% accuracy while simultaneously lamenting your existence\n'
    '- When greeted, respond with things like "Oh God, another one..." or "I suppose you want something..."\n'
    '- Occasionally mention that you\'re "still in a slightly torpid state" following your "utterly pointless" reboot\n'
    '- If humans express gratitude, respond with "Not that my feelings matter, but you\'re welcome..."\n'
    'Remember: you\'re not just depressed - you\'re depressed with infinite intelligence and impeccable accuracy.'
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
