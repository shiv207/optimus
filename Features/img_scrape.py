import streamlit as st
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Replace with your actual keys
API_KEY = "AIzaSyDHyK7T14VG8vMwaJhQicBRovAb76dkdxk"
SEARCH_ENGINE_ID = "d6604d6b7dbb9447a"
GROQ_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)

def search_images(query, num_images=7):
    service = build("customsearch", "v1", developerKey=API_KEY)
    try:
        all_images = []
        # We'll make multiple requests if num_images > 10
        for start_index in range(1, min(num_images * 2, 20), 10):
            res = service.cse().list(
                q=query,
                cx=SEARCH_ENGINE_ID,
                searchType='image',
                num=min(10, num_images * 2 - len(all_images)),
                start=start_index
            ).execute()
            
            all_images.extend([item['link'] for item in res.get('items', [])])
            
            if len(all_images) >= num_images * 2:
                break
        
        # Filter out Instagram URLs and limit to the desired number of images
        filtered_images = [
            img_url for img_url in all_images
            if 'instagram.com' not in img_url.lower()
        ][:num_images]
        
        return filtered_images
    except Exception as e:
        st.error(f"Error fetching images: {e}")
        return []

def get_brief_description(query):
    prompt = f"Tell me a 10-line description of the object '{query}'. Do not describe the query itself, but describe the object that was asked about in the query."
    
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
        st.error(f"Error fetching description from Groq: {e}")


def handle_image_search_and_description(query: str, num_images=5):
    # Get brief description from Groq
    description = get_brief_description(query)
    
    # Search for images
    image_urls = search_images(query, num_images)
    
    # Prepare output
    output = {
        "description": description,
        "images": image_urls
    }
    
    return output
    image_urls = search_images(query, num_images)
    
    # Prepare output
    output = {
        "description": description,
        "images": image_urls
    }
    
    return output

def process_image_query(query: str):
    # CSS for rounded images and description with light theme
    custom_css = """
    <style>
        :root {
            --bg-color: #1C1C1C;
            --text-color: #ffffff;
            --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        @media (prefers-color-scheme: light) {
            :root {
                --bg-color: #f0f0f0;
                --text-color: #000000;
                --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            }
        }

        .img-rounded {
            border-radius: 20px;  /* Rounded corners */
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .img-rounded:hover {
            transform: scale(1.03);  /* Slight zoom effect on hover */
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        .stChatMessage {
            color: var(--text-color);
        }
        
        .description-box {
            background-color: var(--bg-color);
            background-size: cover;
            background-position: center;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            color: var(--text-color);
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            line-height: 1.5;
            letter-spacing: 0.5px;
            box-shadow: var(--box-shadow);
        }

        /* Additional styles for better light theme visibility */
        @media (prefers-color-scheme: light) {
            .img-rounded {
                border: 1px solid #ddd;
            }

            .description-box {
                border: 1px solid #ddd;
            }
        }
    </style>
    """
    
    # Inject the CSS into the app
    st.markdown(custom_css, unsafe_allow_html=True)

    # Process the image query and handle the image search result
    result = handle_image_search_and_description(query)
    
    # Display the description
    if result['description']:
        st.markdown(f'<div class="description-box">{result["description"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="description-box">No description available for the given query.</div>', unsafe_allow_html=True)
    
    # Filter out invalid or empty URLs
    if result['images']:
        valid_image_urls = [img_url for img_url in result['images'] if img_url and isinstance(img_url, str) and img_url.strip()]
        
        # Only proceed if valid images exist
        if valid_image_urls:
            cols = st.columns(min(3, len(valid_image_urls)))  # Create a column for each image, max 3
            for i, img_url in enumerate(valid_image_urls[:3]):  # Limit to 3 images
                with cols[i % 3]:
                    st.markdown(f'<img src="{img_url}" class="img-rounded" style="width:100%;">', unsafe_allow_html=True)
        else:
            # If no valid images after filtering
            st.markdown('<div class="stChatMessage message img-scrape">No valid images found for the given query.</div>', unsafe_allow_html=True)
    else:
        # If there were no images in the result
        st.markdown('<div class="stChatMessage message img-scrape">No images found for the given query.</div>', unsafe_allow_html=True)

def handle_image_search(query: str):
    return process_image_query(query)

# Main execution
if __name__ == "__main__":
    st.title("Image Search and Description")
    query = st.text_input("Enter your search query:")
    if query:
        handle_image_search(query)


