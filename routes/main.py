from flask import Blueprint, render_template, send_from_directory, abort, Response, current_app
import json
import os
from pathlib import Path
from config import Config

main_bp = Blueprint('main', __name__)

def load_history():
    """
    Loads generation history from a local JSON database file.
    """
    history_file = Config.OUTPUT_FOLDER / 'history.json'
    if not history_file.exists():
        return {}
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading history.json: {e}")
        return {}

@main_bp.route('/')
def index():
    """
    Renders the landing page, listing recent reels and trending items.
    """
    history = load_history()
    # Sort history by date descending
    recent_reels = sorted(
        history.values(),
        key=lambda x: x.get('created_at', ''),
        reverse=True
    )[:6]  # Show top 6
    
    # Trending list
    trending_topics = [
        "AI Breakthroughs",
        "Space Exploration",
        "Climate Technologies",
        "Future of Robotics",
        "Cybersecurity Trends"
    ]
    
    return render_template(
        'index.html',
        recent_reels=recent_reels,
        trending_topics=trending_topics,
        voices=Config.TTS_VOICES
    )

@main_bp.route('/result/<task_id>')
def result(task_id):
    """
    Renders the result page for a specific video generation task.
    """
    history = load_history()
    reel = history.get(task_id)
    
    if not reel:
        # Check if file exists anyway
        video_path = Config.OUTPUT_FOLDER / f"{task_id}.mp4"
        if video_path.exists():
            # Create a basic entry if the history JSON is out of sync
            reel = {
                "task_id": task_id,
                "title": "Restored Video Reel",
                "summary": "This video was restored from local storage.",
                "scenes": []
            }
        else:
            abort(404, description="Reel not found or still generating.")
            
    return render_template('result.html', reel=reel)

@main_bp.route('/videos/<filename>')
def serve_video(filename):
    """
    Serves a generated video file directly.
    """
    return send_from_directory(Config.OUTPUT_FOLDER, filename)

@main_bp.route('/download/video/<task_id>')
def download_video(task_id):
    """
    Forces download of the generated MP4 file.
    """
    filename = f"{task_id}.mp4"
    file_path = Config.OUTPUT_FOLDER / filename
    if not file_path.exists():
        abort(404, description="Video file not found.")
    return send_from_directory(Config.OUTPUT_FOLDER, filename, as_attachment=True)

@main_bp.route('/download/audio/<task_id>')
def download_audio(task_id):
    """
    Extracts the audio track from the MP4 dynamically (if not already extracted)
    and forces download of the MP3/AAC file.
    """
    audio_filename = f"{task_id}.mp3"
    audio_path = Config.OUTPUT_FOLDER / audio_filename
    video_path = Config.OUTPUT_FOLDER / f"{task_id}.mp4"
    
    if not video_path.exists():
        abort(404, description="Video file not found.")
        
    if not audio_path.exists():
        # Dynamically extract audio from MP4 using MoviePy
        try:
            from moviepy import VideoFileClip
            video_clip = VideoFileClip(str(video_path))
            if video_clip.audio:
                video_clip.audio.write_audiofile(str(audio_path), logger=None)
            video_clip.close()
        except Exception as e:
            print(f"Error extracting audio: {e}")
            abort(500, description="Could not extract audio track.")
            
    return send_from_directory(Config.OUTPUT_FOLDER, audio_filename, as_attachment=True)

@main_bp.route('/download/script/<task_id>')
def download_script(task_id):
    """
    Generates and returns the script text file.
    """
    history = load_history()
    reel = history.get(task_id)
    if not reel:
        abort(404, description="Reel script not found.")
        
    script_content = f"TITLE: {reel.get('title')}\n"
    script_content += f"SUMMARY: {reel.get('summary')}\n\n"
    script_content += "="*40 + "\n"
    script_content += "SCENE BY SCENE SCRIPT\n"
    script_content += "="*40 + "\n\n"
    
    for scene in reel.get('scenes', []):
        script_content += f"SCENE {scene.get('scene_number')} ({scene.get('duration')}s):\n"
        script_content += f"Narration: {scene.get('narration')}\n"
        script_content += f"Visual Prompt: {scene.get('image_prompt')}\n\n"
        
    return Response(
        script_content,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename={task_id}_script.txt"}
    )
