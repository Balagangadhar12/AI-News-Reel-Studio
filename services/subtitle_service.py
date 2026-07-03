import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config import Config

def add_subtitles_to_clip(clip, text):
    """
    Overlays stylized subtitles onto a MoviePy video clip frame-by-frame.
    This ensures that subtitles do not zoom or distort during panning/zooming animations.
    """
    if not text:
        return clip
        
    def overlay_subtitle(frame):
        # MoviePy frames are RGB numpy arrays
        pil_img = Image.fromarray(frame)
        width, height = pil_img.size
        
        # Create an overlay layer for transparency (alpha blending)
        overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        font_size = 50
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
            
        # Word wrap text to fit within the lower third width (with padding)
        max_text_width = width - 180
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except AttributeError:
                line_width = len(test_line) * (font_size * 0.5)
                
            if line_width > max_text_width:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        # Calculate bounding box for the capsule background
        line_heights = []
        line_widths = []
        for line in lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                line_widths.append(w)
                line_heights.append(h)
            except AttributeError:
                line_widths.append(len(line) * (font_size * 0.5))
                line_heights.append(font_size)
                
        total_text_height = sum(line_heights) + (len(lines) - 1) * 15
        max_line_width = max(line_widths) if line_widths else 0
        
        # Center coordinates
        capsule_width = max_line_width + 60
        capsule_height = total_text_height + 40
        
        # Position in lower third of the video
        y_center = int(height * 0.78)
        x_center = int(width / 2)
        
        left = x_center - int(capsule_width / 2)
        top = y_center - int(capsule_height / 2)
        right = x_center + int(capsule_width / 2)
        bottom = y_center + int(capsule_height / 2)
        
        # Draw background rounded rectangle capsule (semi-transparent black)
        # Pillow >= 9.0 supports rounded_rectangle with radius
        try:
            draw.rounded_rectangle(
                [(left, top), (right, bottom)], 
                radius=15, 
                fill=(0, 0, 0, 160)
            )
        except AttributeError:
            draw.rectangle(
                [(left, top), (right, bottom)], 
                fill=(0, 0, 0, 160)
            )
            
        # Composite text on top of capsule
        y_offset = top + 20
        for line in lines:
            # Draw dropshadow for extra legibility
            draw.text((x_center + 2, y_offset + 2), line, font=font, fill=(0, 0, 0, 200), anchor="mm")
            # Draw yellow text for high contrast modern reel feel
            draw.text((x_center, y_offset), line, font=font, fill="#facc15", anchor="mm")
            y_offset += font_size + 15
            
        # Merge overlay back with original frame
        merged_img = Image.alpha_composite(pil_img.convert("RGBA"), overlay)
        return np.array(merged_img.convert("RGB"))
        
    # Use MoviePy's image transform filter
    return clip.image_transform(overlay_subtitle)
