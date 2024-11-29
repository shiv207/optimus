import streamlit as st

st.set_page_config(page_title="GENESIS", layout="wide", page_icon="Images/avatar/HAL_9000.png", initial_sidebar_state="collapsed")

import logging
import requests
from speech.voice import say
from Features.flux_dev import generate_image_dev
from Features.flux_dreamscape import generate_image_dreamscape
from Features.flux_oilscape import generate_image_oilscape
from Features.flux_pro import generate_image_pro
from Features.grid import add_fixed_grid
from Features.image_scrape import handle_image_search_and_description
from Features.blackwall import poem
from modals.tron_o import prompt_stream as optimus_prompt_stream, function_call as optimus_function_call
from modals.genesis_tron import gen_prompt_stream as genesis_prompt_stream, gen_function_call
from modals.discovery_o1 import Perplexity
from typing import Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import html
import re
import os
from dotenv import load_dotenv; load_dotenv()
from googlesearch import search as google_search
from duckduckgo_search import DDGS
import concurrent.futures
import json
from concurrent.futures import ThreadPoolExecutor

print("server started.....")

def generate_image(prompt):
    dreamscape_styles = ['dreamscape', 'anime', 'ghibli']
    oilscape_styles = ['van gogh', 'painting', 'oil painting']
    premium_keywords = ['premium', 'high quality', 'high definition', 'hd', 'high res', 'high resolution', '4k', '8k', 'ultra hd']
    
    prompt_lower = prompt.lower()
    
    try:
        # Check for premium/high-quality requests first
        if any(keyword in prompt_lower for keyword in premium_keywords):
            result = generate_image_pro(prompt)
        # Check other styles if not premium
        elif any(style in prompt_lower for style in dreamscape_styles):
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
        background-image: linear-gradient(#ff000010 1px, transparent 1px),
                          linear-gradient(to right, #ff000010 1px, transparent 1px);
    }
    </style>
    """

def streamlit_ui():
    # Hide Streamlit's default elements
    hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    body {{
        font-family: 'Inter', sans-serif;
        background: #0a0a0a;
        color: #e0e0e0;
    }}

    .sidebar .sidebar-content {{
        background: transparent;
        padding-top: 0;
        display: flex;
        flex-direction: column;
        height: 100vh;
    }}

    .model-container {{
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding: 0 10px;
        margin-bottom: 20px;
        flex-grow: 1;
    }}

    .model-card {{
        background-color: #121212;
        border-radius: 12px;
        padding: 20px;
        color: #ffffff;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
    }}

    .model-card:hover {{
        transform: translateY(-8px) rotateX(3deg) rotateY(3deg);
        box-shadow: 0 12px 24px rgba(0,0,0,0.3);
    }}

    .model-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, #b89ccc,#7640cd,#382382,#2c2140,#201d26,#1e1e20,#1e1433,#23093d,#310a6c);
        backdrop-filter: blur(80px);
        background-size: cover;
        background-blend-mode: soft-light;
        opacity: 0;
        transition: opacity 0.3s ease;
    }}

    .model-card:hover::before {{
        opacity: 0.9;
    }}

    .model-name {{
        font-size: 20px;
        margin-bottom: 15px;
        font-weight: 600;
        color: #ffffff;
        position: relative;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }}

    .model-card:hover .model-name {{
        color: #ffffff;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.8);
    }}

    .model-description {{
        font-size: 14px;
        line-height: 1.5;
        color: #f0f0f0;
        position: relative;
    }}

    .model-description p {{
        margin: 5px 0;
    }}

    .model-meta {{
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid rgba(255,255,255,0.2);
        font-size: 12px;
        color: #d0d0d0;
        position: relative;
    }}

    [data-theme="light"] .sidebar-header {{
        background: transparent;
    }}

    [data-theme="light"] .sidebar-title {{
        color: #333;
    }}

    .model-selector-container {{
        margin: -10px 10px 20px 10px;
        position: relative;
    }}

    @keyframes dropdownFade {{
        from {{
            opacity: 0;
            transform: translateY(-10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    .stRadio > div {{
        display: flex !important;
        flex-direction: row !important;
        gap: 6px !important;
        background: rgba(0, 0, 0, 0.7) !important;
        border-radius: 100px !important;
        padding: 4px 6px !important;
        width: 310px !important;
        margin: 0 auto !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 0 20px rgba(138, 43, 226, 0.1);
    }}        

    .stRadio > div > label {{  
        position: relative;
        padding: 8px 24px !important;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 100px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        flex: 1 !important;
        margin: 0 !important;
        min-width: 120px !important;
        text-align: center;
        letter-spacing: 1px;
        text-transform: uppercase;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .stRadio > div > label[data-selected="true"] {{
        background: transparent;
        color: rgb(255, 255, 255);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.1),
                    0 0 15px rgba(138, 43, 226, 0.2);
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
    }}

    .stRadio > div > label:not([data-selected="true"]):hover {{
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 0 10px rgba(138, 43, 226, 0.1);
    }}

    .stRadio > div > label::before {{
        display: none !important;
    }}

    .stRadio input[type="radio"] {{
        display: none !important;
    }}

    .stRadio > div > label span {{
        letter-spacing: 1px;
        font-weight: 400;
    }}


    .sidebar-header h2:hover {{
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.4), 0 0 30px rgba(255, 255, 255, 0.3), 0 0 45px rgba(255, 255, 255, 0.2);
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar layout with selection box first
    st.sidebar.markdown("""
        <div class="sidebar-header">
            <h2 class="sidebar-title">Select your Adventure</h2>
        </div>
    """, unsafe_allow_html=True)

    # Add custom container for radio button
    st.sidebar.markdown('<div class="model-selector-container">', unsafe_allow_html=True)
    selected_model = st.sidebar.radio(
        "",
        options=["Regular", "Fun"],
        index=0,
        key="model_selector",
        horizontal=False  # Vertical layout
    )
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Then add your model cards
    with st.sidebar:
        st.markdown("""
            <div class="model-container">
                <div class="model-card">
                    <h3 class="model-name">Genesis</h3>
                    <div class="model-description">
                        <p><strong>Architecture:</strong> LLaMA 3.2-mini</p>
                        <p><strong>Parameters:</strong> 70B</p>
                        <p><strong>Latency:</strong> Ultra-fast (25ms)</p>
                        <p><strong>Specialties:</strong> Factual analysis, Efficient processing</p>
                    </div>
                    <div class="model-meta">
                        <span>PUNK</span> | <span>20 Nov 2024</span>
                    </div>
                </div>
                <div class="model-card">
                    <h3 class="model-name">Genesis-o1</h3>
                    <div class="model-description">
                        <p><strong>Architecture:</strong> LLaMA 3.2</p>
                        <p><strong>Capabilities:</strong> Multimodal</p>
                        <p><strong>Latency:</strong> Instant Reaction (50ms)</p>
                        <p><strong>Specialties:</strong> Creative tasks, Deep reasoning, Cosmic escape</p>
                    </div>
                    <div class="model-meta">
                        <span>PUNK</span> | <span>20 Nov 2024</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Model selection
    model_options = ["Regular", "Fun"]
    model_header_names = {
        "Regular": "GENESIS",
        "Fun": "GENESIS"
    }

    # Add the fixed grid
    add_fixed_grid()

    # Load external CSS
    st.markdown(load_css('style.css'), unsafe_allow_html=True)
    
    # Load dynamic CSS
    st.markdown(load_dynamic_css(), unsafe_allow_html=True)

    # Header Section (Fixed)
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.markdown('<div class="header-content">', unsafe_allow_html=True)
    
    # Apply conditional class based on selected model
    if selected_model == "Fun":
        header_class = "header-title genesis"
    else:
        header_class = "header-title"

    # Use the mapping to display the correct header name
    header_name = model_header_names[selected_model]
    st.markdown(f'<h1 class="{header_class}">{header_name}</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat container and session state management
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "What's up? Need help?"}]
    if 'voice_input' not in st.session_state:
        st.session_state.voice_input = None
    if 'last_image_prompt' not in st.session_state:
        st.session_state.last_image_prompt = None

    # Chat container for messages
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(
            msg["role"], 
            avatar="Images/avatar/cool.png" if msg["role"] == "assistant" else "Backend/avatar/mars.png"
        ):
            # Check if it's a stored message from history
            if "content" in msg:
                st.markdown(msg["content"], unsafe_allow_html=True)  # Allow HTML to preserve formatting
            if "image_path" in msg:
                st.image(msg["image_path"], use_container_width=True, output_format="JPEG", quality=85)
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    prompt = st.chat_input("Message Genesis")
    
    # Check for J0HNY 5ILVERHAND trigger
    if prompt and prompt.lower().strip() in ["j0hny 5ilverhand","johny silverhand69", "johny : what would you write on my grave", "roger that roger 69","sourabhcansuck23"]:
        display_silverhand()
        return
        
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="Backend/avatar/mars.png"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar="Images/avatar/cool.png"):
            loading_placeholder = st.empty()
            
            # Loading animation CSS for the bubble
            loading_animation_css = """
            <style>
            .loading-bubble {
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: #9cc2ff;
                position: absolute;  /* Make it fixed in the parent container */
                left: 5px;  
                bottom: -6px;  /* Adjust this to position it slightly above the bottom if necessary */
                animation: pulse 1s infinite;
            }

            @keyframes pulse {
                0% {
                    transform: scale(0.8);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.2);
                    opacity: 0.6;
                }
                100% {
                    transform: scale(0.8);
                    opacity: 1;
                }
            }
            </style>
            <div class="loading-bubble"></div>
            """
            loading_placeholder.markdown(loading_animation_css, unsafe_allow_html=True)

            try:
                # Check if this is an image search request
                if any(keyword in prompt.lower() for keyword in ["show me", "find images", "search images", "look for images", "find pictures", "show pictures"]):
                    loading_placeholder.empty()
                    st.markdown("🔍 Searching for images...")
                    handle_image_search_and_description(prompt)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Here are the images I found based on your request.",
                        "type": "image_search"
                    })
                else:
                    # Use the appropriate module based on selected model
                    if selected_model == "Regular":
                        function_result = optimus_function_call(prompt)
                    else:  # Fun mode
                        function_result = gen_function_call(prompt)

                    if function_result["function"] == "generate_image":
                        # Check if user is requesting to regenerate the last image
                        regenerate_phrases = ["generate again", "generate the image again", "try again", "regenerate"]
                        if any(phrase in prompt.lower() for phrase in regenerate_phrases) and st.session_state.last_image_prompt:
                            # Use the last stored prompt
                            generation_prompt = st.session_state.last_image_prompt
                            st.markdown(f"*Regenerating image with prompt: '{generation_prompt}'*")
                        else:
                            # Store the new prompt and use it
                            generation_prompt = prompt
                            st.session_state.last_image_prompt = prompt

                        # Display loading GIF based on theme
                        import darkdetect

                        if darkdetect.isDark():
                            gif_path = "Images/loadin_animtions/dark.gif"
                        else:
                            gif_path = "Images/loadin_animtions/light.gif"
                        
                        # Create a loading box with the GIF
                        import base64
                        with open(gif_path, "rb") as f:
                            contents = f.read()
                            data_url = f"data:image/gif;base64,{base64.b64encode(contents).decode()}"
                        
                        loading_box_html = f"""
                        <div style="width: 300px; height: 300px; display: flex; justify-content: center; align-items: center; overflow: hidden;">
                            <img src="{data_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">
                        </div>
                        """
                        loading_placeholder.markdown(loading_box_html, unsafe_allow_html=True)

                        # Ensure the loading box is displayed while the image is being generated
                        result = generate_image(generation_prompt)
                        loading_placeholder.empty()  # Clear the loading box after image generation

                        if result.startswith("Error:"):
                            st.error(result)
                            response = f"I'm sorry, but I encountered an error while trying to generate the image: {result}"
                        else:
                            loading_placeholder.empty()
                            st.image(result, caption="Generated Image", use_container_width=True)

                    elif function_result["function"] == "image_search":
                        try:
                            # Call the image search and description handler
                            result = handle_image_search_and_description(prompt)
                            loading_placeholder.empty()
                            
                            # The response is handled within handle_image_search_and_description
                            # Just append a simple confirmation message to the chat
                            response = "I've searched for images related to your query. You can see them below."
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response,
                                "is_image_response": True
                            })
                            
                        except Exception as e:
                            logging.error(f"Image search error: {str(e)}")
                            response = f"I apologize, but I couldn't find any images: {str(e)}"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response,
                                "is_image_response": True
                            })
                            
                    elif function_result["function"] == "web_search":
                        loading_placeholder.empty()
                        search_animation = st.empty()
                        search_animation.markdown(
                            """
                            <style>
                                .search-container {
                                    display: flex;
                                    justify-content: flex-start;
                                    align-items: flex-start;
                                    position: relative;
                                    width: 100%;
                                    padding: 0;
                                    margin: 0;
                                }
                                .searching {
                                    font-size: clamp(0.8rem, 1.5vw, 0.9rem);
                                    font-weight: 490;
                                    position: relative;
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                                    color: #cccccc;
                                    background: linear-gradient(
                                        90deg,
                                        #636363,
                                        #ffffff,
                                        #636363
                                    );
                                    background-size: 200%;
                                    -webkit-background-clip: text;
                                    background-clip: text;
                                    -webkit-text-fill-color: transparent;
                                    animation: shimmer 4s infinite linear;
                                    letter-spacing: max(0.5px, 0.05vw);
                                    transform: translateX(calc(-0.2vw + 2.5px)) translateY(calc(-0.4vh - 2px));
                                    margin-left: 0.05vw;
                                }
                                @keyframes shimmer {
                                    0% { background-position: 200%; }
                                    100% { background-position: 0%; }
                                }

                                /* Style for Perplexity response */
                                .perplexity-response {
                                    position: relative;
                                    transform: translateY(-4px);
                                    margin-top: -4px;
                                }
                            </style>
                            <div class="search-container">
                                <div class="searching">Searching</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Get search results
                        perplexity = Perplexity()
                        results = perplexity.fetch_search_results(prompt)
                        
                        if results and 'response' in results:
                            # Display the AI response
                            st.markdown(results['response'], unsafe_allow_html=True)
                            
                            # Display search results if available
                            if results.get('search_results'):
                                display_sources(results['search_results'])
                            
                            # Add to chat history
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": results['response']
                            })
                        
                        search_animation.empty()

                    else:
                        # Use the appropriate stream based on selected model
                        if selected_model == "Regular":
                            response_generator = optimus_prompt_stream(prompt=prompt)
                        else:  # Fun mode
                            response_generator = genesis_prompt_stream(prompt=prompt)
                        
                        response = ""
                        message_placeholder = st.empty()
                        loading_placeholder.empty()
                        for chunk in response_generator:
                            response += chunk
                            message_placeholder.markdown(response + "▌")
                        message_placeholder.markdown(response)

                        # Store the final formatted response in session state
                        if function_result["function"] not in ["generate_image", "image_search", "web_search"]:
                            final_response = response  # This is the fully generated response
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": final_response
                            })
                        else:
                            # Handle other function responses appropriately
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response,
                                "function_type": function_result["function"]
                            })
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"An error occurred: {str(e)}")
                response = f"I'm sorry, but an error occurred: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown("</div>", unsafe_allow_html=True)

def web_search(prompt: str) -> None:
    try:
        # Load Perplexity CSS first
        load_perplexity_css()
        
        perplexity = Perplexity()
        final_answer = ""
        sources = None
        images = None
        placeholder = st.empty()

        # Rest of your web_search function...

    except Exception as e:
        st.error(f"Search error: {str(e)}")
        logging.error(f"Search error: {str(e)}")

def display_sources(sources):
    main_sources = sources[:3]
    remaining = len(sources) - 3
    
    st.markdown("<div style='margin-left: 52px;'>", unsafe_allow_html=True)
    
    cols = st.columns(len(main_sources) + (1 if remaining > 0 else 0))
    
    for idx, source in enumerate(main_sources):
        with cols[idx]:
            favicon_url = f"https://www.google.com/s2/favicons?domain={source['url']}&sz=32"
            hostname = urlparse(source['url']).netloc.replace('www.', '')
            
            title = source.get("title")
            if not title or title == "Unknown Title":
                path = source['url'].split('/')[-1].replace('-', ' ').replace('_', ' ')
                title = path.title() if path else hostname.capitalize()
            
            st.markdown(f"""
            <div class="source-tile">
                <div class="source-content">
                    <div class="source-title">{title}</div>
                </div>
                <div class="source-footer">
                    <img src='{favicon_url}' class="source-favicon">
                    <span class="source-hostname">{hostname}</span>
                    <span class="source-separator">·</span>
                    <span class="source-index">{idx + 1}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if remaining > 0:
        with cols[-1]:
            remaining_favicons = [
                f"https://www.google.com/s2/favicons?domain={source['url']}&sz=32"
                for source in sources[3:7]
            ]
            
            st.markdown(f"""
            <div class="source-tile remaining-sources">
                <div class="remaining-favicons">
                    {' '.join([
                        f'<img src="{favicon}" class="remaining-favicon" alt="favicon">'
                        for favicon in remaining_favicons[:4]
                    ])}
                </div>
                <span class="remaining-text">Insights from {remaining} sources</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Add the CSS
    st.markdown("""
    <style>
    @media (prefers-color-scheme: dark) {
        .source-tile {
            background-color: rgba(32, 33, 35, 0.7);
            color: #e6e6e6;
        }
        .source-hostname, .source-separator, .source-index, .remaining-text {
            color: #888;
        }
    }
    .source-tile {
        padding: 12px;
        border-radius: 12px;
        margin: 5px 10px 5px 0;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .source-content {
        font-size: 13px;
        font-weight: 400;
        line-height: 1.2;
        overflow: hidden;
    }
    .source-title {
        font-weight: 500;
        margin-bottom: 3px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .source-footer {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: auto;
        opacity: 0.8;
    }
    .source-favicon {
        width: 14px;
        height: 14px;
    }
    .source-hostname, .source-separator, .source-index {
        font-size: 12px;
    }
    .remaining-sources {
        align-items: center;
        justify-content: center;
    }
    .remaining-favicons {
        display: flex;
        flex-direction: row;
        gap: 12px;
        justify-content: center;
        align-items: center;
        margin-bottom: 16px;
    }
    .remaining-favicon {
        width: 20px;
        height: 20px;
        opacity: 0.8;
    }
    .remaining-text {
        font-size: 13px;
        margin-top: 4px;
    }
    .source-container {
        margin-top: 3.5rem;
        margin-left: 52px;
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
    }
    .source-tile {
        background-color: rgba(32, 33, 35, 0.7);
        padding: 16px;
        border-radius: 12px;
        margin: 8px 10px 8px 0;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        flex: 1;
        min-width: 250px;
        max-width: calc(33.333% - 14px);
    }
    .source-url {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

def load_perplexity_css():
    st.markdown("""
    <style>
    /* Lock main container */
    .main .block-container {
        position: fixed !important;
        left: 0 !important;
        right: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Prevent any horizontal movement */
    .stApp {
        position: fixed !important;
        width: 100vw !important;
        left: 0 !important;
        margin: 0 !important;
        overflow-x: hidden !important;
    }
    
    /* Lock chat elements */
    .stChatMessage, .stChatInputContainer {
        max-width: 100% !important;
        margin: 0 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Ensure content stays centered */
    .element-container {
        transform: none !important;
        transition: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_website_title(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        }
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = None
        
        # Try OG title first
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
        
        # Try Twitter title next
        if not title:
            twitter_title = soup.find('meta', {'name': 'twitter:title'})
            if twitter_title:
                title = twitter_title.get('content')
        
        # Fall back to regular title
        if not title and soup.title:
            title = soup.title.string
        
        if title:
            title = html.unescape(title.strip())
            # Remove common suffixes
            common_suffixes = [' - Wikipedia', ' | Wikipedia', ' - Britannica', ' | Britannica']
            for suffix in common_suffixes:
                if title.endswith(suffix):
                    title = title[:-len(suffix)]
            return title
        
        return None
    except Exception as e:
        logging.error(f"Error fetching title for {url}: {str(e)}")
        return None

def prepare_sources(sources):
    """Prepare sources by fetching missing titles."""
    for source in sources:
        if not source.get('title') or source['title'] == "Unknown Title":
            title = get_website_title(source['url'])
            if title:
                source['title'] = title
    return sources

def handle_image_search_and_description(prompt: str) -> None:
    """
    Handle image search and description using DuckDuckGo
    """
    try:
        with st.spinner("🔍 Searching for images..."):
            perplexity = Perplexity()
            results = perplexity.fetch_search_results(prompt, include_images=True)
            
            if not results.get('image_results'):
                st.warning("No images found for your query. Try a different search term.")
                return
            
            # Display search info
            st.markdown(f"### 🖼️ Found {len(results['image_results'])} images for: _{prompt}_")
            
            # Create columns for the image grid
            cols = st.columns(4)
            
            # Display images in grid
            for idx, image in enumerate(results['image_results']):
                with cols[idx % 4]:
                    try:
                        # Container for each image
                        with st.container():
                            # Image display
                            st.image(
                                image['image_url'],
                                caption=image['title'],
                                use_column_width=True
                            )
                            
                            # Source link
                            st.markdown(
                                f"<a href='{image['context_url']}' target='_blank' "
                                f"class='source-link'>🔗 Source</a>",
                                unsafe_allow_html=True
                            )
                            
                            # Analyze button
                            if st.button("🔍 Analyze", key=f"analyze_{idx}"):
                                with st.spinner("Analyzing image..."):
                                    try:
                                        analysis = perplexity.analyze_image(image['image_url'])
                                        st.info(analysis)
                                    except Exception as e:
                                        st.error("Failed to analyze image. Please try again.")
                                        logging.error(f"Image analysis error: {str(e)}")
                                        
                    except Exception as e:
                        st.error("Failed to load image")
                        logging.error(f"Error loading image {idx}: {str(e)}")
            
            # Add cyberpunk styling
            st.markdown("""
            <style>
            /* Image Grid Styling */
            .stImage {
                position: relative;
                margin-bottom: 0.5rem;
                border-radius: 8px;
                overflow: hidden;
                border: 2px solid rgba(156, 194, 255, 0.2);
                transition: all 0.3s ease;
            }
            
            .stImage:hover {
                transform: translateY(-5px);
                border-color: rgba(156, 194, 255, 0.6);
                box-shadow: 0 8px 24px rgba(156, 194, 255, 0.3);
            }
            
            .stImage img {
                width: 100%;
                height: auto;
                display: block;
                border-radius: 6px;
            }
            
            /* Button Styling */
            .stButton > button {
                width: 100%;
                background: rgba(0, 0, 0, 0.5) !important;
                color: #9cc2ff !important;
                border: 1px solid rgba(156, 194, 255, 0.3) !important;
                border-radius: 6px !important;
                padding: 0.5rem !important;
                font-family: 'Courier New', monospace !important;
                font-size: 0.8rem !important;
                text-transform: uppercase !important;
                letter-spacing: 1px !important;
                margin: 0.5rem 0 !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton > button:hover {
                background: rgba(156, 194, 255, 0.1) !important;
                border-color: rgba(156, 194, 255, 0.6) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(156, 194, 255, 0.2) !important;
            }
            
            /* Source Link Styling */
            .source-link {
                display: inline-block;
                width: 100%;
                padding: 0.4rem;
                margin: 0.2rem 0;
                background: rgba(0, 0, 0, 0.3);
                color: #9cc2ff !important;
                text-align: center;
                text-decoration: none !important;
                font-family: 'Courier New', monospace;
                font-size: 0.8rem;
                border: 1px solid rgba(156, 194, 255, 0.2);
                border-radius: 4px;
                transition: all 0.3s ease;
            }
            
            .source-link:hover {
                background: rgba(156, 194, 255, 0.1);
                border-color: rgba(156, 194, 255, 0.4);
                color: #ffffff !important;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(156, 194, 255, 0.2);
            }
            
            /* Info Box Styling */
            .stAlert {
                background: rgba(0, 0, 0, 0.3) !important;
                color: #ffffff !important;
                border: 1px solid rgba(156, 194, 255, 0.2) !important;
                border-radius: 8px !important;
                padding: 1rem !important;
                margin: 0.5rem 0 !important;
                font-family: 'Courier New', monospace !important;
            }
            
            .stAlert:hover {
                border-color: rgba(156, 194, 255, 0.4) !important;
                box-shadow: 0 0 15px rgba(156, 194, 255, 0.1) !important;
            }
            
            /* Caption Styling */
            .caption {
                color: #9cc2ff;
                font-size: 0.8rem;
                margin: 0.3rem 0;
                font-family: 'Courier New', monospace;
                overflow: hidden;
                text-overflow: ellipsis;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            </style>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"An error occurred during image search: {str(e)}")
        logging.error(f"Image search error: {str(e)}")

def display_silverhand():
    st.markdown("""
    <style>
    .future-grave {
        background: linear-gradient(180deg, #121212 0%, #001f3f 100%);
        padding: 2rem;
        border-radius: 12px;
        margin: 2rem auto;
        max-width: 500px;
        opacity: 0.85;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle border */
    }
    .grave-text {
        font-family: 'Roboto', sans-serif;
        color: #e0e0e0; /* Soft light gray */
        line-height: 1.5;
        font-size: 0.95rem;
        font-weight: 300;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5); /* Subtle shadow for depth */
    }
    .grave-text::first-line {
        font-weight: 700;
        font-size: 1.2rem;
        color: #ffffff; /* Soft white for the first line */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7); /* Stronger shadow for emphasis */
    }
</style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="future-grave"><div class="grave-text">{poem}</div></div>', unsafe_allow_html=True)


def main():
    streamlit_ui()

if __name__ == "__main__":
    main()