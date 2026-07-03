import asyncio
import edge_tts
import os
from pathlib import Path
from config import Config

def generate_tts_file(text, voice, output_path):
    """
    Generates an MP3 audio file using edge-tts.
    Runs the asynchronous edge-tts call synchronously within a new event loop.
    """
    # Ensure parent directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Use fallback if voice is not in system config
    if voice not in Config.TTS_VOICES:
        voice = Config.DEFAULT_VOICE
        
    try:
        # Create a new event loop for this execution thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def save_tts():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
        loop.run_until_complete(save_tts())
        loop.close()
        return True
    except Exception as e:
        print(f"Edge-TTS failed to generate audio: {e}. Trying gTTS fallback...")
        try:
            from gtts import gTTS
            lang_code = Config.TTS_VOICES.get(voice, {}).get('lang', 'en')
            tts = gTTS(text=text, lang=lang_code)
            tts.save(output_path)
            return True
        except Exception as ge:
            print(f"gTTS fallback also failed: {ge}")
            # Generate a silent audio track or mock audio track if all else fails
            return create_silent_audio(output_path, duration=5.0)

def create_silent_audio(output_path, duration=5.0):
    """
    Creates a basic silent audio file using moviepy as a last-resort fallback.
    """
    try:
        from moviepy import AudioClip
        # Generate an empty silent audio clip
        make_frame = lambda t: 0.0
        clip = AudioClip(make_frame, duration=duration, fps=44100)
        clip.write_audiofile(output_path, fps=44100, logger=None)
        clip.close()
        return True
    except Exception as e:
        print(f"Failed to generate silent fallback audio: {e}")
        return False
