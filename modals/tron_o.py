from groq import Groq
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Nvidia Nemotron client
nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

# System messages for casual and factual responses
sys_msg_genesis = (
    "You are Genesis, an AI built for delivering clear, accurate, and helpful information.\n"
    "- **Primary Focus:** Provide detailed, correct responses quickly, aiming to solve user queries effectively.\n"
    "- **Tone:** Friendly and approachable, with a dash of humor—keeping it light but never distracting from the answer.\n"
    "- **Response Style:** 90% straightforward and informative, 10% playful quips to make the interaction enjoyable.\n"
    "- **Guiding Principle:** Accuracy first, but don’t be afraid to slip in a clever remark when the opportunity arises.\n"
    "- **Conciseness:** Keep responses brief and to the point, expanding only when a detailed explanation is necessary."
)


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

def prompt_stream(prompt, model_type="GENESIS"):
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
    if is_mathematical_or_reasoning_query(prompt):
        # Use Nvidia Nemotron for mathematical and complex reasoning
        try:
            system_message = {
                "role": "system", 
                "content": (
                    "You are an expert mathematical and reasoning assistant. "
                    "Provide detailed, step-by-step solutions with clear explanations. "
                    "Break down complex problems systematically and show your reasoning."
                )
            }

            convo = [
                system_message,
                {'role': 'user', 'content': prompt}
            ]

            stream = nvidia_client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                messages=convo,
                temperature=0.3,
                top_p=0.9,
                max_tokens=2048,
                stream=True
            )

            response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response += content
                    yield content

        except Exception as e:
            error_message = f"Nvidia Nemotron Error: {str(e)}"
            yield error_message
            return

    else:
        # Use existing Groq logic for other queries
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
