import os
import json

def get_themes():
    """
    Returns a list of themes available in the 'themes' directory.
    """
    themes_dir = os.path.join(os.path.dirname(__file__), 'themes')
    themes = []
    
    if os.path.isdir(themes_dir):
        for filename in os.listdir(themes_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(themes_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        theme = json.load(f)
                        themes.append(theme)
                    except json.JSONDecodeError:
                        continue

    return themes