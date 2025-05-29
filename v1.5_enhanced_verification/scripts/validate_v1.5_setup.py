#!/usr/bin/env python3
"""
IMIS V1.5 - Enhanced Visual Verification Setup Validator
Validates that all required dependencies and configurations for V1.5 are properly set up
"""

import os
import sys
import json
import shutil
import logging
import tempfile
import platform
import subprocess
import requests
from pathlib import Path
from argparse import ArgumentParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('v1.5_validation.log')
    ]
)
logger = logging.getLogger('v1.5_validator')

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def check_system_dependencies():
    """Verify system dependencies required for V1.5"""
    logger.info("Checking system dependencies...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        raise ValidationError(f"Python 3.8+ is required, found: {sys.version}")
    logger.info(f"✓ Python version: {sys.version}")
    
    # Check poppler for PDF processing
    system = platform.system()
    if system == "Windows":
        poppler_binaries = ["pdfinfo.exe", "pdftoppm.exe"]
    else:
        poppler_binaries = ["pdfinfo", "pdftoppm"]
    
    missing_binaries = []
    for binary in poppler_binaries:
        binary_path = shutil.which(binary)
        if binary_path:
            logger.info(f"✓ Found {binary} at {binary_path}")
            try:
                version_output = subprocess.check_output(
                    [binary_path, "-v"], 
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                logger.info(f"  Version info: {version_output.strip().split('\\n')[0]}")
            except subprocess.SubprocessError as e:
                missing_binaries.append(binary)
                logger.error(f"✗ Error running {binary}: {str(e)}")
        else:
            missing_binaries.append(binary)
            logger.error(f"✗ Missing {binary} - required for PDF processing")
    
    if missing_binaries:
        if system == "Linux":
            logger.error("Install poppler-utils with: sudo apt-get install poppler-utils")
        elif system == "Darwin":  # macOS
            logger.error("Install poppler with: brew install poppler")
        elif system == "Windows":
            logger.error("Download poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases")
        raise ValidationError(f"Missing required poppler binaries: {', '.join(missing_binaries)}")

def check_python_packages():
    """Verify Python packages required for V1.5"""
    logger.info("Checking Python packages...")
    
    required_packages = {
        'flask': 'Web server for webhook handler',
        'requests': 'HTTP client for API communication',
        'python-dotenv': 'Environment variable management',
        'werkzeug': 'Utilities for web applications',
        'pdf2image': 'PDF to image conversion (requires poppler)',
        'pillow': 'Image processing library'
    }
    
    missing_packages = []
    for package, description in required_packages.items():
        try:
            module = __import__(package)
            logger.info(f"✓ {package}: {description}")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ Missing {package}: {description}")
    
    if missing_packages:
        install_cmd = f"pip install {' '.join(missing_packages)}"
        logger.error(f"Install missing packages with: {install_cmd}")
        raise ValidationError(f"Missing required Python packages: {', '.join(missing_packages)}")

def check_directory_structure():
    """Verify the directory structure required for V1.5"""
    logger.info("Checking directory structure...")
    
    # Define required directories
    required_dirs = [
        "./storage",
        "./storage/pages",
        "./storage/crops",
        "./logs"
    ]
    
    # Check each directory
    missing_dirs = []
    permission_issues = []
    
    for dir_path in required_dirs:
        dir_obj = Path(dir_path)
        if not dir_obj.exists():
            missing_dirs.append(dir_path)
            logger.error(f"✗ Directory missing: {dir_path}")
        elif not os.access(dir_path, os.W_OK):
            permission_issues.append(dir_path)
            logger.error(f"✗ Cannot write to directory: {dir_path}")
        else:
            logger.info(f"✓ Directory exists and is writable: {dir_path}")
    
    if missing_dirs:
        logger.error("Create missing directories with:")
        logger.error("mkdir -p storage/pages storage/crops logs")
        logger.error("chmod 755 storage logs storage/pages storage/crops")
    
    if permission_issues:
        logger.error("Fix permissions with:")
        logger.error(f"chmod 755 {' '.join(permission_issues)}")
    
    if missing_dirs or permission_issues:
        raise ValidationError("Directory structure issues detected")

def check_image_processing():
    """Test the image processing capabilities required for V1.5"""
    logger.info("Testing image processing capabilities...")
    
    try:
        # Check pdf2image functionality
        from pdf2image import convert_from_path
        from PIL import Image
        
        logger.info("✓ pdf2image and PIL modules imported successfully")
        
        # Look for a sample PDF to test with
        sample_pdf = None
        sample_locations = [
            Path("./samples").glob("*.pdf"),
            Path("../samples").glob("*.pdf"),
            Path("../../samples").glob("*.pdf"),
        ]
        
        for location in sample_locations:
            for pdf_file in location:
                sample_pdf = pdf_file
                logger.info(f"Found sample PDF for testing: {sample_pdf}")
                break
            if sample_pdf:
                break
        
        if not sample_pdf:
            logger.warning("No sample PDF found. Using test PDF or skipping conversion test.")
            return
        
        # Set up test directories
        test_dir = Path(tempfile.mkdtemp())
        test_pages_dir = test_dir / "pages"
        test_crops_dir = test_dir / "crops"
        test_pages_dir.mkdir(exist_ok=True)
        test_crops_dir.mkdir(exist_ok=True)
        
        # Test PDF to image conversion
        logger.info(f"Converting {sample_pdf} to images...")
        try:
            images = convert_from_path(
                pdf_path=str(sample_pdf),
                output_folder=str(test_pages_dir),
                fmt="jpg",
                dpi=150,
                first_page=1,
                last_page=1
            )
            
            if not images:
                raise ValidationError("PDF conversion produced no images")
                
            logger.info(f"✓ Successfully converted PDF to {len(images)} image(s)")
            
            # Test image cropping
            if images and len(images) > 0:
                test_image = images[0]
                width, height = test_image.size
                
                # Define a test crop (center of the image)
                crop_x1 = width // 4
                crop_y1 = height // 4
                crop_x2 = width * 3 // 4
                crop_y2 = height * 3 // 4
                
                crop = test_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                crop_path = test_crops_dir / "test_crop.jpg"
                crop.save(crop_path)
                
                logger.info(f"✓ Successfully created test crop at {crop_path}")
                logger.info(f"  Original size: {width}x{height}, Crop size: {crop.width}x{crop.height}")
        except Exception as e:
            raise ValidationError(f"PDF/image processing test failed: {str(e)}")
        finally:
            # Clean up test directories
            import shutil
            shutil.rmtree(test_dir)
            
    except Exception as e:
        raise ValidationError(f"Image processing test failed: {str(e)}")

def check_environment_variables():
    """Check if required environment variables are set"""
    logger.info("Checking environment variables...")
    
    # Load environment variables from .env if present
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("✓ Loaded environment variables from .env file")
        except ImportError:
            logger.warning("python-dotenv not installed, skipping .env file loading")
    
    # Required environment variables for V1.5
    required_vars = [
        # Storage paths
        "STORAGE_PATH",
        # LLM Vision API settings
        "LLM_VISION_API_ENDPOINT",
        "LLM_VISION_MODEL",
        # Image processing settings
        "PDF_DPI",
        "CROP_PADDING",
        "IMAGE_FORMAT",
        "IMAGE_QUALITY"
    ]
    
    # Optional but recommended
    recommended_vars = [
        "VISION_BATCH_SIZE",
        "ENABLE_CROP_CACHE"
    ]
    
    # Check required variables
    missing_vars = []
    for var in required_vars:
        if var not in os.environ:
            missing_vars.append(var)
            logger.error(f"✗ Missing required environment variable: {var}")
        else:
            logger.info(f"✓ Found environment variable: {var}")
    
    # Check recommended variables
    missing_recommended = []
    for var in recommended_vars:
        if var not in os.environ:
            missing_recommended.append(var)
            logger.warning(f"! Recommended environment variable not set: {var}")
        else:
            logger.info(f"✓ Found recommended environment variable: {var}")
    
    if missing_vars:
        logger.error("Please set required environment variables in .env file")
        env_template = Path("deployment/env-template.txt")
        if env_template.exists():
            logger.error(f"Use template at {env_template} as reference")
    
    if missing_recommended:
        logger.warning("Consider setting recommended variables for optimal performance")
    
    if missing_vars:
        raise ValidationError(f"Missing required environment variables: {', '.join(missing_vars)}")

def check_n8n_workflow():
    """Check if n8n workflow file exists and has required nodes"""
    logger.info("Checking n8n workflow file...")
    
    workflow_file = Path("deployment/workflow_Materials_Intake_V1.5.json")
    if not workflow_file.exists():
        logger.error(f"✗ Missing n8n workflow file: {workflow_file}")
        raise ValidationError(f"Missing n8n workflow file: {workflow_file}")
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        # Check for required nodes
        required_nodes = [
            "PDF Paginator", 
            "Enhanced Extractor", 
            "Image Cropper",
            "Schema Validator"
        ]
        
        found_nodes = []
        if 'nodes' in workflow:
            for node in workflow['nodes']:
                if 'name' in node and any(req in node['name'] for req in required_nodes):
                    found_nodes.append(node['name'])
        
        missing_nodes = [node for node in required_nodes if not any(node in found for found in found_nodes)]
        
        if missing_nodes:
            logger.error(f"✗ Workflow file missing required nodes: {', '.join(missing_nodes)}")
            raise ValidationError(f"n8n workflow missing required nodes: {', '.join(missing_nodes)}")
        else:
            logger.info(f"✓ Workflow file contains all required nodes")
            
    except json.JSONDecodeError:
        logger.error(f"✗ Invalid JSON in workflow file: {workflow_file}")
        raise ValidationError(f"Invalid JSON in workflow file: {workflow_file}")
    except Exception as e:
        logger.error(f"✗ Error checking workflow file: {str(e)}")
        raise ValidationError(f"Error checking workflow file: {str(e)}")

def check_webhook_handler():
    """Check if webhook handler is functioning correctly"""
    logger.info("Checking webhook handler...")
    
    # Check if webhook_handler.py exists
    webhook_file = Path("scripts/webhook_handler.py")
    if not webhook_file.exists():
        logger.error(f"✗ Missing webhook handler file: {webhook_file}")
        raise ValidationError(f"Missing webhook handler file: {webhook_file}")
    
    logger.info(f"✓ Found webhook handler file: {webhook_file}")
    
    # Try to ping the webhook if it's running
    try:
        webhook_url = os.environ.get("WEBHOOK_URL", "http://localhost:5000")
        health_url = f"{webhook_url}/health"
        
        logger.info(f"Attempting to connect to webhook health endpoint: {health_url}")
        response = requests.get(health_url, timeout=2)
        
        if response.status_code == 200:
            logger.info(f"✓ Webhook handler is running and healthy: {response.json()}")
        else:
            logger.warning(f"! Webhook returned status {response.status_code}: {response.text}")
            logger.warning("Webhook may not be running or has issues")
    except requests.RequestException:
        logger.warning("! Could not connect to webhook handler - it may not be running")
        logger.info("  Start webhook with: python scripts/webhook_handler.py")

def check_prompt_files():
    """Verify that all required prompt files exist"""
    logger.info("Checking prompt files...")
    
    required_prompts = [
        "enhanced_extractor_initial.txt",
        "enhanced_extractor_verification.txt",
    ]
    
    prompts_dir = Path("prompts")
    missing_prompts = []
    
    for prompt_file in required_prompts:
        prompt_path = prompts_dir / prompt_file
        if not prompt_path.exists():
            missing_prompts.append(prompt_file)
            logger.error(f"✗ Missing required prompt file: {prompt_path}")
        else:
            logger.info(f"✓ Found prompt file: {prompt_path}")
    
    if missing_prompts:
        raise ValidationError(f"Missing required prompt files: {', '.join(missing_prompts)}")

def main():
    """Main validation function"""
    parser = ArgumentParser(description="Validate IMIS V1.5 Enhanced Visual Verification setup")
    parser.add_argument("--skip-api-check", action="store_true", 
                        help="Skip checks that require API connectivity")
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("Starting IMIS V1.5 Enhanced Visual Verification validation")
    logger.info("=" * 70)
    
    # Define validation checks
    checks = [
        ("System Dependencies", check_system_dependencies),
        ("Python Packages", check_python_packages),
        ("Directory Structure", check_directory_structure),
        ("Image Processing", check_image_processing),
        ("Environment Variables", check_environment_variables),
        ("n8n Workflow", check_n8n_workflow),
        ("Prompt Files", check_prompt_files),
    ]
    
    # Add webhook check if not skipping API checks
    if not args.skip_api_check:
        checks.append(("Webhook Handler", check_webhook_handler))
    
    # Run validation checks
    success_count = 0
    failures = []
    
    for name, check_func in checks:
        logger.info("\n" + "=" * 50)
        logger.info(f"Checking {name}...")
        logger.info("-" * 50)
        
        try:
            check_func()
            success_count += 1
            logger.info(f"✓ {name} check passed")
        except ValidationError as e:
            logger.error(f"✗ {name} check failed: {str(e)}")
            failures.append(f"{name}: {str(e)}")
        except Exception as e:
            logger.error(f"✗ {name} check failed with unexpected error: {str(e)}")
            failures.append(f"{name}: Unexpected error - {str(e)}")
    
    # Summarize results
    logger.info("\n" + "=" * 70)
    logger.info(f"Validation complete: {success_count}/{len(checks)} checks passed")
    
    if failures:
        logger.error("\nFailures detected:")
        for i, failure in enumerate(failures, 1):
            logger.error(f"{i}. {failure}")
        logger.error("\nPlease address these issues before deploying to production.")
        return 1
    else:
        logger.info("\n🎉 All validation checks passed! V1.5 is ready for production.")
        logger.info("Next steps:")
        logger.info("1. Start the webhook handler: python scripts/webhook_handler.py")
        logger.info("2. Import the workflow into n8n: n8n import:workflow --input=deployment/workflow_Materials_Intake_V1.5.json")
        logger.info("3. Run the testing script: python scripts/testing_script.py")
        logger.info("=" * 70)
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nValidation interrupted.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        sys.exit(1)