#!/usr/bin/env python3

"""
EasyOCR Setup and Testing Tool for RPA Invoice Processing Bot
EasyOCR is a pure Python OCR library that doesn't require external binaries.
"""
import os
import sys
import platform

def test_easyocr():
    """Test if EasyOCR is working"""
    print("🧪 Testing EasyOCR installation...")

    try:
        import easyocr
        print(f"✅ easyocr imported successfully (version: {easyocr.__version__})")

        # Test EasyOCR reader initialization
        print("📝 Testing EasyOCR reader initialization...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✅ EasyOCR reader initialized successfully")

        # Test simple OCR on generated image
        print("📝 Testing OCR with sample text...")
        from PIL import Image, ImageDraw
        import numpy as np

        # Create test image
        img = Image.new('RGB', (300, 50), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST INVOICE TEXT", fill=(0, 0, 0))
        draw.text((10, 30), "Vendor: Test Company", fill=(0, 0, 0))

        # Convert to numpy array for EasyOCR
        img_array = np.array(img)

        # Perform OCR
        results = reader.readtext(img_array, detail=0)  # detail=0 returns just text

        detected_text = " ".join(results) if results else ""
        print(f"📄 Detected text: '{detected_text}'")

        if "TEST" in detected_text.upper():
            print("✅ OCR test successful! EasyOCR is working correctly.")
            return True
        elif detected_text.strip():
            print(f"⚠️  OCR test partial - detected some text but not expected pattern")
            return True  # Still working, just not perfect
        else:
            print("❌ OCR test failed - no text detected")
            return False

    except ImportError as e:
        print(f"❌ easyocr not available: {e}")
        print("   Install with: pip install easyocr")
        return False
    except Exception as e:
        print(f"❌ EasyOCR test failed: {e}")
        return False

def install_easyocr():
    """Install EasyOCR via pip"""
    print("🔧 Installing EasyOCR...")

    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "easyocr>=1.7.0", "torch>=1.13.0"], check=True)
        print("✅ EasyOCR installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print("   Try: pip install easyocr torch --upgrade")
        return False

def main():
    """Main function"""
    print("🔍 EasyOCR Setup Tool")
    print("=" * 40)

    # Check if trying to install
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        success = install_easyocr()
        if success:
            print("\n🧪 Testing installation...")
            test_easyocr()
        return

    # Check if trying to test
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_easyocr()
        return

    # Default behavior: test first, then offer install
    print("EasyOCR is a modern OCR library that works without external binaries!")
    print("Advantages over Tesseract: Pure Python, easier installation, better accuracy")
    print()

    if test_easyocr():
        print("\n🎉 EasyOCR is working! Your RPA bot will now use EasyOCR as primary OCR.")
        print("💡 EasyOCR models will download automatically on first use (can take a few minutes)")
    else:
        print("\n❌ EasyOCR is not working.")
        print("📦 Would you like to install it automatically?")
        print("   Run: python install_ocr.py --install")
        print("   Or manually: pip install easyocr torch")
        print("   Then test: python install_ocr.py --test")

if __name__ == "__main__":
    main()
