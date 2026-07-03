# AI News Reel Studio 🎬

AI News Reel Studio is a complete, production-quality full-stack web application that automatically converts online news articles or global topics into professional vertical short-form videos (Instagram Reels, YouTube Shorts, TikToks) using AI.

---

## Key Features

- **Double-Entry Input**: Paste a direct news article URL for scraping OR search keyword topics to query NewsAPI/Google News RSS.
- **Scrubbing Pipeline**: Clean text extraction using BeautifulSoup, filtering out cookie notices, navigational links, and advertising blocks.
- **Gemini AI Intelligence**: Summarizes news, structures a multi-scene timing-aligned narration script, and drafts visual prompts tailored for image generation.
- **Edge-TTS Integration**: Converts narration scripts into expressive, human-like voiceovers in multiple accents and languages.
- **AI Visual Generation**: Sourced via Pollinations.ai (free unauthenticated text-to-image API) with beautiful PIL-generated gradient placeholders as fallback.
- **Custom Pillow Subtitle Engine**: MoviePy's standard `TextClip` requires ImageMagick, which is notoriously difficult to set up on Windows. This app implements a custom PIL caption drawer, rendering high-contrast yellow subtitle text on semi-transparent dark rounded capsules directly on top of video frames. Captions remain static in the lower-third while the background image undergoes a smooth Ken Burns scale zoom!
- **Futuristic Glassmorphic Dark UI**: Custom-built style sheets featuring particle canvas drift animations, landing-page typing loops, and real-time generation pipelines with progressive timeline checkmarks.

---

## Technical Stack

- **Backend**: Python, Flask, REST APIs, Dotenv, Asyncio
- **Frontend**: HTML5, CSS3 (Vanilla), Bootstrap 5, Vanilla JavaScript, Font Awesome
- **AI Engine**: Google Gemini API (`google-generativeai`), prompt engineering
- **Media Engine**: MoviePy (Video assembly), Pillow (PIL, Subtitle overlays & fallbacks), Edge-TTS / gTTS (Voiceovers), Requests, BeautifulSoup4 (Scraping)

---

## Project Structure

```
AI-News-Reel-Studio/
├── app.py                      # Flask Application factory and startup
├── config.py                   # Central config loader, paths, and voice profiles
├── requirements.txt            # Python dependencies
├── .env                        # Local credentials configuration
├── README.md                   # Project documentation
├── routes/
│   ├── __init__.py
│   ├── main.py                 # Page templates and download routes
│   └── api.py                  # API routes & in-memory async thread worker
├── services/
│   ├── __init__.py
│   ├── news_service.py         # NewsAPI & Google News RSS search
│   ├── article_parser.py       # Custom BeautifulSoup web scraper
│   ├── llm_service.py          # Gemini API connector & mockup fallback
│   ├── script_service.py       # Sanitizes scene schemas & timing forecasts
│   ├── tts_service.py          # edge-tts voiceover compiler
│   ├── image_service.py        # Pollinations.ai & PIL canvas fallbacks
│   ├── subtitle_service.py     # High-contrast Pillow frame captions
│   └── video_service.py        # MoviePy Ken Burns scale and compiler
├── static/
│   ├── css/
│   │   └── style.css           # UI layout and glassmorphism styling
│   └── js/
│   │   └── main.js            # Particle canvasing, polling loops, and copying actions
├── templates/
│   ├── base.html               # General base structure & toast containers
│   ├── index.html              # Twin-action inputs and timeline monitoring
│   └── result.html             # Video preview, action triggers, and visuals gallery
├── uploads/                    # Temporary audio rendering workspace
└── output/                     # Exported vertical videos & gallery DB
```

---

## Installation & Setup

### 1. Clone the repository and navigate inside
```powershell
cd AI-News-Reel-Studio
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Setup environment variables
Create a `.env` file in the root directory (or rename the provided `.env` template) and configure your API keys:
```env
# Create your Google Gemini API key at: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# News API Settings (Optional - fallback RSS feeds are used if not provided)
NEWS_API_KEY=your_news_api_key_here
```
*Note: If the `GEMINI_API_KEY` is not provided, the application will automatically fall back to an offline "Mock Script Mode" generating demo technology reels so you can still preview rendering outputs.*

---

## Running the Application

Start the Flask local development server:
```powershell
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## Subtitle Customization
Subtitles are rendered in [services/subtitle_service.py](file:///c:/Users/pbala/Desktop/Projects/AI-News-Reel-Studio/services/subtitle_service.py). 
You can customize the layout easily:
- Adjust font sizes, margins, or anchor positions.
- Modify colours (currently high contrast yellow `#facc15` inside a black capsule transparent background `fill=(0, 0, 0, 160)`).
