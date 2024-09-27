import logging
from deepgram import DeepgramClient, SpeakOptions
from io import BytesIO
import streamlit as st
import os

def text_to_speech_deepgram(text: str):
    API_KEY = "3956c457b60662f248076b00820080a8b72b1fbf"
    OUTPUT_FILE = "Backend/output.wav"  # Save the audio file on the server

    try:
        client = DeepgramClient(api_key=API_KEY)
        options = SpeakOptions(
            model="aura-orion-en",
            encoding="linear16",
            container="wav",
            sample_rate=48000
        )

        SPEAK_OPTIONS = {"text": text}

        # Save the audio file to the specified OUTPUT_FILE path
        response = client.speak.v("1").save(OUTPUT_FILE, SPEAK_OPTIONS, options)
        
        logging.info(f"Successfully generated speech and saved to {OUTPUT_FILE}")
        return OUTPUT_FILE  # Return the saved file path
        
    except Exception as e:
        logging.error(f"Failed to convert text to speech using Deepgram: {e}")
        return None

def say(text: str):
    audio_file = text_to_speech_deepgram(text)
    
    if audio_file and os.path.exists(audio_file):
        try:
            # Display a player in Streamlit that plays the saved audio file
            audio_bytes = open(audio_file, "rb").read()  # Read the audio file as binary data
            st.audio(audio_bytes, format="audio/wav")  # Play the audio using Streamlit's audio component
            logging.info(f"Successfully played audio from {audio_file}")
        except Exception as e:
            logging.error(f"Failed to play audio: {e}")
    else:
        logging.error("No audio file generated to play")
