import requests
import io
from PIL import Image, UnidentifiedImageError
import os
import json
import streamlit as st
from time import sleep

API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": "Bearer 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"}

# Retry logic in case of temporary issues with the API
def query(payload, retries=3, wait_time=2):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            # Return the response if status code is 200 OK
            if response.status_code == 200:
                return response
            else:
                print(f"API request failed with status code {response.status_code}. Retrying...")
                attempt += 1
                sleep(wait_time)  # Wait before retrying
        except requests.exceptions.RequestException as e:
            print(f"Network or server error: {e}")
            attempt += 1
            sleep(wait_time)
    
    # If all retries fail, return the last response or None
    return response if response else None

def apply_custom_css():
    custom_css = """
    <style>
        div[data-testid="stImage"] > img {
            border-radius: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease-in-out;
            max-width: 100%;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def generate_image_dev(prompt):
    apply_custom_css()

    print(f"Generating image with prompt: {prompt}")
    
    payload = {
        "inputs": prompt,
        "options": {
            "wait_for_model": True  # Forces the API to wait for model readiness
        }
    }
    
    try:
        response = query(payload)

        # If all retries failed, return error
        if not response or response.status_code != 200:
            error_message = f"API request failed with status code {response.status_code if response else 'N/A'}"
            print(error_message)
            return f"Error: {error_message}"

        # Check if the content type is an image
        if 'image' in response.headers.get('Content-Type', ''):
            image_bytes = response.content
        else:
            # Handle JSON response, which might indicate an error
            try:
                json_response = response.json()
                print(f"JSON response: {json.dumps(json_response, indent=2)}")
                return f"Error: {json_response.get('error', 'Unexpected JSON response')}"
            except json.JSONDecodeError:
                return "Error: Unexpected response format (neither image nor valid JSON)."

        # Try to process the image
        image = Image.open(io.BytesIO(image_bytes))
        output_dir = 'Images/flux_images'
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.join(output_dir, "dev.png")
        image.save(filename)
        print(f"Image saved to {filename}")
        return filename  # Return the path to the saved image

    except UnidentifiedImageError as e:
        # Handle image decoding issues
        print(f"Failed to identify image: {e}")
        debug_filename = 'debug_image_bytes.bin'
        with open(debug_filename, 'wb') as f:
            f.write(image_bytes)
        return f"Error: Failed to identify image. Debug data saved to {debug_filename}"
    
    except Exception as e:
        # Handle all other unexpected errors
        print(f"Unexpected error: {e}")
        return f"Error: Unexpected error occurred: {str(e)}"