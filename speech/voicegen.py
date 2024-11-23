import logging
from openai_unofficial import OpenAIUnofficial
import streamlit as st
import os
import tempfile
import base64

def text_to_speech_openai(text: str):
    try:
        client = OpenAIUnofficial()
        audio_data = client.audio.create(
            input_text=text,
            model="tts-1-hd",
            voice="alloy"
        )

        # Save audio to temporary file and stream audio back immediately
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
            temp_file.write(audio_data)

        logging.info("Successfully generated speech to temporary file")
        return temp_filename

    except Exception as e:
        logging.error(f"Failed to convert text to speech using OpenAI: {e}")
        return None

def say(text: str):
    audio_file = text_to_speech_openai(text)
    
    if audio_file and os.path.exists(audio_file):
        try:
            with open(audio_file, "rb") as file:
                audio_base64 = base64.b64encode(file.read()).decode()
            
            audio_html = f'''
                <audio autoplay="true">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
            '''
            
            st.markdown(audio_html, unsafe_allow_html=True)
            logging.info("Successfully streamed audio from temporary file")

            os.unlink(audio_file)
            
        except Exception as e:
            logging.error(f"Failed to stream audio: {e}")
    else:
        logging.error("No audio file generated to stream")
