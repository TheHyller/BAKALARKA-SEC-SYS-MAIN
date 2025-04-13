import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_security_logo():
    """Create a simple security system logo"""
    # Define dimensions for the logo
    width, height = 300, 300
    
    # Create a new image with white background
    image = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Define colors
    blue = (41, 128, 185, 255)  # Nice blue color
    dark_blue = (52, 73, 94, 255)  # Dark blue for text
    
    # Draw a shield shape
    shield_points = [
        (width//2, height//10),  # Top point
        (width*9//10, height//4),  # Top right
        (width*4//5, height*4//5),  # Bottom right
        (width//2, height*9//10),  # Bottom point
        (width//5, height*4//5),  # Bottom left
        (width//10, height//4),  # Top left
    ]
    draw.polygon(shield_points, fill=blue)
    
    # Draw a house silhouette in the middle
    house_width = width // 2
    house_height = height // 2
    house_top = height // 3
    house_left = (width - house_width) // 2
    
    # Draw the house roof
    roof_points = [
        (house_left, house_top + house_height//2),  # Left point
        (house_left + house_width//2, house_top),  # Top point
        (house_left + house_width, house_top + house_height//2),  # Right point
    ]
    draw.polygon(roof_points, fill=(255, 255, 255, 220))
    
    # Draw the house body
    house_body = [
        (house_left + house_width//5, house_top + house_height//2),  # Top left
        (house_left + house_width*4//5, house_top + house_height//2),  # Top right
        (house_left + house_width*4//5, house_top + house_height),  # Bottom right
        (house_left + house_width//5, house_top + house_height),  # Bottom left
    ]
    draw.polygon(house_body, fill=(255, 255, 255, 220))
    
    # Draw a door
    door_width = house_width // 5
    door_height = house_height // 3
    door_left = house_left + (house_width - door_width) // 2
    door_top = house_top + house_height - door_height
    
    draw.rectangle(
        [(door_left, door_top), (door_left + door_width, house_top + house_height)],
        fill=(52, 73, 94, 200)
    )
    
    # Try to add text if font is available
    try:
        # Add text "SECURITY" at the bottom
        font_size = width // 10
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            # Use default font if specific font not available
            font = ImageFont.load_default()
            
        text = "SECURITY"
        text_width = draw.textlength(text, font=font)
        text_position = ((width - text_width) // 2, height * 6 // 7)
        draw.text(text_position, text, font=font, fill=dark_blue)
    except Exception as e:
        print(f"Could not add text to logo: {e}")
    
    # Save the image
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    logo_path = os.path.join(assets_dir, "security_logo.png")
    image.save(logo_path)
    print(f"Logo created and saved to {logo_path}")
    return logo_path

if __name__ == "__main__":
    create_security_logo()