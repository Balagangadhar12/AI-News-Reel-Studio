import requests
import random
from pathlib import Path
from urllib.parse import quote_plus
from PIL import Image, ImageDraw, ImageFont
from config import Config

def generate_image_for_prompt(prompt, output_path, width=1080, height=1920):
    """
    Generates an image for a given text prompt.
    Uses Pollinations.ai text-to-image API, and falls back to generating a beautiful
    local gradient card using PIL if it fails.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Try Pollinations.ai first
    try:
        # Add cinematic styling keywords
        styled_prompt = f"{prompt}, professional photography, volumetric lighting, detailed, 8k resolution, vertical composition"
        encoded_prompt = quote_plus(styled_prompt)
        seed = random.randint(1, 100000)
        
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            # Verify the image is valid
            with Image.open(output_path) as img:
                img.verify()
            return True
            
    except Exception as e:
        print(f"Pollinations.ai generation failed: {e}. Creating PIL fallback...")
        
    # Fallback: PIL Gradient and Title Drawing
    return create_gradient_placeholder(prompt, output_path, width, height)

def create_gradient_placeholder(prompt, output_path, width=1080, height=1920):
    """
    Generates a beautiful gradient background with overlay text as a fallback image.
    """
    try:
        # Create gradient image
        image = Image.new("RGB", (width, height), "#0f0f15")
        draw = ImageDraw.Draw(image)
        
        # Color definitions for gradient
        colors = [
            (15, 15, 21),       # Deep Space Dark
            (76, 29, 149),     # Neon Purple
            (12, 74, 96)        # Dark Cyan
        ]
        
        # Draw soft gradient vertical bands
        for y in range(height):
            # Interpolate colors based on height
            if y < height / 2:
                ratio = y / (height / 2)
                r = int(colors[0][0] + ratio * (colors[1][0] - colors[0][0]))
                g = int(colors[0][1] + ratio * (colors[1][1] - colors[0][1]))
                b = int(colors[0][2] + ratio * (colors[1][2] - colors[0][2]))
            else:
                ratio = (y - height / 2) / (height / 2)
                r = int(colors[1][0] + ratio * (colors[2][0] - colors[1][0]))
                g = int(colors[1][1] + ratio * (colors[2][1] - colors[1][1]))
                b = int(colors[1][2] + ratio * (colors[2][2] - colors[1][2]))
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        # Draw beautiful overlay circle glows
        draw.ellipse([(-200, -200), (600, 600)], fill=(124, 58, 237, 20), outline=None)
        draw.ellipse([(width-600, height-600), (width+200, height+200)], fill=(6, 182, 212, 20), outline=None)
        
        # Write text of prompt (wrapped) in center
        font_size = 40
        try:
            # Try to load a standard system font, otherwise default
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
            
        # Word wrap prompt
        words = prompt.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            # Roughly measure text size (using font.getbbox or fallback)
            test_line = " ".join(current_line)
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except AttributeError:
                line_width = len(test_line) * (font_size * 0.5)
                
            if line_width > width - 160:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        # Limit prompt display to 5 lines for aesthetics
        lines = lines[:5]
        
        # Draw "AI IMAGE FALLBACK" tag
        try:
            tag_font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            tag_font = ImageFont.load_default()
            
        draw.text((width/2, height/2 - 150), "AI STUDIO VISUAL", font=tag_font, fill="#a78bfa", anchor="mm")
        
        # Draw wrapped lines
        y_offset = height / 2 - 50
        for line in lines:
            draw.text((width/2, y_offset), line, font=font, fill="#f3f4f6", anchor="mm")
            y_offset += font_size + 15
            
        # Draw studio footer
        draw.text((width/2, height - 100), "AI News Reel Studio", font=tag_font, fill="#4b5563", anchor="mm")
        
        # Save placeholder
        image.save(output_path, "JPEG")
        return True
    except Exception as e:
        print(f"PIL fallback creation failed: {e}")
        # absolute bare minimum image creation
        img = Image.new("RGB", (width, height), color=(15, 15, 21))
        img.save(output_path, "JPEG")
        return True
