import streamlit as st
from duckduckgo_search import DDGS
import os
import spacy
from dotenv import load_dotenv
from groq import Groq
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("""
    The required spaCy model is not installed. Attempting to install it...
    """)
    
    # Try to install the model automatically
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        # Reload the model after installation
        nlp = spacy.load("en_core_web_sm")
        st.success("spaCy model installed successfully!")
    except subprocess.CalledProcessError as e:
        st.error(f"Installation failed: {e}")
        st.stop()

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def refine_search_query(query):
    """Refine search query using spaCy NLP to extract meaningful keywords."""
    doc = nlp(query.lower())
    important_pos = {"NOUN", "PROPN", "ADJ"}
    stop_words = {"find", "show", "get", "search", "look", "give", "want", "need", "image", "picture", "photo", "images", "pictures", "photos"}
    keywords = [token.text for token in doc if token.pos_ in important_pos and not token.is_stop and token.text not in stop_words and len(token.text) > 1]
    
    return ' '.join(keywords) if keywords else query

async def fetch_image_url(session, url):
    """Asynchronously fetch a single image URL to verify it's valid."""
    try:
        async with session.head(url, timeout=2) as response:
            return url if response.status == 200 else None
    except:
        return None

async def verify_images_async(image_urls):
    """Asynchronously verify multiple image URLs."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_image_url(session, url) for url in image_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [url for url in results if url]

def scrape_images(query, max_results=4):
    """Search for images with guaranteed results."""
    try:
        with DDGS() as ddgs:
            # Get more images initially to have backups
            all_images = list(ddgs.images(
                query,
                max_results=20,  # Get more for backup
            ))
            
            # Simple extraction of URLs
            image_urls = []
            for img in all_images:
                if img.get('image'):
                    image_urls.append(img['image'])
            
            return image_urls[:max_results] if image_urls else ["https://via.placeholder.com/400x300.png"]

    except Exception as e:
        print(f"Search error: {str(e)}")
        return ["https://via.placeholder.com/400x300.png"]

def get_brief_description(query):
    """Generate a brief description using Groq."""
    prompt = (
        f"Tell me a 10-line description of the object '{query}'. Do not describe the query itself, "
        "but instead focus on the object's characteristics, uses, and any interesting facts."
        'do not say you cannot find the description, just say it, doesnt matter if it is not good or bad'
    )
    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides brief descriptions."},
                {"role": "user", "content": prompt}
            ],
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
    custom_css = """
    <style>
        :root {
            --bg-color-dark: #1C1C1C;
            --text-color-dark: #ffffff;
            --bg-color-light: rgb(22,232,232);
            --text-color-light: #000000;
            --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            --gap-size: 12px; /* Define a CSS variable for gap size */
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
            border-radius: 20px; /* 6px */
            object-fit: cover;
            margin-bottom: 0.375rem; /* 6px */
        }

        .stChatMessage {
            color: var(--text-color);
        }

        .image-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--gap-size);  /* Use the CSS variable for consistency */
            justify-items: center;
            align-items: center;
            margin-top: 0.375rem; /* 6px */
        }

        .image-container {
            width: 100%;
            padding-top: 75%;  /* Keeps the aspect ratio */
            position: relative;
            border-radius: 10px; /* 3px */
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
            border-radius: 20px; /* 3px */
        }

        @media (max-width: 768px) {
            .description-box {
                font-size: 0.875rem; /* 14px */
                padding: 0.25rem; /* 4px */
            }
            .image-grid {
                display: flex;
                flex-direction: column;
                gap: var(--gap-size);
                align-items: center;
                margin-top: 0.375rem; /* 6px */
            }
            .image-container {
                width: 100%;
                padding-top: 75%;  /* Keeps the aspect ratio */
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
    
    # Display the results
    st.markdown(f'<div class="description-box">{description}</div>', unsafe_allow_html=True)
    
    if image_urls:
        # Create a container for images with onerror handler
        image_html = '<div class="image-grid">'
        for image_url in image_urls[:4]:  # Always limit to 4
            image_html += f'''
                <div class="image-container">
                    <img src="{image_url}" 
                         alt="Search Result" 
                         onerror="this.onerror=null; this.src='https://via.placeholder.com/400x300.png';"
                    />
                </div>'''
        image_html += '</div>'
        st.markdown(image_html, unsafe_allow_html=True)

def search_images_duckduckgo(query, max_results=4):
    """Search for images using DuckDuckGo and verify their availability."""
    return scrape_images(query, max_results)  # Call the existing scrape_images function
