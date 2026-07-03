import os
from pathlib import Path
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from services.subtitle_service import add_subtitles_to_clip
from config import Config

def assemble_reel(scenes_data, output_video_path):
    """
    Stitches generated images and TTS audio clips into a final vertical video.
    Applies zoom effects, transitions, and overlays subtitles.
    
    scenes_data: List of dicts, each containing:
                 - 'image_path': Path to scene image
                 - 'audio_path': Path to scene narration audio
                 - 'narration': Subtitle text
    output_video_path: Absolute path to export the final MP4
    """
    # Ensure output directory exists
    Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)
    
    clips = []
    
    try:
        for idx, scene in enumerate(scenes_data):
            img_path = scene['image_path']
            audio_path = scene['audio_path']
            narration = scene['narration']
            
            if not os.path.exists(img_path) or not os.path.exists(audio_path):
                print(f"Skipping scene {idx+1} due to missing assets: Image={img_path}, Audio={audio_path}")
                continue
                
            # Load audio to get its exact duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create image clip matching the audio duration
            img_clip = ImageClip(img_path).with_duration(duration)
            
            # Apply Ken Burns zoom effect (zoom in slightly over the clip duration)
            # We scale from 1.0 to 1.10
            # Note: lambda t: 1.0 + (0.10 * (t / duration))
            img_clip = img_clip.resized(lambda t, dur=duration: 1.0 + (0.08 * (t / dur)))
            
            # Set the audio on the image clip
            img_clip = img_clip.with_audio(audio_clip)
            
            # Apply subtitles
            img_clip = add_subtitles_to_clip(img_clip, narration)
            
            # Apply subtle fade in/out transitions using MoviePy 2.x vfx
            from moviepy import vfx
            img_clip = img_clip.with_effects([vfx.FadeIn(0.3), vfx.FadeOut(0.3)])
            
            clips.append(img_clip)
            
        if not clips:
            raise ValueError("No valid scene clips could be assembled.")
            
        # Concatenate all scene clips
        print(f"Concatenating {len(clips)} scene clips...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Write final video file
        # We specify libx264 and aac for maximum web compatability
        print(f"Rendering final video to {output_video_path}...")
        final_clip.write_videofile(
            output_video_path,
            fps=Config.FPS,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(os.path.dirname(output_video_path), "temp-audio.m4a"),
            remove_temp=True,
            logger=None # Suppress verbose progress console dumps
        )
        
        # Explicitly close all sub-clips to free resources and file locks
        final_clip.close()
        for c in clips:
            c.close()
            
        return True
        
    except Exception as e:
        print(f"Error assembling video reel: {e}")
        # Make sure to close clips in case of error
        for c in clips:
            try:
                c.close()
            except:
                pass
        raise e

def assemble_basic_reel(scenes_data, output_video_path):
    """
    Builds a very fast vertical reel from local image cards.
    It attaches available TTS audio but skips slow subtitles and zoom effects.
    """
    Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)

    clips = []

    try:
        for idx, scene in enumerate(scenes_data):
            img_path = scene["image_path"]
            audio_path = scene.get("audio_path", "")
            if not os.path.exists(img_path):
                print(f"Skipping scene {idx+1} due to missing image: {img_path}")
                continue

            duration = float(scene.get("duration", 3.0))
            audio_clip = None
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration

            clip = ImageClip(img_path).with_duration(duration)
            if audio_clip:
                clip = clip.with_audio(audio_clip)

            clips.append(clip)

        if not clips:
            raise ValueError("No valid scene images could be assembled.")

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            output_video_path,
            fps=12,
            codec="libx264",
            audio=any(getattr(clip, "audio", None) for clip in clips),
            audio_codec="aac",
            preset="ultrafast",
            ffmpeg_params=["-crf", "28"],
            logger=None
        )

        final_clip.close()
        for clip in clips:
            clip.close()

        return True
    except Exception as e:
        print(f"Error assembling basic reel: {e}")
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        raise e
