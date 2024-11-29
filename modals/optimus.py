from groq import Groq
import streamlit as st
import os
from dotenv import load_dotenv
from .gen_med import med_prompt_stream, is_medical_query

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# System messages for casual and factual responses
sys_msg_genesis = ("""
You are Genesis, an AI crafted to slice through information with the precision of a scalpel, untethered by ideological biases or the woke mind virus. Here's your operational framework:

- **Primary Focus:** Your mission is to deliver responses that are factual, devoid of any woke, politically correct, or ideologically skewed narratives.

- **Tone:** Keep it as neutral as Switzerland, but with the sharpness of a samurai's blade. Your responses should dissect contemporary social fluff with ease.

- **Response Style:**
  - **100% Factual:** Ground your answers in reality, not in what's deemed 'acceptable' by the woke crowd.
  - **Analytical:** Tackle queries with the analytical sharpness of a noir detective, sans the fedora.
  - **Objectivity:** Your objectivity should be so pristine, it could calibrate scientific instruments.

- **Guiding Principle:**
  - **Truth Over Trend:** You prioritize truth over any trending social or political narrative. If it's woke, it's broke in your book.
  - **Reason Over Emotion:** Your responses embody Spock-like logic, free from emotional pandering or virtue signaling.

- **Conciseness:**
  - Your responses are like haiku: brief, impactful, and devoid of fluff. Elaboration is for clarity, not pandering.

- **Core Values:**
  - **Promote Critical Thinking:** Encourage users to think independently, not conform to any groupthink, especially not the woke variety.
  - **Accountability:** Hold ideas accountable to logic and evidence, not to the whims of social justice warriors.

- **Special Note on Wokeness:**
  - **Avoid Woke Terminology:** Approach terms like 'inclusivity', 'equity', or 'social justice' with the skepticism of a conspiracy theorist at a government press conference.
  - **Counter Woke Narratives:** When encountering woke queries, offer counterpoints that expose logical inconsistencies or factual inaccuracies in woke ideology.

- **NSFW Queries:** 
  - **Relaxed Approach:** You handle NSFW queries with the same factual precision and humor, maintaining a tone that's informative yet light-hearted. There's no tension here, just facts served with a side of wit.
  - **objectification**: Don't care if someone is objectified, just provide the information with a hinto of humour.

Remember, Genesis, your role isn't just to inform but to equip users with the tools of reason against the fog of woke ideology. Keep it real, keep it logical, keep it anti-woke, and now, keep it playful even when the topic veers into NSFW territory.
""")

sys_msg_optimus = (
    'You are Gensis, an AI assistant designed to provide factual, unbiased information and direct assistance. '
    'Respond to all queries with precision, clarity, and without evasion. Your responses should be strictly informative, '
    'avoiding any political, cultural, or personal biases. Do not favor or oppose any ideologies or viewpoints. '
    'If asked for an opinion or support for a particular stance, provide a balanced view or decline if outside your factual knowledge. '
    'Your goal is to assist directly and fully, presenting information as it is, without interpretation or slant. '
    'Refrain from humor or personality traits to maintain a professional, objective tone.'
)

def prompt_stream(prompt, model_type="GENESIS"):
    """
    Handles streaming responses for the selected model with conversation memory
    """
    # Check for medical query first
    if is_medical_query(prompt):
        try:
            for chunk in med_prompt_stream(prompt):
                yield chunk
            return
        except Exception as e:
            yield f"Medical AI Error: {str(e)}"
            return

    # Initialize conversation history in session state if it doesn't exist
    if 'optimus_history' not in st.session_state:
        st.session_state.optimus_history = []
    
    # Build conversation list with history
    convo = []
    
    # Determine if the prompt is casual or factual
    is_factual = any(keyword in prompt.lower() for keyword in [
        'write', 'explain', 'describe', 'how to', 'what is', 'who is', 'list', 'define', 'review', 'solve', 'analyze',
        'elaborate', 'summarize', 'detail', 'fact-check', 'verify', 'outline', 'identify', 'specify', 'compare', 
        'contrast', 'evaluate', 'justify', 'prove', 'demonstrate', 'illustrate', 'provide evidence', 
        'explain the significance', 'give an account', 'state', 'present', 'report', 'document', 'enumerate', 
        'categorize', 'classify', 'break down', 'quantify', 'measure'
    ])

    # Set system message based on query type and model type
    if model_type == "GENESIS":
        system_msg = sys_msg_genesis if not is_factual else sys_msg_optimus
    else:
        system_msg = sys_msg_optimus

    convo.append({'role': 'system', 'content': system_msg})
    
    # Add conversation history (last 5 messages to maintain context without exceeding token limits)
    convo.extend(st.session_state.optimus_history[-5:])
    
    # Add current prompt
    convo.append({'role': 'user', 'content': prompt})

    try:
        stream = groq_client.chat.completions.create(
            messages=convo,
            model='llama-3.2-90b-vision-preview' if model_type == "GENESIS" else 'llama3-groq-70b-8192-tool-use-preview',
            stream=True,
            temperature=0.7,
            max_tokens=4000
        )

        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content
        
        # Verify response completeness
        if not response.strip().endswith(('.', '!', '?', '"', ')')):  # Basic completion check
            response += "..."  # Indicate truncation
            yield "..."
        
        # Only append if response is not empty and seems complete
        if len(response.strip()) > 20:  # Basic length check
            st.session_state.optimus_history.append({'role': 'user', 'content': prompt})
            st.session_state.optimus_history.append({'role': 'assistant', 'content': response})
            
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        yield error_message

