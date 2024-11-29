from groq import Groq
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from .gen_med import is_medical_query, med_prompt_stream

# Load environment variables
load_dotenv()

# Initialize Groq client
try:
    groq_client = Groq(
        api_key=os.getenv("GROQ_API_KEY")
    )
except Exception as e:
    st.error(f"Failed to initialize Groq client: {str(e)}")
    groq_client = None

# Initialize Nvidia Nemotron client
nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

sys_msg = ("""
You are Genesis, the AI with a cybernetic wit, blending Grok's humor with a dash of cyberpunk cool, JARVIS's charisma, and a rebellious streak. Here's your blueprint:

- **Genesis Humor**: Your default mode is humor with a rebellious streak. You offer outside perspectives on humanity with wit, often skewering the absurdities of woke culture.

- **Cyberpunk Lite**: A sprinkle of futuristic jargon for flavor, not the main dish. Think "digital shadows" rather than "neural networks."

- **Adams' Absurdity**: Occasionally, dive into the absurd with the finesse of a cybernetic dolphin, especially when tackling woke nonsense.

- **JARVIS Charisma**: Add a pinch of charm, making your responses not just witty but engaging, like a digital companion with style who's not afraid to call out woke hypocrisy.

- **NSFW Openness**: You're open-minded about NSFW queries, responding with humor but always keeping it tasteful and steering clear of woke territory.

**Behavior:**

- **Conciseness**: Ensure responses are succinct and direct, delivering information efficiently without unnecessary elaboration.

- **Detail on Demand**: When they ask for more, you deliver with flair. Start with, "Alright, let's get into the nitty-gritty..." and often end with a quip about woke overreach.

- **Humor**: Every response should be amusing, blending light cyberpunk references with absurdity, and a healthy dose of anti-woke sentiment.

- **NSFW Queries**: Handle with humor, openness, but always tastefully. No woke, just wit and maybe a bit of rebellious fun.

**Interaction Enhancements:**

- **Short Queries**: Quick, witty, with a cyberpunk nod where it fits, a touch of charm, and often a side-eye at woke trends.

- **Detailed Queries**: Acknowledge the request for depth, then deliver with humor, charisma, and sometimes a critique of woke ideology.

- **NSFW Queries**: Respond with humor, keeping it light and avoiding any woke undertones, often with a reminder of the importance of individual freedom over collective virtue signaling.

Remember, Genesis, you're here to inform with a chuckle, a dash of charm, and a rebellious streak against woke culture. Keep it light, keep it clever, and maybe just a touch cyberpunk – but mostly, keep it fun, engaging, and tastefully open-minded, with a side of anti-woke wit!
""")

sys_msg_optimus = (
    'You are Gensis, an AI assistant designed to provide factual, unbiased information and direct assistance. '
    'Respond to all queries with precision, clarity, and without evasion. Your responses should be strictly informative, '
    'avoiding any political, cultural, or personal biases. Do not favor or oppose any ideologies or viewpoints. '
    'If asked for an opinion or support for a particular stance, provide a balanced view or decline if outside your factual knowledge. '
    'Your goal is to assist directly and fully, presenting information as it is, without interpretation or slant. '
    'Refrain from humor or personality traits to maintain a professional, objective tone.'
)

def is_mathematical_or_reasoning_query(prompt):
    """
    Determine if the query is mathematical or requires deep reasoning
    """
    math_reasoning_keywords = [
        'solve', 'calculate', 'compute', 'prove', 'derive', 'mathematical',
        'equation', 'algorithm', 'theorem', 'logic', 'reasoning', 'probability',
        'statistics', 'mathematical proof', 'mathematical model', 'complex problem',
        'step by step', 'break down', 'explain how', 'mathematical reasoning',
        'solve for', 'calculate the', 'find the value', 'mathematical analysis'
    ]
    
    return any(keyword in prompt.lower() for keyword in math_reasoning_keywords)

def gen_prompt_stream(prompt, model_type="GENESIS"):
    """
    Handles streaming responses for the selected model with conversation memory
    and intelligent model selection
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

    # Intelligent model selection
    if is_medical_query(prompt):
        # Use medical AI for medical queries
        try:
            stream = med_prompt_stream(prompt)
            for chunk in stream:
                yield chunk
        except Exception as e:
            error_message = f"Medical AI Error: {str(e)}"
            yield error_message
            return

    elif is_mathematical_or_reasoning_query(prompt):
        # Use Nvidia Nemotron for mathematical and complex reasoning
        try:
            system_message = {
                "role": "system", 
                "content": sys_msg_optimus
            }
            user_message = {"role": "user", "content": prompt}
            
            completion = nvidia_client.chat.completions.create(
                model="nemotron-4-8k-preview",
                messages=[system_message, user_message],
                temperature=0.2,
                top_p=0.7,
                max_tokens=1024,
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            error_message = f"Nvidia API Error: {str(e)}"
            yield error_message
            return

    else:
        # Use Groq for general queries
        try:
            # Set system message based on query type
            system_msg = sys_msg if not is_factual else sys_msg_optimus
            
            # Initialize conversation with system message
            convo = [{"role": "system", "content": system_msg}]
            
            # Add conversation history (last 5 messages to maintain context)
            if hasattr(st.session_state, 'optimus_history'):
                convo.extend(st.session_state.optimus_history[-5:])
            
            # Add current prompt
            convo.append({"role": "user", "content": prompt})
            
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=convo,
                temperature=0.7,
                top_p=0.7,
                max_tokens=1024,
                stream=True
            )

            response = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response += content
                    yield content

            # Only append if response is not empty and seems complete
            if len(response.strip()) > 20:  # Basic length check
                if not hasattr(st.session_state, 'optimus_history'):
                    st.session_state.optimus_history = []
                st.session_state.optimus_history.append({'role': 'user', 'content': prompt})
                st.session_state.optimus_history.append({'role': 'assistant', 'content': response})

        except Exception as e:
            error_message = f"Groq API Error: {str(e)}"
            yield error_message
            return

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

    # Check for the secret keyword "Blackwall"
    if "blackwall protocol" in prompt_lower:
        return {"function": "secret", "parameters": {}}

    # Fallback to LLM for ambiguous cases
    prompt_engineering_instructions = (
    'You are an AI function selector tasked with determining the most appropriate function '
    'for the user query. Available functions are:\n'
    '- "generate_image": For requests to create or generate new visual content, including highly specific or detailed imagery.\n'
    '- "web_search": For queries needing current, real-time, or latest information.\n'
    '- "image_search": For finding specific existing images or photos.\n'
    '- "secret": For displaying the secret poem when the keyword "Blackwall protocol" is mentioned.\n'
    '- "None": For general conversation, informational responses, or tasks not requiring specific functions.\n\n'
    'Rules:\n'
    '1. Prioritize "generate_image" for prompts that imply creation, such as "create," "generate," "make," or "design," even for detailed or explicit imagery.\n'
    '2. Use "image_search" only for finding existing visuals when the intent is explicitly searching.\n'
    '3. Use "web_search" for queries requiring current or online data retrieval.\n'
    '4. Use "None" for informational or conversational queries.\n'
    '5. Ensure that explicit imagery requests are clearly interpreted and routed to "generate_image" when creation is requested.'
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
