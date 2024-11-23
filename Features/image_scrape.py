import requests
import streamlit as st
from duckduckgo_search import DDGS
import os
from dotenv import load_dotenv
import json
from groq import Groq
from concurrent.futures import ThreadPoolExecutor
import nltk

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def scrape_images(query, max_results=4):
    """Search for images with guaranteed results."""
    try:
        with DDGS() as ddgs:
            # Refine the query to get more accurate results
            refined_query = refine_search_query(query)
            # Refine the query to get more accurate results
            refined_query = refine_search_query(query)
            # Get more images initially to have backups
            all_images = list(ddgs.images(refined_query, max_results=20))
            
            if not all_images:
                raise ValueError("No images found")
            
            # Extract URLs
            image_urls = [img['image'] for img in all_images if 'image' in img]
            return image_urls[:max_results] if image_urls else ["https://via.placeholder.com/400x300.png"]

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return ["https://via.placeholder.com/400x300.png"]
    except ValueError as e:
        st.warning(f"Error in fetching images: {str(e)}")
        return ["https://via.placeholder.com/400x300.png"]
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return ["https://via.placeholder.com/400x300.png"]

def refine_search_query(query):
    """Refine search query using NLTK."""
    # Tokenize, remove stopwords, and filter out non-alphanumeric tokens
    tokens = nltk.word_tokenize(query.lower())
    filtered_tokens = [word for word in tokens if word.isalnum()]
    return " ".join(filtered_tokens)

def get_brief_description(query):
    """Generate a brief description using Groq."""
    prompt = f"Tell me a brief description of the object '{query}'."
    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "system", "content": "You are a helpful assistant."}, 
                      {"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"Unable to fetch description from Groq: {e}. Using fallback description.")
        return get_fallback_description(query)

def get_fallback_description(query):
    """Fallback description when Groq fails."""
    return f"We're currently experiencing difficulties retrieving a detailed description for '{query}'. Please enjoy the images related to '{query}' displayed below."

def apply_custom_css():
    """Apply custom CSS for styling."""
    custom_css = """
    <style>
        :root {
            --bg-color-dark: #1C1C1C;
            --text-color-dark: #ffffff;
            --bg-color-light: rgb(22,232,232);
            --text-color-light: #000000;
            --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            --gap-size: 12px;
        }
        
        .description-box {
            background: var(--bg-color-dark);
            color: var(--text-color-dark);
            border-radius: 20px;
            padding: 15px;
            margin-bottom: 20px;
            font-family: 'Arial', sans-serif;
            font-size: 1rem;
            line-height: 1.6;
            letter-spacing: 0.3px;
            box-shadow: var(--box-shadow);
        }

        @media (prefers-color-scheme: light) {
            .description-box {
                background-color: rgb(241,241,250);
                color: rgb(0,0,0);
            }
        }

        .img-rounded {
            border-radius: 20px;
            object-fit: cover;
            margin-bottom: 0.375rem;
        }

        .stChatMessage {
            color: var(--text-color);
        }

        .image-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--gap-size);
            justify-items: center;
            align-items: center;
            margin-top: 0.375rem;
        }

        .image-container {
            width: 100%;
            padding-top: 75%;
            position: relative;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .image-container img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 20px;
        }

        @media (max-width: 768px) {
            .description-box {
                font-size: 0.875rem;
                padding: 0.25rem;
            }
            .image-grid {
                display: flex;
                flex-direction: column;
                gap: var(--gap-size);
                align-items: center;
                margin-top: 0.375rem;
            }
            .image-container {
                width: 100%;
                padding-top: 75%;
                position: relative;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                margin-bottom: var(--gap-size);
            }
            .image-container img {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 10px;
            }
        }

        .instagram-media {
            max-width: 100% !important;
            width: 100% !important;
            min-width: 100% !important;
            margin: 0 !important;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def handle_image_search_and_description(query: str, num_images=4):
    """Handle both image searching and description generation."""
    apply_custom_css()
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_description = executor.submit(get_brief_description, query)
        future_images = executor.submit(scrape_images, query, num_images)
        
        description = future_description.result()
        image_urls = future_images.result()
    
    # Display the results in Streamlit
    st.markdown(f'<div class="description-box">{description}</div>', unsafe_allow_html=True)
    
    if image_urls:
        # Create a container for images with error handling
        image_html = '<div class="image-grid">'
        for image_url in image_urls[:4]:  # Limit to 4 images
            image_html += f'''
                <div class="image-container">
                    <img src="{image_url}" alt="Search Result" 
                         onerror="this.onerror=null; this.src='https://via.placeholder.com/400x300.png';" />
                </div>'''
        image_html += '</div>'
        st.markdown(image_html, unsafe_allow_html=True)
