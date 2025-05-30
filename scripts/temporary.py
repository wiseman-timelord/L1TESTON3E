import json
from utility import Node

# Global variables
tree = None
selected_node = None
clipboard = None  # Stores copied Node
clipboard_action = None  # "copy" or "cut"
settings = {}
item_to_node = {}

# Default settings
_DEFAULT_SETTINGS = {
    "window_width": 800,
    "window_height": 600,
    "default_font": "Arial",
    "default_font_size": 12
}

def load_settings():
    """Load settings from persistent.json."""
    global settings
    try:
        with open("data/persistent.json", "r") as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = _DEFAULT_SETTINGS.copy()