import logging
from deepgram import DeepgramClient, SpeakOptions
import streamlit as st
import base64
import asyncio

# Initialize logging
logging.basicConfig(level=logging.INFO)

def text_to_speech_deepgram(text: str):
    API_KEY = "3956c457b60662f248076b00820080a8b72b1fbf"
    
    try:
        client = DeepgramClient(api_key=API_KEY)
        options = SpeakOptions(
            model="aura-stella-en",
            encoding="linear16",  # Consider changing to a lower encoding for speed
            container="wav",
            sample_rate=24000  # Lower sample rate for faster processing
        )

        SPEAK_OPTIONS = {"text": text}

        # Instead of saving to a file, stream the audio directly
        response = client.speak.v("1").send(SPEAK_OPTIONS, options)
        audio_data = response.audio  # Assuming this gets you the audio data directly

        logging.info("Successfully generated speech")
        return audio_data  # Return audio data directly
        
    except Exception as e:
        logging.error(f"Failed to convert text to speech using Deepgram: {e}")
        return None

def say(text: str):
    audio_data = text_to_speech_deepgram(text)
    
    if audio_data:
        try:
            # Encode the audio bytes to base64
            audio_base64 = base64.b64encode(audio_data).decode()
            
            # Create an HTML audio element with autoplay
            audio_html = f'''
                <audio autoplay="true">
                    <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                    Your browser does not support the audio element.
                </audio>
            '''
            
            # Display the audio using HTML
            st.markdown(audio_html, unsafe_allow_html=True)
            
            logging.info("Successfully streamed audio")
        except Exception as e:
            logging.error(f"Failed to stream audio: {e}")
    else:
        logging.error("No audio data generated to stream")
