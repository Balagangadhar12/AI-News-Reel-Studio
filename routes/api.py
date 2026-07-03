from flask import Blueprint, request, jsonify
import uuid
import threading
import datetime
import json
import os
import shutil
import re
from pathlib import Path
from config import Config
from services import (
    news_service,
    article_parser,
    llm_service,
    script_service,
    tts_service,
    image_service,
    video_service
)

api_bp = Blueprint('api', __name__)

# Global dictionary to track active task progress in-memory
ACTIVE_TASKS = {}
history_lock = threading.Lock()

def compact_text(value, max_chars):
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rsplit(" ", 1)[0].strip() + "..."

def build_basic_script(title, text):
    """
    Creates a tiny script without calling an LLM.
    Used by quick mode for fast local rendering.
    """
    clean_title = compact_text(title or "Latest News", 95)
    clean_text = compact_text(text, 260)
    summary = clean_text
    if not summary:
        summary = "A quick update on this developing story."

    return {
        "title": clean_title,
        "summary": summary,
        "scenes": [
            {
                "scene_number": 1,
                "narration": clean_title,
                "image_prompt": f"LATEST NEWS\n\n{clean_title}",
                "duration": 4.0
            },
            {
                "scene_number": 2,
                "narration": f"Here is the key update. {summary}",
                "image_prompt": f"KEY UPDATE\n\n{summary}",
                "duration": 5.0
            },
            {
                "scene_number": 3,
                "narration": summary,
                "image_prompt": "FOLLOW FOR MORE\n\nQuick news update",
                "duration": 4.0
            }
        ]
    }

