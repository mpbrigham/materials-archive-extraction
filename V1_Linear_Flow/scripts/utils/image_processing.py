#!/usr/bin/env python3
"""
IMIS V1.5 - Image Processing Utilities
Provides PDF pagination and image cropping functionality
"""

import os
import logging
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('imis_image_processor')

try:
    # Attempt to import pdf2image (requires poppler)
    from pdf2image import convert_from_path
    from PIL import Image
    DEPS_INSTALLED = True
except ImportError:
    logger.warning("Required dependencies not installed. Please install with: pip install pdf2image pillow")
    DEPS_INSTALLED = False

# Define types for type hinting
BoundingBox = Tuple[int, int, int, int]  # [x1, y1, x2, y2]
ImageInfo = Dict[str, Any]  # Will contain path, dimensions, etc.


def validate_environment() -> bool:
    """Ensure all required dependencies are available"""
    if not DEPS_INSTALLED:
        logger.error("Missing required dependencies. Install with: pip install pdf2image pillow")
        return False
    
    try:
        # Test PDF conversion capability
        test_image = convert_from_path(
            pdf_path="placeholder", 
            dpi=100, 
            first_page=1, 
            last_page=1,
            use_pdftocairo=True,
            size=(100, 100)
        )
        return True
    except Exception as e:
        if "placeholder" in str(e):
            # Expected error for placeholder file, but converter loaded
            return True
        logger.error(f"PDF conversion error: {str(e)}")
        logger.error("Ensure poppler-utils is installed on your system")
        return False


def paginate_pdf(
    pdf_path: str, 
    output_dir: str, 
    dpi: int = 300,
    prefix: Optional[str] = None
) -> List[ImageInfo]:
    """
    Convert a PDF to a sequence of page images
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save page images
        dpi: Resolution for image conversion
        prefix: Optional filename prefix
    
    Returns:
        List of image info dictionaries with paths and metadata
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return []
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Generate a unique ID for this document's images
    doc_id = prefix or uuid.uuid4().hex[:8]
    
    try:
        # Convert PDF to images
        logger.info(f"Converting PDF: {pdf_path}")
        images = convert_from_path(
            pdf_path=pdf_path,
            dpi=dpi,
            output_folder=output_dir,
            fmt="jpg",
            output_file=f"{doc_id}_page",
            thread_count=4,
            use_pdftocairo=True,
            paths_only=False
        )
        
        # Create image info for each page
        image_info_list = []
        for i, img in enumerate(images):
            # Save image if not already saved
            img_path = os.path.join(output_dir, f"{doc_id}_page_{i+1}.jpg")
            if not os.path.exists(img_path):
                img.save(img_path, "JPEG")
            
            # Store image metadata
            width, height = img.size
            image_info_list.append({
                "page": i + 1,
                "path": img_path,
                "width": width,
                "height": height,
                "dpi": dpi,
                "format": "jpg"
            })
            
            logger.info(f"Processed page {i+1}: {img_path}")
        
        return image_info_list
    
    except Exception as e:
        logger.error(f"Error paginating PDF: {str(e)}")
        return []


def crop_image(
    image_path: str,
    bbox: BoundingBox,
    output_dir: str,
    padding: int = 10
) -> Optional[str]:
    """
    Crop a region from an image based on bounding box coordinates
    
    Args:
        image_path: Path to the source image
        bbox: Tuple of coordinates [x1, y1, x2, y2]
        output_dir: Directory to save cropped image
        padding: Padding to add around the crop (pixels)
    
    Returns:
        Path to the cropped image, or None if failed
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Extract coordinates
            x1, y1, x2, y2 = bbox
            
            # Add padding (ensuring within image bounds)
            width, height = img.size
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)
            
            # Perform the crop
            crop = img.crop((x1, y1, x2, y2))
            
            # Save the cropped image
            base_name = Path(image_path).stem
            crop_name = f"{base_name}_crop_{x1}_{y1}_{x2}_{y2}.jpg"
            crop_path = os.path.join(output_dir, crop_name)
            crop.save(crop_path, "JPEG")
            
            logger.info(f"Cropped image saved to: {crop_path}")
            return crop_path
    
    except Exception as e:
        logger.error(f"Error cropping image: {str(e)}")
        return None


def images_to_base64(image_paths: List[str]) -> List[Dict[str, str]]:
    """
    Convert images to base64 for API requests
    
    Args:
        image_paths: List of paths to images
        
    Returns:
        List of dictionaries with base64-encoded images
    """
    import base64
    
    encoded_images = []
    for path in image_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    
                    encoded_images.append({
                        "path": path,
                        "base64": encoded,
                        "mime_type": "image/jpeg"
                    })
            except Exception as e:
                logger.error(f"Error encoding image {path}: {str(e)}")
    
    return encoded_images


# Command line interface for testing
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF Image Processing Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Paginate command
    paginate_parser = subparsers.add_parser("paginate", help="Convert PDF to page images")
    paginate_parser.add_argument("pdf_path", help="Path to PDF file")
    paginate_parser.add_argument("--output", default="./output", help="Output directory")
    paginate_parser.add_argument("--dpi", type=int, default=300, help="Image resolution (DPI)")
    
    # Crop command
    crop_parser = subparsers.add_parser("crop", help="Crop region from image")
    crop_parser.add_argument("image_path", help="Path to image file")
    crop_parser.add_argument("bbox", help="Bounding box (x1,y1,x2,y2)")
    crop_parser.add_argument("--output", default="./output", help="Output directory")
    crop_parser.add_argument("--padding", type=int, default=10, help="Padding in pixels")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "paginate":
        result = paginate_pdf(args.pdf_path, args.output, args.dpi)
        print(f"Generated {len(result)} page images:")
        for img in result:
            print(f"  Page {img['page']}: {img['path']}")
    
    elif args.command == "crop":
        try:
            bbox = [int(x) for x in args.bbox.split(",")]
            if len(bbox) != 4:
                raise ValueError("Bounding box must have 4 values")
            
            result = crop_image(args.image_path, tuple(bbox), args.output, args.padding)
            print(f"Cropped image: {result}")
        
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    else:
        parser.print_help()