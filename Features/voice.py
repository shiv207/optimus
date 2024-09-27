import logging
from deepgram import DeepgramClient, SpeakOptions
from playsound import playsound

def text_to_speech_deepgram(text: str):
    API_KEY = "3956c457b60662f248076b00820080a8b72b1fbf"
    OUTPUT_FILE = "Backend/output.wav"
    
    try:
        client = DeepgramClient(api_key=API_KEY)
        options = SpeakOptions(
            model="aura-orion-en",
            encoding="linear16",
            container="wav",
            sample_rate=48000
        )
        SPEAK_OPTIONS = {"text": text}
        response = client.speak.v("1").save(OUTPUT_FILE, SPEAK_OPTIONS, options)
        
        logging.info(f"Successfully generated speech and saved to {OUTPUT_FILE}")
        return OUTPUT_FILE
        
    except Exception as e:
        logging.error(f"Failed to convert text to speech using Deepgram: {e}")
        return None

def say(text: str):
    audio_file = text_to_speech_deepgram(text)
    if audio_file:
        try:
            playsound(audio_file)
            logging.info(f"Successfully played audio from {audio_file}")
        except Exception as e:
            logging.error(f"Failed to play audio: {e}")
    else:
        logging.error("No audio file generated to play")
