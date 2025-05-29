# Global variables
tree = None
selected_node = None
clipboard = None
clipboard_action = None
settings = {}
item_to_node = {}

def load_settings():
    """Load settings from persistent.json."""
    global settings
    try:
        with open("data/persistent.json", "r") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {
            "window_width": 800,
            "window_height": 600,
            "default_font": "Arial",
            "default_font_size": 12
        }