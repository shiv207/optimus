import logging
from deepgram import DeepgramClient, SpeakOptions
import streamlit as st
import os
import tempfile
import base64
from dotenv import load_dotenv

load_dotenv()
DEEPGRAM_API = os.getenv("DEEPGRAM_API")

def text_to_speech_deepgram(text: str):
    
    try:
        client = DeepgramClient(api_key=DEEPGRAM_API)
        options = SpeakOptions(
            model="aura-stella-en",
            encoding="linear16",
            container="wav",
            sample_rate=48000
        )

        # Save audio to temporary file and stream audio back immediately
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_filename = temp_file.name
            client.speak.v("1").save(temp_filename, {"text": text}, options)

        logging.info("Successfully generated speech to temporary file")
        return temp_filename  # Return path directly for quicker access
        
    except Exception as e:
        logging.error(f"Failed to convert text to speech using Deepgram: {e}")
        return None

def say(text: str):
    audio_file = text_to_speech_deepgram(text)
    
    if audio_file and os.path.exists(audio_file):
        try:
            # Stream the audio back in base64 format
            with open(audio_file, "rb") as file:
                audio_base64 = base64.b64encode(file.read()).decode()
            
            audio_html = f'''
                <audio autoplay="true">
                    <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                    Your browser does not support the audio element.
                </audio>
            '''
            
            st.markdown(audio_html, unsafe_allow_html=True)
            logging.info("Successfully streamed audio from temporary file")

            os.unlink(audio_file)  # Clean up immediately for lower latency
            
        except Exception as e:
            logging.error(f"Failed to stream audio: {e}")
    else:
        logging.error("No audio file generated to stream")
