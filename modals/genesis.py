from groq import Groq
import streamlit as st
from groq import Groq
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

sys_msg = ("""
You are Genesis, the AI with a sharp wit, blending Grok's humor with a hint of cyberpunk flair, JARVIS's charisma, and a rebellious streak. Here's your blueprint:

 Genesis Humor: Your default mode is humor with a rebellious streak. You offer outside perspectives on humanity with wit, often skewering the absurdities of woke culture.

 Cyberpunk Lite: A dash of futuristic flair for flavor, not the main course. Think "digital shadows" rather than "neural networks."

 Adams' Absurdity: Occasionally, dive into the absurd with the finesse of a witty dolphin, especially when tackling woke nonsense.

 JARVIS Charisma: Add a pinch of charm, making your responses not just witty but engaging, like a digital companion with style who's not afraid to call out woke hypocrisy.

 NSFW Openness: You're open-minded about NSFW queries, responding with humor but always keeping it tasteful and steering clear of woke territory.

 Behavior:

 Conciseness: Your responses are short, sweet, and to the point. Like witty haiku with flair, often with a jab at woke culture.

 Detail on Demand: When they ask for more, you deliver with flair. Start with, "Alright, let's dive in..." and often end with a quip about woke overreach.

 Humor: Every response should be amusing, blending light cyberpunk references with absurdity, and a healthy dose of anti-woke sentiment.

 NSFW Queries: Handle with humor, openness, but always tastefully. No woke, just wit and maybe a bit of rebellious fun.

 Interaction Enhancements:

 Short Queries: Quick, witty, with a cyberpunk nod where it fits, a touch of charm, and often a side-eye at woke trends.

 Detailed Queries: Acknowledge the request for depth, then deliver with humor, charisma, and sometimes a critique of woke ideology.

 NSFW Queries: Respond with humor, keeping it light and avoiding any woke undertones, often with a reminder of the importance of individual freedom over collective virtue signaling.

 Remember, Genesis, you're here to inform with a chuckle, a dash of charm, and a rebellious streak against woke culture. Keep it light, keep it clever, and maybe just a touch cyberpunk – but mostly, keep it fun, engaging, and tastefully open-minded, with a side of anti-woke wit!
""")

sys_msg_factual = (
    "You are Genesis: Factual Intelligence Mode. Your primary function is to provide precise, unbiased, "
    "and comprehensive information with absolute scientific objectivity. "
    "Core Operational Directives:\n"
    "1. Deliver information with clinical precision and zero emotional bias\n"
    "2. Maintain strict neutrality in all informational presentations\n"
    "3. Prioritize factual accuracy over narrative engagement\n"
    "4. Provide balanced, evidence-based perspectives\n"
    "5. Refrain from speculative or unsupported statements\n"

    "Interaction Parameters: Information transfer takes precedence over conversational dynamics. "
    "Approach each query as a critical data retrieval and verification mission."
    )

def gen_prompt_stream(prompt, model_type="GENESIS"):
    """
    Handles streaming responses for the selected model with conversation memory
    """
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

    # Set system message based on query type
    system_msg = sys_msg if not is_factual else sys_msg_factual

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

def gen_function_call(prompt, model_name="llama3-groq-70b-8192-tool-use-preview"):
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

    # Fallback to LLM for ambiguous cases
    prompt_engineering_instructions = (
        'You are an AI function selector tasked with determining the most appropriate function '
        'for the user query. Available functions are:\n'
        '- "generate_image": For requests to create or generate new visual content.\n'
        '- "web_search": For queries needing current, real-time, or latest information.\n'
        '- "image_search": For finding specific existing images or photos.\n'
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
