import json # Added missing import

# Global variables
tree = None
selected_node = None
clipboard = None
clipboard_action = None
settings = {}
item_to_node = {}

# Default settings dictionary, to be used if persistent.json is not found or corrupted
_DEFAULT_SETTINGS = {
    "window_width": 800,
    "window_height": 600,
    "default_font": "Arial",
    "default_font_size": 12
    # Add any other default settings your application might need
}

def load_settings():
    """Load settings from persistent.json, applying defaults for missing keys."""
    global settings
    
    # Initialize with a copy of default settings
    settings = _DEFAULT_SETTINGS.copy()

    try:
        with open("data/persistent.json", "r") as f:
            loaded_settings = json.load(f)
            # Update with loaded settings, ensuring all default keys are present
            settings.update(loaded_settings)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file not found or JSON is invalid, settings remains as _DEFAULT_SETTINGS
        pass