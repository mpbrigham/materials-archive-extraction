#!/usr/bin/env python3
"""
IMIS V1 - Dependency Validation Script
Validates that all required dependencies are properly installed and configured
"""

import os
import sys
import shutil
import logging
import tempfile
import platform
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dependency_validator')

def check_python_version():
    """Check that Python version meets requirements"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"Python 3.8+ is required. Current version: {sys.version}")
        return False
    logger.info(f"Python version: {sys.version}")
    return True

def check_python_packages():
    """Check required Python packages are installed"""
    required_packages = [
        'flask', 'requests', 'python-dotenv', 'werkzeug', 
        'pdf2image', 'pillow'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is not installed")
    
    if missing_packages:
        install_cmd = f"pip install {' '.join(missing_packages)}"
        logger.error(f"Missing packages. Install with: {install_cmd}")
        return False
    return True

def check_poppler_installation():
    """Check that poppler-utils are installed and in PATH"""
    system = platform.system()
    if system == "Windows":
        poppler_binaries = ["pdfinfo.exe", "pdftoppm.exe"]
    else:
        poppler_binaries = ["pdfinfo", "pdftoppm"]
    
    all_found = True
    for binary in poppler_binaries:
        binary_path = shutil.which(binary)
        if binary_path:
            logger.info(f"✅ Found {binary} at {binary_path}")
            try:
                # Try to run the binary to confirm it works
                version_output = subprocess.check_output(
                    [binary_path, "-v"], 
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                logger.info(f"  Version info: {version_output.strip().split('\\n')[0]}")
            except subprocess.SubprocessError as e:
                logger.error(f"❌ Error running {binary}: {str(e)}")
                all_found = False
        else:
            logger.error(f"❌ Could not find {binary} in PATH")
            all_found = False
    
    if not all_found:
        if system == "Linux":
            logger.error("Install poppler-utils with: sudo apt-get install poppler-utils")
        elif system == "Darwin":  # macOS
            logger.error("Install poppler with: brew install poppler")
        elif system == "Windows":
            logger.error("Download poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases")
            logger.error("Add the bin directory to your PATH environment variable")
        return False
    return True

def test_pdf_processing():
    """Test PDF processing capabilities"""
    try:
        from pdf2image import convert_from_path
        from PIL import Image
        
        # Create a simple test PDF file
        test_pdf = Path(tempfile.gettempdir()) / "test_poppler.pdf"
        output_dir = Path(tempfile.gettempdir()) / "test_poppler_output"
        output_dir.mkdir(exist_ok=True)
        
        # Try to find a sample PDF
        sample_found = False
        sample_locations = [
            Path("./samples").glob("*.pdf"),
            Path("../samples").glob("*.pdf"),
            Path("../../samples").glob("*.pdf"),
        ]
        
        for location in sample_locations:
            for sample in location:
                test_pdf = sample
                sample_found = True
                logger.info(f"Using sample PDF: {test_pdf}")
                break
            if sample_found:
                break
        
        if not sample_found:
            logger.warning("No sample PDF found. Will skip PDF conversion test.")
            return True
            
        # Test conversion
        logger.info(f"Testing PDF conversion with: {test_pdf}")
        images = convert_from_path(
            pdf_path=str(test_pdf),
            output_folder=str(output_dir),
            fmt="jpg",
            output_file="test_page",
            first_page=1,
            last_page=1
        )
        
        if images:
            logger.info(f"✅ Successfully converted PDF to {len(images)} image(s)")
            logger.info(f"  First image size: {images[0].size}")
            
            # Clean up
            for f in output_dir.glob("test_page*.jpg"):
                f.unlink()
            return True
        else:
            logger.error("❌ PDF conversion returned no images")
            return False
    
    except Exception as e:
        logger.error(f"❌ PDF processing test failed: {str(e)}")
        return False

def check_required_directories():
    """Check if required directories exist and have proper permissions"""
    required_dirs = [
        "./storage",
        "./storage/pages",
        "./storage/crops",
        "./logs"
    ]
    
    all_valid = True
    for dir_path in required_dirs:
        dir_obj = Path(dir_path)
        if not dir_obj.exists():
            logger.error(f"❌ Directory does not exist: {dir_path}")
            all_valid = False
        elif not os.access(dir_path, os.W_OK):
            logger.error(f"❌ Directory not writable: {dir_path}")
            all_valid = False
        else:
            logger.info(f"✅ Directory valid: {dir_path}")
    
    if not all_valid:
        logger.error("Create required directories with:")
        logger.error("mkdir -p storage/pages storage/crops logs")
        logger.error("chmod 755 storage logs storage/pages storage/crops")
    
    return all_valid

def main():
    """Main function to run all checks"""
    logger.info("Starting dependency validation...")
    
    checks = [
        ("Python Version", check_python_version),
        ("Python Packages", check_python_packages),
        ("Poppler Installation", check_poppler_installation),
        ("PDF Processing", test_pdf_processing),
        ("Required Directories", check_required_directories)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        logger.info(f"\n{'=' * 40}\nChecking {name}...\n{'-' * 40}")
        result = check_func()
        if result:
            passed += 1
            logger.info(f"\n✅ {name} check passed\n")
        else:
            logger.error(f"\n❌ {name} check failed\n")
    
    logger.info("=" * 60)
    logger.info(f"Validation complete: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 All dependency checks passed! The system is ready for deployment.")
        return 0
    else:
        logger.error("⚠️ Some dependency checks failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())