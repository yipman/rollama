#!/usr/bin/env python3
"""
Rollama GUI - A graphical interface for Rollama
"""

import sys
import os

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rollama.gui import main

if __name__ == "__main__":
    main()
