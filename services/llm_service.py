import os
import json
import google.generativeai as genai
from config import Config

def init_gemini():
    """
    Initialize the Gemini API configuration.
    """
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in configuration. Mock LLM service will be used.")
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return False

def generate_video_script(article_title, article_text):
    """
    Summarizes the article and generates a scene-by-scene narration script with image prompts.
    Uses Gemini API if available, otherwise falls back to generating a mock script.
    """
    has_api = init_gemini()
    
    if not has_api:
        return generate_mock_script(article_title, article_text)
        
    prompt = f"""
    You are an expert news writer and social media producer. Analyze this news article:
    
    Title: {article_title}
    Body: {article_text}
    
    Create a vertical video short script (60 seconds maximum, suitable for Instagram Reels or YouTube Shorts) based on this news.
    The output MUST be in JSON format matching this EXACT schema:
    {{
        "title": "A short, engaging hook title for the reel",
        "summary": "A 1-2 sentence high-level summary of the news",
        "scenes": [
            {{
                "scene_number": 1,
                "narration": "The narration voiceover script for this scene. Keep it energetic, clear, and easy to speak. (Around 15-20 words)",
                "image_prompt": "A detailed, high-quality prompt for generating a vertical 9:16 image representing this scene. Describe subject, lighting, mood, cinematic details, avoiding text or abstract jargon. (e.g. 'Cinematic photo of a rocket launch, bright fire flames, dramatic smoke, vertical composition, 8k resolution')",
                "duration": 8
            }}
        ]
    }}
    
    Guidelines:
    1. Structure the video into 4 to 6 scenes total.
    2. The narration across all scenes should flow naturally and complete within 60 seconds (around 120-150 words total).
    3. Ensure the duration is between 5 and 10 seconds per scene. The sum of scene durations should be around 35-50 seconds.
    4. Make the image prompts highly detailed, visually concrete, and suitable for a text-to-image generator.
    5. Return ONLY the JSON object. Do not include markdown codeblocks or other formatting outside the JSON structure.
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Request JSON output specifically
        generation_config = {
            "response_mime_type": "application/json"
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Parse the JSON response
        response_text = response.text.strip()
        data = json.loads(response_text)
        
        # Validate structure
        if "title" in data and "summary" in data and "scenes" in data:
            return {
                "success": True,
                "data": data,
                "error": None
            }
        else:
            raise ValueError("Returned JSON is missing required fields.")
            
    except Exception as e:
        print(f"Gemini generation error: {e}")
        return generate_mock_script(article_title, article_text, error=str(e))

def generate_mock_script(title, text, error=None):
    """
    Generates a high-quality mock script to keep the app working if Gemini key is missing/fails.
    """
    print("Generating mock script fallback...")
    
    # Use keywords in title/text to make the mock somewhat relevant
    keywords = ["AI", "Tech", "Space", "Crypto", "Finance", "Science", "Business", "Sports", "Politics"]
    detected_topic = "General News"
    
    for kw in keywords:
        if kw.lower() in title.lower() or kw.lower() in text.lower():
            detected_topic = kw
            break
            
    mock_data = {
        "title": f"Breaking News: The Future of {detected_topic}!",
        "summary": f"This video covers the latest developments in {detected_topic} and what it means for the future.",
        "scenes": [
            {
                "scene_number": 1,
                "narration": f"Welcome to AI News Reel Studio! Today we are looking at the massive shifts happening in {detected_topic}.",
                "image_prompt": f"Close-up of a futuristic glowing holographic interface, high tech laboratory, soft dramatic neon lighting, depth of field, ultra-detailed, vertical 9:16",
                "duration": 7
            },
            {
                "scene_number": 2,
                "narration": "Experts are surprised by the rapid pace of change, calling it a historic turning point.",
                "image_prompt": "Cinematic shot of professional scientists in a dark modern control room looking at glowing blue data screens, volumetric lighting, photorealistic, 9:16 aspect ratio",
                "duration": 8
            },
            {
                "scene_number": 3,
                "narration": "As technology advances, new opportunities and challenges are emerging across the industry.",
                "image_prompt": "Concept art of a modern smart city skyline at sunset, light trails, high-speed trains, aerial view, cinematic concept art, vertical layout",
                "duration": 8
            },
            {
                "scene_number": 4,
                "narration": "How will this affect your daily life? Make sure to follow for more daily updates on these stories!",
                "image_prompt": "Cinematic portrait of a young person smiling while using a clean transparent phone interface, soft lighting, modern workplace background, 8k, 9:16",
                "duration": 7
            }
        ]
    }
    
    return {
        "success": True,
        "data": mock_data,
        "error": f"Using Mock Script Fallback (Gemini key not configured or errored: {error})" if error else "Mock Script Mode"
    }
