import os
import json
import subprocess
import time
import readchar
from datetime import datetime
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich import box
from steam_tui import get_games
from imag_proc import image_to_ascii
from load_themes import get_themes

def sort_games(games, sort_mode, sort_ascending):
    """
    Sort games based on the given sort mode and order.

    Args:
        games (list): List of game dictionaries.
        sort_mode (str): The field to sort by.
        sort_ascending (bool): Sort order, True for descending.

    Returns:
        list: Sorted list of games.
    """
    sorted_list = sorted(games, key=lambda g: g[sort_mode], reverse=sort_ascending)
    return sorted_list

def filter_games(games, query):
    """
    Filter games by a search query on the game name.

    Args:
        games (list): List of game dictionaries.
        query (str): Search string.

    Returns:
        list: Filtered list of games.
    """
    if query != "":
        filter =  [g for g in games if query.lower() in g["name"].lower()]
    else:
        filter = games
    return filter

def update_games(games, search_query, sort_mode, sort_ascending):
    """
    Update the games list by sorting and filtering.

    Args:
        games (list): List of game dictionaries.
        search_query (str): Search string.
        sort_mode (str): Field to sort by.
        sort_ascending (bool): Sort order.

    Returns:
        list: Filtered and sorted list of games.
    """
    sorted_games = sort_games(games, sort_mode, sort_ascending)
    filtered_games = filter_games(sorted_games, search_query)
    return filtered_games

def quit_steam():
    """
    Save the current configuration and quit the application.
    """
    with open("config.json", "w", encoding="utf-8") as f:
        config["theme"] = current_palette_index
        config["sort_index"] = sort_index
        config["ascending"] = sort_ascending
        json.dump(config, f, indent=4)
    quit()

def get_key():
    """
    Read a key from the user and map special keys to actions.

    Returns:
        str: The mapped key or character.
    """
    key = readchar.readkey()
    # Map arrow keys to 'w' (up) and 's' (down)
    if key == readchar.key.UP:
        return "w"
    if key == readchar.key.DOWN:
        return "s"
    # Enter key
    if key == readchar.key.ENTER:
        return "\r"
    # Tab key
    if key == readchar.key.TAB:
        return "\t"
    # Backspace
    if key == readchar.key.BACKSPACE:
        return "\x08"
    # All other keys (printable)
    if len(key) == 1 and key.isprintable():
        return key.lower()
    return ""

console = Console(record=True)

# Read config from config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
steam_id = config["steam_id"]
steam_path = config["steam_path"]
palettes = get_themes()

games = get_games(steam_id, steam_path)

# UI state
selected = 0
first_visible_game_index = 0
# Load the current theme
current_palette_index = config['theme']
if current_palette_index >= len(palettes) or current_palette_index < 0:
    current_palette_index = 0
palette_selected = palettes[current_palette_index]
# Set terminal size limits
max_height = os.get_terminal_size().lines - 6
max_width = os.get_terminal_size().columns - 6

# Sort options
sort_index = config['sort_index']
sort_ascending = config['ascending']
sort_modes = ["name", "category", "last_played", "play_time"]

# Search
search_query = ""
search_mode = False
# Fallback for no result in search
no_result = [
    {
        "appid": "No Result",
        "name": "No Result",
        "exe": "No Result",
        "icon": "",
        "category": "No Result",
        "last_played": 0,
        "path": "No Result"
    }
]

filtered_games = update_games(games, search_query, sort_modes[sort_index], sort_ascending)


def compute_visible_games(games_list, selected_game, first_visible_game_index, height, width):
    """
    Compute the list of visible games in the UI, scrolling if needed.

    Args:
        games_list (list): List of games to display.
        selected (int): Index of the selected game.
        max_height (int): Maximum number of lines available.
        width (int): Width for text wrapping.

    Returns:
        list: List of tuples (index, game) for visible games.
    """
    n = len(games_list)
    total_height = 0
    # Start point: try to put selected at the top
    start_index = first_visible_game_index

    # Cache for entry heights: {(name, width): height}
    height_cache = {}

    while True:
        total_height = 0
        visible = []

        while total_height < height:
            for i in range(start_index, n):
                cache_key = (games_list[i]['name'], width)
                if cache_key in height_cache:
                    h = height_cache[cache_key]
                else:
                    h = estimate_entry_height(games_list[i]['name'], width)
                    height_cache[cache_key] = h
                if total_height + h > height:
                    # If adding this game exceeds the height, stop
                    break
                visible.append((i, games_list[i]))
                total_height += h + 1  # +1 for padding between entries

        visible_games_names = [g[1]['name'] for g in visible]
        if selected_game['name'] not in visible_games_names:
            # If selected game is not visible, adjust the start index
            if selected > start_index:
                # If selected game is below the current start index, scroll down
               start_index += 1
            else:
                # If selected game is above the current start index, scroll up
                start_index -= 1
            
        else:
            # If selected game is visible, return the visible games
            break

    return visible

def estimate_entry_height(entry, width=28):
    """
    Estimate the number of lines needed to display a game entry.

    Args:
        entry (str): The game name.
        width (int): The width for wrapping.

    Returns:
        int: Number of lines required.
    """
    text = Text("➤ " + entry)
    lines = text.wrap(console, width, tab_size=4)
    return len(lines)

