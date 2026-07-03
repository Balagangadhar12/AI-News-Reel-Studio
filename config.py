import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    # Directories
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'output'
    ASSETS_FOLDER = BASE_DIR / 'assets'
    STATIC_FOLDER = BASE_DIR / 'static'
    GENERATED_FOLDER = STATIC_FOLDER / 'generated'
    
    # Ensure directories exist
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, ASSETS_FOLDER, STATIC_FOLDER, GENERATED_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)
        
    # Flask Settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'default-dev-secret-key-18374829374')
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')
    
    # Available high-quality voices for Edge-TTS
    TTS_VOICES = {
        'en-US-GuyNeural': {'name': 'English (US) - Guy (Male)', 'lang': 'en', 'gender': 'Male'},
        'en-US-AriaNeural': {'name': 'English (US) - Aria (Female)', 'lang': 'en', 'gender': 'Female'},
        'en-GB-RyanNeural': {'name': 'English (UK) - Ryan (Male)', 'lang': 'en', 'gender': 'Male'},
        'en-GB-SoniaNeural': {'name': 'English (UK) - Sonia (Female)', 'lang': 'en', 'gender': 'Female'},
        'es-ES-AlvaroNeural': {'name': 'Spanish (Spain) - Alvaro (Male)', 'lang': 'es', 'gender': 'Male'},
        'es-ES-ElviraNeural': {'name': 'Spanish (Spain) - Elvira (Female)', 'lang': 'es', 'gender': 'Female'},
        'fr-FR-HenriNeural': {'name': 'French (France) - Henri (Male)', 'lang': 'fr', 'gender': 'Male'},
        'fr-FR-DeniseNeural': {'name': 'French (France) - Denise (Female)', 'lang': 'fr', 'gender': 'Female'},
        'de-DE-ConradNeural': {'name': 'German (Germany) - Conrad (Male)', 'lang': 'de', 'gender': 'Male'},
        'de-DE-KatjaNeural': {'name': 'German (Germany) - Katja (Female)', 'lang': 'de', 'gender': 'Female'},
        'it-IT-DiegoNeural': {'name': 'Italian (Italy) - Diego (Male)', 'lang': 'it', 'gender': 'Male'},
        'it-IT-ElsaNeural': {'name': 'Italian (Italy) - Elsa (Female)', 'lang': 'it', 'gender': 'Female'},
    }
    
    # Fallback/Default Voice
    DEFAULT_VOICE = 'en-US-GuyNeural'
    
    # Video Settings
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920
    FPS = 24
