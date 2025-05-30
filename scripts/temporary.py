import json # Added missing import

# Global variables
tree = None
selected_node = None
clipboard = None
clipboard_action = None
settings = {}
item_to_node = {}

# Default settings dictionary, to be used if persistent.json is not found or corrupted\n_DEFAULT_SETTINGS = {\n    "window_width": 800,\n    "window_height": 600,\n    "default_font": "Arial",\n    "default_font_size": 12\n    # Add any other default settings your application might need\n}\n
def load_settings():
    """Load settings from persistent.json."""
    global settings
    try:
        with open("data/persistent.json", "r") as f:
            settings = json.load(f)
        settings = {
            "window_width": 800,
            "window_height": 600,
            "default_font": "Arial",
            "default_font_size": 12
            # Add any other default settings your application might need
        }
        settings = {
            "window_width": 800,
            "window_height": 600,
            "default_font": "Arial",
            "default_font_size": 12
        }