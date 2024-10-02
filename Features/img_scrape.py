import streamlit as st
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
from groq import Groq
import instaloader
import tempfile
import os
import hashlib
import base64  # Required for encoding images

# Replace with your actual keys
API_KEY = "AIzaSyDHyK7T14VG8vMwaJhQicBRovAb76dkdxk"
SEARCH_ENGINE_ID = "d6604d6b7dbb9447a"
GROQ_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)

def search_images(query, num_images=7):
    service = build("customsearch", "v1", developerKey=API_KEY)
    try:
        res = service.cse().list(
            q=query,
            cx=SEARCH_ENGINE_ID,
            searchType='image',
            num=num_images
        ).execute()
        images = [item['link'] for item in res.get('items', [])]
        if not images:
            st.warning(f"No images found for query: '{query}'. Please try a different search term.")
        return images
    except Exception as e:
        st.error(f"Error fetching images: {e}")
        return []

def get_brief_description(query):
    prompt = (
        f"Tell me a 10-line description of the object '{query}'. Do not describe the query itself, "
        "but instead focus on the object's characteristics, uses, and any interesting facts., do not include the query in the description"
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
    # This function provides a more informative fallback description
    return f"""
    We're currently experiencing difficulties retrieving a detailed description for '{query}'.
    This could be due to temporary server issues or high demand.
    
    In the meantime, please enjoy the images related to '{query}' displayed below.
    These images should give you a visual representation of the topic.
    
    We apologize for the inconvenience and are working to resolve this issue.
    Try refreshing the page or searching again in a few minutes.
    """

def apply_custom_css():
    custom_css = """
    <style>
        :root {
            --bg-color: #1C1C1C;
            --text-color: #ffffff;
            --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            --gap-size: 12px; /* Define a CSS variable for gap size */
        }

        @media (prefers-color-scheme: light) {
            :root {
                --bg-color: #f0f0f0;
                --text-color: #000000;
                --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
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

        .description-box {
            background-color: var(--bg-color);
            border-radius: 20px; /* 3px */
            padding: 0.375rem; /* 6px */
            margin-bottom: 0.375rem; /* 6px */
            color: var(--text-color);
            font-family: 'Arial', sans-serif;
            font-size: 1rem; /* 16px */
            line-height: 1.6;
            letter-spacing: 0.3px;
            box-shadow: var(--box-shadow);
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
                grid-template-columns: repeat(2, 1fr);
                gap: 0.3rem;  /* 4.8px */
            }
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def search_instagram_images(query, num_images=7):
    L = instaloader.Instaloader()
    posts = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        for post in instaloader.Hashtag.from_name(L.context, query).get_posts():
            L.download_post(post, target=temp_dir)
            image_files = [f for f in os.listdir(temp_dir) if f.endswith('.jpg') or f.endswith('.png')]
            if image_files:
                image_path = os.path.join(temp_dir, image_files[0])
                posts.append(image_path)
            if len(posts) >= num_images:
                break
    except Exception as e:
        st.error(f"Error fetching Instagram images: {e}")
    
    return posts

def handle_image_search_and_description(query: str, num_images=7, source='google'):
    apply_custom_css()
    
    # Get brief description from Groq
    description = get_brief_description(query)
    
    # Search for images
    if source == 'instagram':
        image_urls = search_instagram_images(query, num_images)
    else:
        image_urls = search_images(query, num_images)
    
    # Prepare output
    output = {
        "description": description,
        "images": image_urls
    }
    
    return output

def encode_image_to_base64(image_path):
    """
    Encodes an image file to a base64 string.
    This is necessary for displaying local images in Streamlit using HTML.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def process_image_query(query: str, source='google'):
    result = handle_image_search_and_description(query, source=source)
    
    # Apply custom styling to the description box
    description_html = f'''
    <div class="description-box">
        {result["description"]}
    </div>
    '''
    
    st.markdown(description_html, unsafe_allow_html=True)
    
    if result['images']:
        unique_images = set()
        
        # Custom CSS is already applied via apply_custom_css()
        
        # Create a 2x2 grid for images
        image_html = '<div class="image-grid">'
        for image in result['images']:
            if len(unique_images) >= 4:
                break
            # Create a unique identifier for the image
            image_id = image if source == 'instagram' else hashlib.md5(image.encode()).hexdigest()
            
            if image_id not in unique_images:
                unique_images.add(image_id)
                # For Instagram images, encode the image to base64
                if source == 'instagram':
                    try:
                        encoded_image = encode_image_to_base64(image)
                        image_html += f'<div class="image-container"><img src="data:image/jpeg;base64,{encoded_image}" alt="Instagram Image"/></div>'
                    except Exception as e:
                        st.error(f"Error encoding image {image}: {e}")
                else:
                    image_html += f'<div class="image-container"><img src="{image}" alt="Google Image"/></div>'
        
        image_html += '</div>'
        st.markdown(image_html, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="description-box">No images found for the given query on {source.capitalize()}. Please try a different search term.</div>', unsafe_allow_html=True)
    
    return description_html

# This function would be called by the main chatbot logic
def handle_image_search(query: str, source='google'):
    return process_image_query(query, source)