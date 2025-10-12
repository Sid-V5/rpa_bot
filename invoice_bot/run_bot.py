#!/usr/bin/env python3
"""
Launcher script for the RPA Invoice Processing Bot
Fixes relative import issues by setting up proper Python path.
"""

import sys
import os

# Add the src directory to Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Import and run the main module
from main import main

if __name__ == "__main__":
    main()
