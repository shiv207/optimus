import streamlit as st
import os
import re
import logging
from requests.exceptions import RequestException, Timeout
import threading
from Features.voice import say
from Features.flux_dev import generate_image_dev
from groq import Groq
from Features.flux_dreamscape import generate_image_dreamscape
from Features.img_scrape import handle_image_search
from Features.flux_oilscape import generate_image_oilscape
from Features.grid import add_fixed_grid
import random
from modals.optimus import groq_prompt_stream, function_call as groq_function_call
from modals.genesis import genesis_prompt_stream, genesis_function_call
import base64
from PIL import Image
import io

# Initialize API clients
wake_word = 'optimus'
groq_client = Groq(api_key='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')

st.set_page_config(page_title="Optimus", layout="wide", page_icon="Images/avatar/HAL.png", initial_sidebar_state="collapsed")

# Add caching for loading CSS files
@st.cache_data(ttl=24*60*60)  # Cache for 24 hours
def load_css(file_name):
    with open(file_name) as f:
        return f'<style>{f.read()}</style>'

# Add this new function to load dynamic CSS
def load_dynamic_css():
    return """
    <style>
    body:not(.sidebar-open) .stDecoration {
        background-image: linear-gradient(#00000010 1px, transparent 1px),
                          linear-gradient(to right, #00000010 1px, transparent 1px);
    }
    body.sidebar-open .stDecoration {
        background-image: linear-gradient(#0000FF10 1px, transparent 1px),
                          linear-gradient(to right, #0000FF10 1px, transparent 1px);
    }
    </style>
    """

def parse_groq_stream(stream):
    response = ""
    for chunk in stream:
        if chunk.choices:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content
    return response

# Cache the base64 encoding function
@st.cache_data(ttl=24*60*60)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Cache the image generation functions
@st.cache_data(ttl=60*60)  # Cache for 1 hour
def generate_image(prompt):
    dreamscape_styles = ['dreamscape', 'anime', 'ghibli']
    oilscape_styles = ['van gogh', 'painting', 'oil painting']
    
    prompt_lower = prompt.lower()
    
    try:
        if any(style in prompt_lower for style in dreamscape_styles):
            if not any(style in prompt_lower for style in ['dreamscape style', 'anime style', 'ghibli style']):
                prompt += " in dreamscape style"
            result = generate_image_dreamscape(prompt)
        elif any(style in prompt_lower for style in oilscape_styles):
            if 'oil painting style' not in prompt_lower:
                prompt += " in oil painting style"
            result = generate_image_oilscape(prompt)
        else:
            result = generate_image_dev(prompt)
        
        if result.startswith("Error:"):
            return result 
        else:
            return result  
    except Exception as e:
        return f"Error: Failed to generate image. {str(e)}"

# Cache the Groq client initialization
@st.cache_resource
def get_groq_client():
    return Groq(api_key='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')

# Initialize chat history with caching
@st.cache_data(ttl=None)
def initialize_chat_history():
    return [{"role": "assistant", "content": "What's up? Need help?"}]

# Cache the avatar images
@st.cache_data(ttl=24*60*60)
def get_avatar_images():
    return {
        "assistant": "Images/avatar/cool.png",
        "user": "Backend/avatar/mars.png"
    }

# Cache the model options
@st.cache_data
def get_model_options():
    return ["Optimus", "Genesis"]

# Cache the model cards HTML
@st.cache_data
def get_model_cards_html():
    return """
        <div class="model-container">
            <div class="model-card">
                <h3 class="model-name">Optimus</h3>
                <div class="model-description">
                    <p><strong>Architecture:</strong> LLaMA 3</p>
                    <p><strong>Parameters:</strong> 70B</p>
                    <p><strong>Latency:</strong> Ultra-fast (25ms)</p>
                    <p><strong>Specialties:</strong> Factual analysis, Efficient processing</p>
                </div>
                <div class="model-meta">
                    <span>PUNK</span> | <span>22 Oct 2023</span>
                </div>
            </div>
            <div class="model-card">
                <h3 class="model-name">Genesis</h3>
                <div class="model-description">
                    <p><strong>Architecture:</strong> MIXTERAL</p>
                    <p><strong>Capabilities:</strong> Multimodal</p>
                    <p><strong>Latency:</strong> Instant Reaction (50ms)</p>
                    <p><strong>Specialties:</strong> Creative tasks, Deep reasoning</p>
                </div>
                <div class="model-meta">
                    <span>PUNK</span> | <span>22 Oct 2023</span>
                </div>
            </div>
        </div>
    """

# Add batch processing for response generation
@st.cache_data(ttl=60)  # Cache for 1 minute
def process_response(prompt, selected_model):
    try:
        if selected_model == "Optimus":
            function_result = groq_function_call(prompt)
        else:
            function_result = genesis_function_call(prompt)
        return function_result
    except Exception as e:
        return {"error": str(e)}

