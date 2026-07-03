import sys
import os
import argparse
from pathlib import Path
from config import Config

# Add current workspace to path to resolve imports
sys.path.append(str(Path(__file__).resolve().parent))

def test_news():
    print("\n=== Testing News Service ===")
    from services.news_service import search_news
    query = "AI advances"
    print(f"Searching news for: '{query}'...")
    articles = search_news(query)
    print(f"Found {len(articles)} articles.")
    for idx, art in enumerate(articles[:3]):
        print(f"[{idx+1}] {art['title']} (Source: {art['source']})")
        print(f"    URL: {art['url']}")
    return len(articles) > 0

def test_parser():
    print("\n=== Testing Article Parser ===")
    from services.article_parser import extract_article_text
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(f"Scraping Wikipedia Artificial Intelligence page...")
    res = extract_article_text(test_url)
    if res["success"]:
        print(f"SUCCESS: Scraped Title: {res['title']}")
        print(f"First 200 chars: {res['text'][:200]}...")
        return True
    else:
        print(f"FAILED: {res['error']}")
        return False

def test_llm():
    print("\n=== Testing LLM Script Generation ===")
    from services.llm_service import generate_video_script
    title = "SpaceX Starship Prepares for Next Orbital Launch"
    text = "SpaceX is finalizing launch preparations for its massive Starship rocket. The team plans to test orbit capture systems and test outer shield thermal tiles. Regulatory permits are expected next week."
    print("Requesting script generation from Gemini (or Fallback)...")
    res = generate_video_script(title, text)
    if res["success"]:
        print("SUCCESS! Generated Title:", res["data"]["title"])
        print("Generated Summary:", res["data"]["summary"])
        print(f"Generated {len(res['data']['scenes'])} scenes:")
        for scene in res["data"]["scenes"]:
            print(f"  Scene {scene.get('scene_number')} ({scene.get('duration')}s): {scene.get('narration')[:60]}...")
        return True
    else:
        print("FAILED:", res["error"])
        return False

def test_tts():
    print("\n=== Testing Edge-TTS Service ===")
    from services.tts_service import generate_tts_file
    text = "Testing the expressive Edge-TTS neural voice synthesis in AI News Reel Studio."
    voice = Config.DEFAULT_VOICE
    output_path = Config.UPLOAD_FOLDER / "test_tts.mp3"
    print(f"Generating audio to {output_path}...")
    
    # Clean old file
    if output_path.exists():
        output_path.unlink()
        
    success = generate_tts_file(text, voice, str(output_path))
    if success and output_path.exists():
        print(f"SUCCESS! Created audio file (Size: {output_path.stat().st_size} bytes)")
        return True
    else:
        print("FAILED to create audio file.")
        return False

def test_image():
    print("\n=== Testing Image Service ===")
    from services.image_service import generate_image_for_prompt
    prompt = "Cinematic shot of a glowing blue server rack, futuristic database laboratory, detailed, 9:16 aspect ratio"
    output_path = Config.UPLOAD_FOLDER / "test_image.jpg"
    print(f"Generating image to {output_path}...")
    
    # Clean old file
    if output_path.exists():
        output_path.unlink()
        
    success = generate_image_for_prompt(prompt, str(output_path))
    if success and output_path.exists():
        print(f"SUCCESS! Created image file (Size: {output_path.stat().st_size} bytes)")
        return True
    else:
        print("FAILED to create image file.")
        return False

def test_video():
    print("\n=== Testing MoviePy Video Rendering ===")
    from services.tts_service import generate_tts_file
    from services.image_service import generate_image_for_prompt
    from services.video_service import assemble_reel
    
    test_run_dir = Config.UPLOAD_FOLDER / "test_run"
    test_run_dir.mkdir(parents=True, exist_ok=True)
    
    output_mp4 = Config.OUTPUT_FOLDER / "test_verify_reel.mp4"
    if output_mp4.exists():
        try:
            output_mp4.unlink()
        except Exception as e:
            print(f"Warning: could not delete existing file {output_mp4}: {e}")
            
    print("Preparing mock scenes assets...")
    scenes = [
        {
            "scene_number": 1,
            "narration": "Welcome to the test build. This is scene number one.",
            "image_prompt": "Futuristic coding background, soft neon colors, 9:16 aspect ratio",
            "image_path": str(test_run_dir / "scene_1.jpg"),
            "audio_path": str(test_run_dir / "scene_1.mp3")
        },
        {
            "scene_number": 2,
            "narration": "Our custom Pillow subtitles and MoviePy zoom transitions are working.",
            "image_prompt": "Modern server glowing, cyber pink accent, vertical 9:16 layout",
            "image_path": str(test_run_dir / "scene_2.jpg"),
            "audio_path": str(test_run_dir / "scene_2.mp3")
        }
    ]
    
    try:
        # Generate assets
        for s in scenes:
            print(f"Generating assets for Scene {s['scene_number']}...")
            generate_tts_file(s["narration"], Config.DEFAULT_VOICE, s["audio_path"])
            generate_image_for_prompt(s["image_prompt"], s["image_path"])
            
        print("Compiling video...")
        success = assemble_reel(scenes, str(output_mp4))
        
        if success and output_mp4.exists():
            print(f"\nSUCCESS! Rendered vertical verification MP4.")
            print(f"Output File: {output_mp4}")
            print(f"File Size: {output_mp4.stat().st_size} bytes")
            return True
        else:
            print("FAILED to compile MP4 output.")
            return False
            
    except Exception as e:
        print(f"Error during video compilation verification: {e}")
        return False
    finally:
        # Cleanup test run assets
        import shutil
        if test_run_dir.exists():
            try:
                shutil.rmtree(test_run_dir)
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="AI News Reel Studio - Service Test Suite")
    parser.add_argument("--news", action="store_true", help="Test news fetching service")
    parser.add_argument("--parser", action="store_true", help="Test BeautifulSoup scraper service")
    parser.add_argument("--llm", action="store_true", help="Test Gemini API service")
    parser.add_argument("--tts", action="store_true", help="Test Edge-TTS audio generator")
    parser.add_argument("--image", action="store_true", help="Test image generator")
    parser.add_argument("--video", action="store_true", help="Test MoviePy video assembly and subtitle overlay")
    parser.add_argument("--all", action="store_true", help="Test all services in sequence")
    
    args = parser.parse_args()
    
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)
        
    results = {}
    
    if args.news or args.all:
        results["news"] = test_news()
    if args.parser or args.all:
        results["parser"] = test_parser()
    if args.llm or args.all:
        results["llm"] = test_llm()
    if args.tts or args.all:
        results["tts"] = test_tts()
    if args.image or args.all:
        results["image"] = test_image()
    if args.video or args.all:
        results["video"] = test_video()
        
    print("\n=== Dry-Run Summary ===")
    all_passed = True
    for service, status in results.items():
        pass_fail = "PASSED" if status else "FAILED"
        print(f"Service '{service}': {pass_fail}")
        if not status:
            all_passed = False
            
    if all_passed:
        print("\nAll systems operational!")
        sys.exit(0)
    else:
        print("\nSome services failed. Check logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