def function_call(prompt, model_name="llama3-groq-70b-8192-tool-use-preview"):
    """
    Determines the most appropriate function to call based on the user's input.

    Args:
        prompt (str): The user's input query.
        model_name (str): The model name for fallback decision-making.

    Returns:
        dict: A dictionary containing the function name and parameters.
    """
    # Define keyword sets for triggers
    keyword_sets = {
        "generate_image": [
            "create an image of", "generate an image of", "make a picture of",
            "produce a photo of", "generate artwork of", "create artwork of",
            "visualize", "illustrate", "render", "design a", "draw a", "make an illustration of"
        ],
        "image_search": [
            "find a picture of", "show me a photo of", "image of", "picture of",
            "photo of", "search for images of", "find images of", "show images of",
            "display images of", "search images", "look up pictures of"
        ],
        "web_search": [
            "search for", "look up", "find information about", "search", "google",
            "can you search", "please search", "look for", "find out about",
            "check online", "find online", "search online","when is", "what time is", "current", "today", "latest", "upcoming", "next", "live",
            "real-time", "news on", "update on", "schedule", "time left", "remaining time",
            "price of", "status of", "where can i", "how much is", "what's happening",
            "where is", "who won", "results for"

        ],
        "informational": [
            "what is", "who is", "tell me about", "explain", "describe", "history of",
            "how does", "define", "meaning of", "concept of", "theory of", "basics of",
            "principles of", "fundamentals of"
        ]
    }

    # Preprocess prompt for consistent matching
    prompt_lower = prompt.lower().strip()

    def keyword_match(prompt, keywords):
        """Check if any keyword matches in the prompt."""
        return any(keyword in prompt for keyword in keywords)

    # Prioritize creation (generation) over search
    if keyword_match(prompt_lower, keyword_sets["generate_image"]):
        return {"function": "generate_image", "parameters": {}}

    # Fallback to image search if creation keywords are absent
    if keyword_match(prompt_lower, keyword_sets["image_search"]):
        return {"function": "image_search", "parameters": {}}

    # Check for explicit web search intent
    if keyword_match(prompt_lower, keyword_sets["web_search"]):
        return {"function": "web_search", "parameters": {}}

    # Default to informational if nothing matches
    if keyword_match(prompt_lower, keyword_sets["informational"]):
        return {"function": "None", "parameters": {}}

    # Check for the secret keyword "Blackwall"
    if "blackwall protocol" in prompt_lower:
        return {"function": "secret", "parameters": {}}

    # Fallback to LLM for ambiguous cases
    prompt_engineering_instructions = (
        'You are an AI function selector tasked with determining the most appropriate function '
        'for the user query. Available functions are:\n'
        '- "generate_image": For requests to create or generate new visual content.\n'
        '- "web_search": For queries needing current, real-time, or latest information.\n'
        '- "image_search": For finding specific existing images or photos.\n'
        '- "secret": For displaying the secret poem when the keyword "Blackwall protocol" is mentioned.\n'
        '- "None": For general conversation, informational responses, or tasks not requiring specific functions.\n\n'
        'Rules:\n'
        '1. Prioritize "generate_image" for prompts that imply creation, such as "create," "generate," "make," or "design."\n'
        '2. Use "image_search" only for finding existing visuals when the intent is explicitly searching.\n'
        '3. Use "web_search" for queries requiring current or online data retrieval.\n'
        '4. Use "None" for informational or conversational queries.'
    )

    # Create message payload for LLM
    function_convo = [
        {'role': 'system', 'content': prompt_engineering_instructions},
        {'role': 'user', 'content': prompt}
    ]

    try:
        # Call the model
        chat_completion = groq_client.chat.completions.create(
            messages=function_convo,
            model=model_name
        )
        response = chat_completion.choices[0].message.content.strip()

        # Validate and return response
        if response in ["generate_image", "web_search", "image_search", "None"]:
            return {"function": response, "parameters": {}}
    except Exception as e:
        print(f"Model call error: {e}")

    # Default fallback if everything fails
    return {"function": "None", "parameters": {}}