def render():
    """
    Render the entire TUI layout using Rich.

    Returns:
        Layout: The Rich Layout object representing the UI.
    """
    layout = Layout()
    layout.split_column(
        Layout(name="banner", size=1),
        Layout(name="main", ratio=8),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=3)
    )
    search_size = 3
    layout["main"]["left"].split_column(
        Layout(name="search",size=search_size),
        Layout(name="library")
    )

    info_icon_layout = Layout()
    info_icon_layout.split_column(
        Layout(name="info"),
        Layout(name="icon")  # fixed space for ASCII icon
    )

    current_game = filtered_games[selected]

    max_height = os.get_terminal_size().lines - 6
    max_width = os.get_terminal_size().columns - 6

    term_width = os.get_terminal_size().columns
    theme_name = palette_selected.get("name", "Theme")
    banner_text = f"= TUI Media Player - {theme_name} ="
    banner_line = banner_text.center(term_width, "=")

    banner = Text(banner_line, style=palette_selected["text"], justify="center")
    layout["banner"].update(Align.center(banner))

    left_width =  max_width*((layout["main"]["left"].ratio)/(layout["main"]["left"].ratio+layout["main"]["right"].ratio))
    left_height = max_height - search_size
    global first_visible_game_index
    visible_games = compute_visible_games(filtered_games, current_game, first_visible_game_index, left_height, int(left_width))
    
    if visible_games:
        first_game_name = visible_games[0][1]['name']
        for idx, game in enumerate(filtered_games):
            if game['name'] == first_game_name:
                first_visible_game_index = idx
                break
    else:
        first_visible_game_index = 0

    table = Table.grid(padding=1)
    table.box = box.SIMPLE

    for i, game in visible_games:
        prefix = "➤ " if i == selected else ""
        row = Text(prefix + str(game["name"]))
        if i == selected:
            row.stylize(f"bold {palette_selected['selected']}")
        table.add_row(row)

    search_panel = Panel(Text(f"Search: {search_query}_"), title="Search", subtitle=f"[dim]Sort by: {sort_modes[sort_index]} {'↑' if sort_ascending else '↓'}[/]", style=f"{palette_selected['search']}")
    lib_panel = Panel(table, title="Library", box=box.DOUBLE, style=palette_selected["text"])

    layout["main"]["left"]["search"].update(search_panel)
    layout["main"]["left"]["library"].update(lib_panel)

    # Footer with commands
    footer_text = Text("[W/S] Move | [Enter] Start | [/] Search | [TAB] Sort | [R] Reverse | [T] Theme | [Q] Exit")
    layout["footer"].update(Panel(footer_text, style=palette_selected['text']))

    info_title = Text(f"{current_game['name']} \n", style=palette_selected['game_title'])
    info_details = Text(f"\n\nAppId: {current_game['appid']}\nPath: {current_game['exe']}\nCategory: {current_game['category']}\nIcon: {current_game['icon']}", style=palette_selected['info'])

    info_text = Text()
    info_text.append(info_title)
    info_text.append(info_details)

    if(current_game['last_played'] != 0):
        last_played = datetime.fromtimestamp(current_game['last_played'])
        last_player = last_played.strftime("%b %d %Y %H:%M")
        last_played_text = Text(f"\n\nLast Played: {last_player}", style=palette_selected['time'])
        info_text.append(last_played_text)

    if(current_game['play_time'] != 0):
        play_time = current_game['play_time']
        play_time_hours = play_time / 60
        play_time_minutes = play_time % 60
        play_time_text = Text(f"\n\nPlay Time: {play_time_hours:.0f} hours {play_time_minutes} minutes", style=palette_selected['time'])
        info_text.append(play_time_text)

    info_icon_layout["info"].update(Align.left(info_text))

    icon_padding = 2
    right_width =  max_width*((layout["main"]["right"].ratio)/(layout["main"]["left"].ratio+layout["main"]["right"].ratio))
    right_width -= estimate_entry_height(info_text.__str__(), int(right_width))
    icon_width = int(right_width + icon_padding)
    icon_height = int(max_height/2)

    try:
        ascii_icon = image_to_ascii(current_game["icon"], icon_width, icon_height)
    except:
        ascii_icon = Text(f"[bold cyan]{current_game['name']}[/bold cyan]\n╭────╮\n│ :) │\n╰────╯")

    info_icon_layout["icon"].update(Align.right(ascii_icon))

    # Insert everything into the right panel
    layout["right"].update(Panel(info_icon_layout, title="Details", box=box.DOUBLE, style=palette_selected["text"]))

    return layout

# Live rendering and input
with Live(render(), screen=True) as live:
    """
    Main event loop for the TUI. Handles user input and updates the UI.
    """
    while True:
        key = get_key()

        if search_mode:
            if key == "\r": # Enter: return to normal mode
                search_mode = False
            elif key == "\x08": # Backspace: delete char
                search_query = search_query[:-1]
                selected = 0
            elif key.isprintable(): # OTHER: add to search_query
                search_query += key
                selected = 0
        else:
            if key == "q":  # Q: save config and quit
                quit_steam()
            elif key == "/":    # /: search mode
                search_mode = True
            elif key == "\t":   # TAB: sort mode
                sort_index = (sort_index + 1) % len(sort_modes)
                selected = 0
            elif key == "t":    # T: change theme
                current_palette_index = (current_palette_index + 1) % len(palettes)
                palette_selected = palettes[current_palette_index]
            elif key == "r":    # R: reverse order
                sort_ascending = not sort_ascending
            elif key == "w":    # W: move up
                selected = (selected - 1) % len(filtered_games)
            elif key == "s":    # S: move down
                selected = (selected + 1) % len(filtered_games)
            elif key == "\r":   # Enter: start game
                try:
                    command = filtered_games[selected]["exe"]
                    subprocess.Popen(command, shell=True)
                    time.sleep(5)
                    games = get_games(steam_id, steam_path)
                except Exception as e:
                    console.print(f"[bold red]Error:[/] {e}")

        filtered_games = update_games(games, search_query, sort_modes[sort_index], sort_ascending)
        if filtered_games.__len__() <= 0:
            filtered_games = no_result
        live.update(render())