def update_task_progress(task_id, progress, stage, status="processing", error=None, result=None):
    """
    Updates the global in-memory progress tracker for a specific task.
    """
    ACTIVE_TASKS[task_id] = {
        "status": status,
        "progress": progress,
        "stage": stage,
        "error": error,
        "result": result,
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def save_to_history(task_id, reel_record):
    """
    Saves a completed reel's metadata to the local JSON history file in a thread-safe way.
    """
    history_file = Config.OUTPUT_FOLDER / 'history.json'
    
    with history_lock:
        history = {}
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                print(f"Error reading history.json for writing: {e}")
                history = {}
                
        history[task_id] = reel_record
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing to history.json: {e}")

def background_generation_worker(task_id, source_url, search_query, voice, selected_article=None, fast_mode=True):
    """
    Worker thread that runs the entire reel generation pipeline.
    """
    temp_dir = Config.UPLOAD_FOLDER / task_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = Config.GENERATED_FOLDER / task_id
    images_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Initializing (5%)
        update_task_progress(task_id, 5, "Initializing workspace")
        
        title = ""
        text = ""
        
        # Step 2: Fetch Article content (20%)
        if source_url:
            update_task_progress(task_id, 10, "Extracting article from URL")
            res = article_parser.extract_article_text(source_url)
            if not res["success"]:
                raise ValueError(res["error"])
            title = res["title"]
            text = res["text"]
        elif selected_article:
            title = selected_article.get("title", "").strip()
            source = selected_article.get("source", "").strip()
            description = compact_text(selected_article.get("description", ""), 260)
            content = compact_text(selected_article.get("content", ""), 260)
            url = selected_article.get("url", "").strip()

            if not title:
                raise ValueError("Selected headline is missing a title.")

            update_task_progress(task_id, 10, "Preparing selected headline")
            text_parts = [
                description,
                content,
                f"Source: {source}" if source else "",
                f"Original article URL: {url}" if url else ""
            ]
            text = "\n\n".join(part for part in text_parts if part)

            if url and not fast_mode:
                update_task_progress(task_id, 15, "Trying to enrich headline from source")
                res = article_parser.extract_article_text(url)
                if res["success"] and len(res.get("text", "")) > len(text):
                    title = res.get("title") or title
                    text = res["text"]

            if len(text.strip()) < 50:
                text = f"{title}\n\nThis is a latest news headline from {source or 'a news source'}. Create a concise short news reel from the available headline."
        elif search_query:
            update_task_progress(task_id, 10, f"Searching trending news for '{search_query}'")
            articles = news_service.search_news(search_query)
            if not articles:
                raise ValueError(f"No news articles found for query: '{search_query}'")
                
            # Take first article and scrape it
            top_article = articles[0]
            update_task_progress(task_id, 15, "Parsing top search result")
            res = article_parser.extract_article_text(top_article["url"])
            if not res["success"]:
                # If scraping the top URL fails, fallback to using the article description/content directly
                if top_article["description"] or top_article["content"]:
                    title = top_article["title"]
                    text = f"{top_article['description']}\n\n{top_article['content']}"
                else:
                    raise ValueError(f"Failed to parse source article: {res['error']}")
            else:
                title = res["title"]
                text = res["text"]
        else:
            raise ValueError("Either source_url or search_query must be provided.")
            
        if fast_mode:
            update_task_progress(task_id, 30, "Creating quick basic script")
            sanitized_script = build_basic_script(title, text)
            scenes = sanitized_script["scenes"]

            update_task_progress(task_id, 45, "Generating quick voice narration")
            for idx, scene in enumerate(scenes):
                scene_num = scene["scene_number"]
                update_task_progress(task_id, 45 + int((idx/len(scenes)) * 20), f"Narrating quick scene {scene_num} of {len(scenes)}")
                audio_path = temp_dir / f"scene_{scene_num}.mp3"
                success = tts_service.generate_tts_file(scene["narration"], voice, str(audio_path))
                scene["audio_path"] = str(audio_path) if success else ""

            update_task_progress(task_id, 65, "Creating local text-card visuals")
            for idx, scene in enumerate(scenes):
                scene_num = scene["scene_number"]
                update_task_progress(task_id, 65 + int((idx/len(scenes)) * 15), f"Creating card {scene_num} of {len(scenes)}")
                image_path = images_dir / f"scene_{scene_num}.jpg"
                success = image_service.create_gradient_placeholder(scene["image_prompt"], str(image_path), width=720, height=1280)
                if not success:
                    raise ValueError(f"Failed to generate visual card for scene {scene_num}")
                scene["image_path"] = str(image_path)
        else:
            # Step 3: Summarize & Script (40%)
            update_task_progress(task_id, 25, "Analyzing content & drafting script")
            llm_res = llm_service.generate_video_script(title, text)
            if not llm_res["success"]:
                raise ValueError(llm_res["error"])
                
            update_task_progress(task_id, 40, "Sanitizing script scenes")
            sanitized_script = script_service.validate_and_sanitize_script(llm_res["data"])
            
            # Step 4: TTS voiceover generation (60%)
            update_task_progress(task_id, 45, "Generating high-quality narration voiceovers")
            scenes = sanitized_script["scenes"]
            
            for idx, scene in enumerate(scenes):
                scene_num = scene["scene_number"]
                update_task_progress(task_id, 45 + int((idx/len(scenes)) * 15), f"Narrating scene {scene_num} of {len(scenes)}")
                audio_path = temp_dir / f"scene_{scene_num}.mp3"
                
                success = tts_service.generate_tts_file(scene["narration"], voice, str(audio_path))
                if not success:
                    raise ValueError(f"Failed to generate TTS audio for scene {scene_num}")
                scene["audio_path"] = str(audio_path)
                
            # Step 5: Image asset generation (80%)
            update_task_progress(task_id, 60, "Generating context-aware AI visual assets")
            for idx, scene in enumerate(scenes):
                scene_num = scene["scene_number"]
                update_task_progress(task_id, 60 + int((idx/len(scenes)) * 20), f"Drawing scene {scene_num} of {len(scenes)}")
                image_path = images_dir / f"scene_{scene_num}.jpg"
                
                success = image_service.generate_image_for_prompt(scene["image_prompt"], str(image_path))
                if not success:
                    raise ValueError(f"Failed to generate visual asset for scene {scene_num}")
                scene["image_path"] = str(image_path)
            
        # Step 6: Video compile & Subtitle render (95%)
        update_task_progress(task_id, 82, "Compiling quick reel" if fast_mode else "Compiling video clips and overlaying captions")
        output_path = Config.OUTPUT_FOLDER / f"{task_id}.mp4"
        
        if fast_mode:
            video_service.assemble_basic_reel(scenes, str(output_path))
        else:
            video_service.assemble_reel(scenes, str(output_path))
        
        # Step 7: Finalize & History Logging (100%)
        update_task_progress(task_id, 95, "Logging reel to historical catalog")
        
        # Convert path objects to strings for JSON serialization
        serializable_scenes = []
        for s in scenes:
            scene_num = s["scene_number"]
            serializable_scenes.append({
                "scene_number": scene_num,
                "narration": s["narration"],
                "image_prompt": s["image_prompt"],
                "duration": s["duration"],
                "image_url": f"/static/generated/{task_id}/scene_{scene_num}.jpg"
            })
            
        reel_record = {
            "task_id": task_id,
            "title": sanitized_script["title"],
            "summary": sanitized_script["summary"],
            "scenes": serializable_scenes,
            "video_url": f"/videos/{task_id}.mp4",
            "audio_url": f"/download/audio/{task_id}",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        save_to_history(task_id, reel_record)
        
        # Success completion
        update_task_progress(
            task_id, 
            100, 
            "Video generation complete!", 
            status="completed", 
            result=reel_record
        )
        
    except Exception as e:
        print(f"Background thread error on task {task_id}: {e}")
        update_task_progress(task_id, 100, "Failed during processing", status="failed", error=str(e))
    finally:
        # Cleanup temporary audio files in upload/task_id to save server space
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as ce:
            print(f"Error cleaning up temp directory {temp_dir}: {ce}")

# API ENDPOINTS

@api_bp.route('/news/search', methods=['POST'])
def api_search_news():
    """
    Searches news articles based on a text query.
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"success": False, "error": "Query parameter is required"}), 400
        
    try:
        articles = news_service.search_news(query)
        return jsonify({"success": True, "articles": articles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/news/latest', methods=['GET'])
def api_latest_news():
    """
    Returns latest headlines for the headline picker.
    """
    topic = request.args.get("topic", "top stories").strip() or "top stories"

    try:
        articles = news_service.get_latest_news(topic)
        return jsonify({"success": True, "articles": articles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/news/extract', methods=['POST'])
def api_extract_article():
    """
    Extracts article text and title from a web URL.
    """
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    
    if not url:
        return jsonify({"success": False, "error": "URL parameter is required"}), 400
        
    try:
        res = article_parser.extract_article_text(url)
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/reel/generate', methods=['POST'])
def api_generate_reel():
    """
    Spawns a background thread to initiate video generation and returns a task ID.
    """
    data = request.get_json() or {}
    source_url = data.get("source_url", "").strip()
    search_query = data.get("search_query", "").strip()
    voice = data.get("voice", Config.DEFAULT_VOICE).strip()
    selected_article = data.get("selected_article")
    fast_mode = bool(data.get("fast_mode", True))
    if not isinstance(selected_article, dict):
        selected_article = None
    
    if not source_url and not search_query and not selected_article:
        return jsonify({"success": False, "error": "Provide source_url, search_query, or selected_article"}), 400
        
    task_id = str(uuid.uuid4())
    
    # Initialize in-memory active tasks
    update_task_progress(task_id, 0, "Enqueuing generation task")
    
    # Start thread
    thread = threading.Thread(
        target=background_generation_worker,
        args=(task_id, source_url, search_query, voice, selected_article, fast_mode)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "Generation started in the background."
    })

@api_bp.route('/reel/status/<task_id>', methods=['GET'])
def api_reel_status(task_id):
    """
    Returns progress percentage, current stage, results, or error messages for a task.
    """
    task = ACTIVE_TASKS.get(task_id)
    if not task:
        # Check if the video already exists in the completed history
        history_file = Config.OUTPUT_FOLDER / 'history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                if task_id in history:
                    return jsonify({
                        "success": True,
                        "status": "completed",
                        "progress": 100,
                        "stage": "Finished",
                        "error": None,
                        "result": history[task_id]
                    })
            except Exception as e:
                print(f"Error loading history during status poll: {e}")
                
        return jsonify({"success": False, "error": "Task not found"}), 404
        
    return jsonify({
        "success": True,
        "status": task["status"],
        "progress": task["progress"],
        "stage": task["stage"],
        "error": task["error"],
        "result": task["result"]
    })

@api_bp.route('/reel/history', methods=['GET'])
def api_reel_history():
    """
    Returns the complete list of previously generated reels.
    """
    history_file = Config.OUTPUT_FOLDER / 'history.json'
    if not history_file.exists():
        return jsonify({"success": True, "history": []})
        
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        # Convert dict to sorted list by creation date
        history_list = sorted(
            history.values(),
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        return jsonify({"success": True, "history": history_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
