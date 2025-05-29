#!/usr/bin/env python3
"""
Resize images in the images/ folder to create smaller versions for PDF integration.
Creates resized versions in images/small/ folder.
"""

import os
from PIL import Image
import glob

# Create the small images directory
input_dir = "/media/data/share/repos/materiatek/materials-library-extraction/workflow_review/images"
output_dir = "/media/data/share/repos/materiatek/materials-library-extraction/workflow_review/images/small"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Target dimensions and quality
MAX_WIDTH = 800
MAX_HEIGHT = 600
QUALITY = 85  # JPEG quality (1-100)

def resize_image(input_path, output_path):
    """Resize an image while maintaining aspect ratio"""
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate new dimensions while maintaining aspect ratio
            width, height = img.size
            aspect_ratio = width / height
            
            if width > MAX_WIDTH or height > MAX_HEIGHT:
                if aspect_ratio > 1:  # Landscape
                    new_width = min(MAX_WIDTH, width)
                    new_height = int(new_width / aspect_ratio)
                else:  # Portrait
                    new_height = min(MAX_HEIGHT, height)
                    new_width = int(new_height * aspect_ratio)
                
                # Ensure we don't exceed max dimensions
                if new_height > MAX_HEIGHT:
                    new_height = MAX_HEIGHT
                    new_width = int(new_height * aspect_ratio)
                if new_width > MAX_WIDTH:
                    new_width = MAX_WIDTH
                    new_height = int(new_width / aspect_ratio)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as JPEG with specified quality
            img.save(output_path, 'JPEG', quality=QUALITY, optimize=True)
            
            # Get file size
            file_size = os.path.getsize(output_path)
            print(f"✓ {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            print(f"  Size: {file_size // 1024}KB, Dimensions: {img.size[0]}x{img.size[1]}")
            
            return True
            
    except Exception as e:
        print(f"✗ Error processing {input_path}: {str(e)}")
        return False

def main():
    # Find all PNG files in the input directory
    png_files = glob.glob(os.path.join(input_dir, "*.png"))
    
    if not png_files:
        print("No PNG files found in the images directory")
        return
    
    print(f"Found {len(png_files)} images to resize")
    print(f"Output directory: {output_dir}")
    print(f"Target max dimensions: {MAX_WIDTH}x{MAX_HEIGHT}")
    print(f"JPEG quality: {QUALITY}")
    print("-" * 50)
    
    successful = 0
    for png_file in png_files:
        # Create output filename (change extension to .jpg)
        base_name = os.path.splitext(os.path.basename(png_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}.jpg")
        
        if resize_image(png_file, output_file):
            successful += 1
        print()
    
    print("-" * 50)
    print(f"Successfully resized {successful}/{len(png_files)} images")
    print(f"Resized images saved to: {output_dir}")

if __name__ == "__main__":
    main()
