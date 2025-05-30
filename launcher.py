import os
import subprocess
import sys
from PyQt5.QtWidgets import QApplication
from scripts.interface import MainWindow  # Corrected import path

def main():
    try:
        print("Launching LiteStone...")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"An error occurred while launching the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()