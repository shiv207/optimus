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
from modals.genesis import gen_prompt_stream as genesis_prompt_stream, gen_function_call
from modals.discovery_o1 import Perplexity
from typing import Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import html


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

    .sidebar-header h2 {{
        font-size: 1.6rem;
        margin-left: 3cm;
        color: #ffffff;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.3), 0 0 20px rgba(255, 255, 255, 0.2), 0 0 30px rgba(255, 255, 255, 0.1);
        transition: text-shadow 0.3s ease;
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
            if "content" in msg:
                st.markdown(msg["content"])
            if "image_path" in msg:
                st.image(msg["image_path"], use_column_width=True, output_format="JPEG", quality=85)
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    prompt = st.chat_input("Send a message")
    
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
                        st.image(result, caption="Generated Image", use_column_width=True)

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
                                justify-content: center;
                                align-items: center;
                                padding: 12px;
                                margin: 8px 0;
                            }
                            .searching {
                                font-size: 0.9rem;
                                font-weight: 490;
                                margin-right: 1015px;
                                margin-top: -15px;
                                position: fixed;
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
                                animation: shimmer 3s infinite linear;
                                letter-spacing: 0.5px;
                            }
                            @keyframes shimmer {
                                0% {
                                    background-position: 200%;
                                }
                                100% {
                                    background-position: 0%;
                                }
                            }
                            @media (max-width: 768px) {
                                .search-container {
                                    padding: 8px;
                                    margin: 6px 0;
                                }
                                .searching {
                                    font-size: 0.8rem;
                                    margin-right: 6cm;
                                    margin-top: -0.4cm;
                                }
                            }
                            @supports (-webkit-touch-callout: none) {
                                .searching {
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                                }
                            }
                        </style>
                        <div class="search-container">
                            <div class="searching">Searching</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    web_search_result = web_search(prompt)
                    search_animation.empty()
                    if web_search_result:
                        st.markdown(web_search_result)
                        st.session_state.messages.append({"role": "assistant", "content": web_search_result})
                        say(web_search_result)

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

                    st.session_state.messages.append({"role": "assistant", "content": response})
                    say(response)
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"An error occurred: {str(e)}")
                response = f"I'm sorry, but an error occurred: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown("</div>", unsafe_allow_html=True)

def web_search(prompt: str) -> None:
    try:
        perplexity = Perplexity()
        final_answer = ""
        sources = None
        images = None
        placeholder = st.empty()

        for answer in perplexity.generate_answer(prompt):
            if "error" in answer:
                st.error(answer["error"])
                return

            if answer.get('answer'):
                final_answer = answer['answer']
                images = answer.get('images', [])
                
                response_html = f"""
                <div style="margin-bottom: 20px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin-bottom: 20px;">
                        {''.join([
                            f'<div style="aspect-ratio: 1; position: relative;">'
                            f'<img src="{img}" alt="Search result" '
                            f'style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">'
                            f'</div>'
                            for img in images[:4]
                        ])}
                    </div>
                    <div style="font-size: 16px; line-height: 1.6; color: #d1d5db;">
                        {final_answer}
                    </div>
                </div>
                """
                
                placeholder.markdown(response_html, unsafe_allow_html=True)
            
            if answer.get('references'):
                sources = answer['references']

        if sources:
            display_sources(sources)

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
            hostname = source['url'].split('//')[1].split('/')[0].replace('www.', '')
            
            title = source.get("title")
            if not title or title == "Unknown Title":
                path = source['url'].split('/')[-1].replace('-', ' ').replace('_', ' ')
                title = path.title() if path else hostname.capitalize()
            
            st.markdown(f"""
            <div class="source-tile">
                <div class="source-content">
                    <div class="source-title">{title}</div>
                    <a href="{source['url']}" target="_blank" class="source-url">{source['url']}</a>
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

    st.markdown("""
    <style>
    @media (prefers-color-scheme: dark) {
        .source-tile {
            background-color: rgba(32, 33, 35, 0.7);
            color: #e6e6e6;
        }
        .source-url, .source-hostname, .source-separator, .source-index, .remaining-text {
            color: #888;
        }
    }
    @media (prefers-color-scheme: light) {
        .source-tile {
            background-color: #f0f2f5;
            color: #333;
        }
        .source-url, .source-hostname, .source-separator, .source-index, .remaining-text {
            color: #666;
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
    .source-url {
        font-size: 11px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        text-decoration: none;
    }
    .source-footer {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: auto;
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
        display: block;
    }
    .remaining-text {
        font-size: 13px;
        margin-top: 4px;
    }
    @media (max-width: 768px) {
        .source-tile {
            height: auto;
            padding: 15px;
            margin: 10px 0;
            border-radius: 15px;
        }
        .source-content {
            font-size: 14px;
        }
        .source-title {
            font-size: 16px;
            margin-bottom: 5px;
        }
        .source-url {
            font-size: 12px;
        }
        .source-footer {
            margin-top: 10px;
        }
        .source-favicon {
            width: 16px;
            height: 16px;
        }
        .source-hostname, .source-separator, .source-index {
            font-size: 12px;
        }
        .remaining-sources {
            flex-direction: column;
        }
        .remaining-favicons {
            margin-bottom: 10px;
        }
        .remaining-favicon {
            width: 24px;
            height: 24px;
        }
        .remaining-text {
            font-size: 14px;
        }
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
        
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
        
        if not title:
            twitter_title = soup.find('meta', {'name': 'twitter:title'})
            if twitter_title:
                title = twitter_title.get('content')
        
        if not title and soup.title:
            title = soup.title.string
        
        if title:
            title = html.unescape(title.strip())
            common_suffixes = [' - Wikipedia', ' | Wikipedia', ' - Britannica', ' | Britannica']
            for suffix in common_suffixes:
                if title.endswith(suffix):
                    title = title[:-len(suffix)]
            return title
        
        return None
    except Exception as e:
        print(f"Error fetching title for {url}: {str(e)}")
        return None

def prepare_sources(sources):
    for source in sources:
        if not source.get('title') or source['title'] == "Unknown Title":
            title = get_website_title(source['url'])
            if title:
                source['title'] = title
    return sources

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
