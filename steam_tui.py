import json
from parser import get_shortcuts, get_steam_libraries, get_installed_games
from icon_search import find_and_classify_steam_images
import os

def get_games():
    with open("config.json", "r") as f:
        config = json.load(f)
    steam_id = config["steam_id"]
    steam_path = config["steam_path"]
    games = []

    shortcut_path = os.path.join(steam_path, "userdata", steam_id, "config", "shortcuts.vdf")
    shortcuts = get_shortcuts(shortcut_path)
    for shortcut in shortcuts:
        game = {
            "appid": shortcut["appid"],
            "name": shortcut["appname"],
            "exe": str(shortcut["exe"]).strip('"'),
            "icon": shortcut["icon"],
            "category": shortcut["0"]
        }
        games.append(game)

    libraries = get_steam_libraries(steam_path)
    for lib in libraries:
        steam_games = get_installed_games(lib)

    for steam_game in steam_games:
        try:
            imgs = find_and_classify_steam_images(steam_path, steam_game["appid"])
        except Exception as e:
            print(f"icon not found for {steam_game['name']} - {steam_game['appid']}")
            print(e)
            continue

        game = {
            "appid": steam_game["appid"],
            "name": steam_game["name"],
            "exe": f"start steam://run/{steam_game['appid']}",
            "icon": imgs['icon'],
            "category": "Steam",
            "last_played": steam_game["LastPlayed"],
            "size_on_disk": steam_game["SizeOnDisk"]
        }
        games.append(game)

    return games