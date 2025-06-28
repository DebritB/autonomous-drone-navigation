#!/usr/bin/env python3
"""
Main entry point for the Autonomous Drone Navigation System.

This script launches the GUI application for controlling the drone.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from src.main_window_final import DroneGUI

def main():
    """Main function to launch the drone navigation application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Autonomous Drone Navigation")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Drone Navigation Team")
    
    # Create and show the main window
    window = DroneGUI()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 