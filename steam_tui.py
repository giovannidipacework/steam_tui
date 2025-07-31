"""
steam_tui.py

Provides functions to retrieve and aggregate games from Steam libraries and user shortcuts.
"""

from parser import get_shortcuts, get_steam_libraries, get_installed_games, get_shortcut_last_playtime, get_localconfig_last_playtime
from icon_search import find_and_classify_steam_images
import os

def get_games(steam_id, steam_path):
    """
    Retrieve all games from Steam libraries and user shortcuts.

    Args:
        steam_id (str): The user's Steam ID.
        steam_path (str): The root path of the Steam installation.

    Returns:
        list[dict]: A list of dictionaries, each representing a game with keys such as
            'appid', 'name', 'exe', 'icon', 'category', 'last_played', and optionally 'size_on_disk' and 'path'.
    """
    games = []

    # Get user shortcuts
    shortcut_path = os.path.join(steam_path, "userdata", steam_id, "config", "shortcuts.vdf")
    shortcuts = get_shortcuts(shortcut_path)
    for shortcut in shortcuts:
        id = (shortcut["appid"] << 32) | 0x02000000
        game = {
            "appid": shortcut["appid"],
            "name": shortcut["appname"],
            "exe": f"start steam://rungameid/{id}",
            "icon": shortcut["icon"],
            "category": shortcut["0"],
            "last_played": 0,
            "play_time": 0,
            "path": shortcut['exe']
        }
        games.append(game)
    
    # Update last played time for shortcuts
    gameprocess_log_path = os.path.join(steam_path, "logs", "gameprocess_log.txt")
    get_shortcut_last_playtime(games, gameprocess_log_path)

    libraries = get_steam_libraries(steam_path)
    for lib in libraries:
        steam_games = get_installed_games(lib)

        for steam_game in steam_games:
            try:
                imgs = find_and_classify_steam_images(steam_path, steam_game["appid"])
            except Exception as e:
                print(f"icon not found for {steam_game['name']} - {steam_game['appid']}")
                # print(e)
                continue

            game = {
                "appid": steam_game["appid"],
                "name": steam_game["name"],
                "exe": f"start steam://run/{steam_game['appid']}",
                "icon": imgs['icon'],
                "category": "Steam",
                "last_played": int((steam_game["LastPlayed"])),
                "play_time": 0,
                "size_on_disk": steam_game["SizeOnDisk"]
            }
            games.append(game)

    localconfig_path = os.path.join(steam_path, "userdata", steam_id, "config", "localconfig.vdf")
    get_localconfig_last_playtime(games, localconfig_path)

    return games