# Add lazy loading for images
@st.cache_data(ttl=24*60*60)
def get_optimized_avatar_images():
    return {
        "assistant": {
            "path": "Images/avatar/cool.png",
            "size": (32, 32)  # Smaller size for mobile
        },
        "user": {
            "path": "Backend/avatar/mars.png",
            "size": (32, 32)
        }
    }

# Optimize image loading for chat messages
@st.cache_data(ttl=60*60)
def optimize_chat_image(image_path, max_width=800):
    try:
        img = Image.open(image_path)
        # Calculate new height maintaining aspect ratio
        ratio = max_width / img.size[0]
        new_size = (max_width, int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to WebP format for better compression
        buffer = io.BytesIO()
        img.save(buffer, format="WebP", quality=85, optimize=True)
        return buffer
    except Exception:
        return image_path

# Optimize the chat container rendering
def render_chat_messages():
    messages_per_page = 20
    start_idx = max(0, len(st.session_state.messages) - messages_per_page)
    
    for msg in st.session_state.messages[start_idx:]:
        with st.chat_message(
            msg["role"],
            avatar=get_optimized_avatar_images().get(msg["role"], {}).get("path")
        ):
            if "content" in msg:
                st.markdown(msg["content"])
            if "image_path" in msg:
                optimized_image = optimize_chat_image(msg["image_path"])
                st.image(optimized_image, use_column_width=True)

# Optimize CSS delivery
@st.cache_data(ttl=24*60*60)
def get_optimized_css():
    return """
    <style>
    /* Mobile-first responsive design */
    .chat-container {
        max-width: 100%;
        margin: 0 auto;
        padding: 8px;
    }
    
    .model-container {
        display: flex;
        flex-direction: column;
        gap: 30px;  /* Increased gap between cards */
        padding: 15px;
    }
    
    .model-card {
        padding: 20px;  /* Increased padding */
        margin-bottom: 25px;  /* Increased margin */
        border-radius: 15px;  /* Optional: slightly larger border radius */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);  /* Optional: enhanced shadow */
    }
    
    /* Reduce animations on mobile */
    @media (max-width: 768px) {
        .model-container {
            gap: 20px;  /* Slightly smaller gap on mobile */
            padding: 10px;
        }
        
        .model-card {
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .model-card:hover {
            transform: none;
        }
        
        .loading-bubble {
            animation: none;
        }
        
        /* Simplify gradients */
        .model-card::before {
            background: linear-gradient(135deg, #26D0CE, #1A2980);
            opacity: 0.1;
        }
    }
    
    /* Optimize font loading */
    @font-face {
        font-family: 'Inter';
        font-display: swap;
        src: url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    }

    /* Add spacing between model card elements */
    .model-description {
        margin-top: 15px;
    }

    .model-description p {
        margin: 10px 0;  /* Add vertical spacing between paragraphs */
    }

    .model-meta {
        margin-top: 20px;  /* Increased space before meta section */
        padding-top: 15px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    """

# Optimize model cards for mobile
@st.cache_data
def get_mobile_optimized_model_cards():
    return """
        <div class="model-container">
            <div class="model-card">
                <h3 class="model-name">Optimus</h3>
                <div class="model-description">
                    <p>LLaMA 3 • 70B • 25ms</p>
                    <p>Factual analysis & processing</p>
                </div>
            </div>
            <div class="model-card">
                <h3 class="model-name">Genesis</h3>
                <div class="model-description">
                    <p>MIXTERAL • Multimodal • 50ms</p>
                    <p>Creative tasks & reasoning</p>
                </div>
            </div>
        </div>
    """

# Detect mobile devices
@st.cache_data
def is_mobile():
    import streamlit as st
    try:
        user_agent = st.get_user_agent()
        return user_agent.is_mobile
    except:
        return False

def streamlit_ui():
    add_fixed_grid()

    # Hide Streamlit's default elements
    hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    # Add mobile-optimized CSS
    mobile_optimizations = """
    <style>
    @media (max-width: 768px) {
        .chat-container {
            padding: 8px;
            margin: 0;
        }
        
        .model-card {
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .model-card:hover {
            transform: translateY(-2px);  /* Reduced animation */
        }
        
        .header-title {
            font-size: 24px;  /* Smaller title on mobile */
        }
        
        .stMarkdown {
            font-size: 14px;  /* Smaller text on mobile */
        }
        
        /* Optimize images for mobile */
        .stImage > img {
            max-width: 100%;
            height: auto;
        }
    }
    </style>
    """
    st.markdown(mobile_optimizations, unsafe_allow_html=True)
    
    # Sidebar title
    st.sidebar.markdown('<h1 class="sidebar-title">Pick Your Fighter!</h1>', unsafe_allow_html=True)

    # Model cards in sidebar
    with st.sidebar:
        st.markdown("""
            <style>
            .model-container {
                display: flex;
                flex-direction: column;
                gap: 20px !important;  /* Reduced from 28px */
                padding: 20px;
                margin-top: 15px;  /* Reduced from 20px */
            }
            
            .model-card {
                background-color: #121212;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 20px !important;  /* Reduced from 25px */
                color: #ffffff;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                border: 1px solid rgba(255,255,255,0.1);
                position: relative;
                overflow: hidden;
            }

            /* Slightly reduced spacing after title */
            .sidebar-title {
                margin-bottom: 20px !important;  /* Reduced from 25px */
            }

            /* Slightly adjusted internal spacing */
            .model-description {
                margin-top: 15px;  /* Reduced from 18px */
                margin-bottom: 15px;  /* Reduced from 18px */
            }

            .model-meta {
                margin-top: 18px;  /* Reduced from 22px */
                padding-top: 15px;
            }

            @media (max-width: 768px) {
                .model-container {
                    gap: 18px !important;  /* Reduced from 22px */
                    padding: 15px;
                }
                
                .model-card {
                    margin-bottom: 18px !important;  /* Reduced from 22px */
                    padding: 20px;
                }
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Then add your model cards HTML
        st.markdown(get_model_cards_html(), unsafe_allow_html=True)

    # Model selection with cached options
    model_options = get_model_options()
    selected_model = st.sidebar.selectbox(
        "",
        options=model_options,
        index=0,
    )

    # Load external CSS with caching
    st.markdown(load_css('style.css'), unsafe_allow_html=True)
    
    # Load dynamic CSS with caching
    st.markdown(load_dynamic_css(), unsafe_allow_html=True)

    # Header Section with conditional class
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.markdown('<div class="header-content">', unsafe_allow_html=True)
    
    header_class = "header-title genesis" if selected_model == "Genesis" else "header-title"
    st.markdown(f'<h1 class="{header_class}">{selected_model}</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat container and session state management
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    if 'messages' not in st.session_state:
        st.session_state.messages = initialize_chat_history()
    if 'voice_input' not in st.session_state:
        st.session_state.voice_input = None

    # Optimized chat container rendering
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    messages_per_page = 20  # Limit messages for better performance
    start_idx = max(0, len(st.session_state.messages) - messages_per_page)
    
    for msg in st.session_state.messages[start_idx:]:
        with st.chat_message(msg["role"], avatar=get_optimized_avatar_images().get(msg["role"], {}).get("path")):
            if "content" in msg:
                st.markdown(msg["content"])
            if "image_path" in msg:
                optimized_image = optimize_chat_image(msg["image_path"])
                st.image(optimized_image, use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input(f"Ask {selected_model} something", key="chat_input")

    # Handle user input with optimized response processing
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar=get_optimized_avatar_images()["assistant"]["path"]):
            loading_placeholder = st.empty()
            
            loading_animation_css = """
            <style>
            @media (min-width: 769px) {
                .loading-bubble {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: radial-gradient(circle at bottom right, #3477f4, #ffffff);
                    box-shadow: 0 0 10px rgba(135, 206, 235, 0.4);
                    position: absolute;
                    left: 5px;
                    bottom: -6px;
                    animation: pulse 3s infinite;
                }

                @keyframes pulse {
                    0% { transform: scale(0.8); opacity: 1; }
                    50% { transform: scale(1.2); opacity: 0.6; }
                    100% { transform: scale(0.8); opacity: 1; }
                }
            }
            
            @media (max-width: 768px) {
                .loading-bubble {
                    width: 12px;
                    height: 12px;
                    background: #3477f4;
                    border-radius: 50%;
                    position: absolute;
                    left: 5px;
                    bottom: -6px;
                }
            }
            </style>
            <div class="loading-bubble"></div>
            """
            loading_placeholder.markdown(loading_animation_css, unsafe_allow_html=True)

            try:
                function_result = process_response(prompt, selected_model)
                
                if function_result.get("function") == "generate_image":
                    result = generate_image(prompt)
                    if result.startswith("Error:"):
                        st.error(result)
                        response = f"I'm sorry, but I encountered an error while trying to generate the image: {result}"
                    else:
                        optimized_image = optimize_chat_image(result)
                        st.image(optimized_image, caption="Generated Image", use_column_width=True)
                        response = "I've generated an image based on your prompt. You can see it above."
                
                elif function_result.get("function") == "search_images":
                    result = handle_image_search(prompt)
                    if result and isinstance(result, list):
                        valid_images = [optimize_chat_image(img) for img in result if img]
                        if valid_images:
                            for img in valid_images:
                                st.image(img, use_column_width=True)
                        else:
                            response = "No valid images found for your prompt."
                    else:
                        response = ""
                        
                else:
                    if selected_model == "Optimus":
                        response_generator = groq_prompt_stream(prompt=prompt)
                    else:
                        response_generator = genesis_prompt_stream(prompt)
                    
                    response = ""
                    message_placeholder = st.empty()
                    for chunk in response_generator:
                        response += chunk
                        message_placeholder.markdown(response + "▌")
                    message_placeholder.markdown(response)
                
                loading_placeholder.empty()
                st.session_state.messages.append({"role": "assistant", "content": response})
                say(response)
                
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"An error occurred: {str(e)}")
                response = f"I'm sorry, but an error occurred: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Run the Streamlit UI
    streamlit_ui()

if __name__ == "__main__":
    main()

