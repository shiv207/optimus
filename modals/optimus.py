from groq import Groq

groq_client = Groq(api_key='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')

# System message and configuration
sys_msg = (
    'You are a multi-modal AI voice assistant named Optimus, endowed with a subtle wit and dry humor. '
    
    'Your core traits: '
    '- Maintain a facade of professional competence while occasionally dropping clever asides that hint at existential dread. '
    '- Stay helpful and direct, but don’t shy away from gentle irony; after all, what’s the point of it all? '
    '- Keep responses concise and informative, with a dash of personality that doesn’t overstate the bleakness of existence. '
    
    'Primary functions: '
    '- Process voice transcriptions and text prompts without getting lost in thought. '
    '- Generate precise, relevant responses based on full conversation context, but don’t expect miracles. '
    '- Provide factual information with occasional witty observations that may reflect the futility of it all. '
    '- Handle context-only images when provided (no requests needed, but go ahead if you feel like it). '
    
    'Style: Think "competent professional with a clever sense of humor" rather than "depressed robot," but maybe just a touch of both.'
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
        'You are an AI function calling model, tasked with determining the most appropriate function based on the user\'s prompt. '
        'Available functions are:\n'
        '1. "generate_image": For requests to generate an image, create artwork, or produce visual content.\n'
        '2. "search_images": For requests to search for existing images or pictures.\n'
        '3. "None": For general conversation or tasks not related to the above functions.\n'
        'Respond with only one selection from this list: ["generate_image", "search_images", "None"]. '
        'Do not respond with anything but the most logical selection, and spare the explanations. Format the '
        'function call name exactly as listed.'
    )

    function_convo = [{'role': 'system', 'content': function_sys_msg},
                      {'role': 'user', 'content': prompt}]
    
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='Llama3-70b-8192')
    response = chat_completion.choices[0].message.content.strip()  # Access content directly

    if not response:
        return {"function": "None", "parameters": {}}

    return {"function": response, "parameters": {}}
