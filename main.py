"""
Main entry point for the Git Commit Review Application.

This script initializes and runs the PyQt5 GUI application.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the GUI
from gui import GitCommitReviewGUI
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GitCommitReviewGUI()
    window.show()
    sys.exit(app.exec_())