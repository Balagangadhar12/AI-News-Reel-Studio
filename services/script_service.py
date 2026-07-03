import re

def validate_and_sanitize_script(script_data):
    """
    Validates and cleans script data from the LLM.
    Ensures that narration texts are safe and scene durations are estimated properly
    if they are missing or out of bounds.
    """
    if not isinstance(script_data, dict):
        raise ValueError("Script data must be a dictionary.")
        
    sanitized = {
        "title": script_data.get("title", "Breaking News").strip(),
        "summary": script_data.get("summary", "").strip(),
        "scenes": []
    }
    
    scenes = script_data.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) == 0:
        raise ValueError("Script data must contain a non-empty list of scenes.")
        
    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
            
        narration = scene.get("narration", "").strip()
        # Clean up any quotes or braces in narration
        narration = re.sub(r'["\'\{\}\[\]]', '', narration)
        
        image_prompt = scene.get("image_prompt", "").strip()
        if not image_prompt:
            image_prompt = f"Abstract background representing {sanitized['title']}, modern colors, 9:16 aspect ratio"
            
        # Calculate duration based on words-per-minute (130 WPM / 2.16 words per second)
        word_count = len(narration.split())
        estimated_duration = max(4.0, round(word_count / 2.2, 1))
        
        # Override with LLM provided duration if it's reasonable
        duration = scene.get("duration")
        if duration is not None:
            try:
                duration = float(duration)
                if 2.0 <= duration <= 15.0:
                    estimated_duration = duration
            except (ValueError, TypeError):
                pass
                
        sanitized["scenes"].append({
            "scene_number": scene.get("scene_number", idx + 1),
            "narration": narration,
            "image_prompt": image_prompt,
            "duration": estimated_duration
        })
        
    return sanitized
