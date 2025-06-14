import os
import msvcrt
import json
import subprocess
import threading
import time
from datetime import datetime
from rich.console import Console
from rich.text import Text
from rich.padding import Padding
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich import box
from steam_tui import get_games
from imag_proc import image_to_ascii

# Sort games based on sort mode and sord_ascending order
def sort_games(games, sort_mode, sort_ascending):
    sorted_list = sorted(games, key=lambda g: g[sort_mode], reverse=sort_ascending)
    return sorted_list

# Filter games based on query
def filter_games(games, query):
    if query != "":
        filter =  [g for g in games if query.lower() in g["name"].lower()]
    else:
        filter = games
    return filter

# Update the games based on query and sort mode
def update_games(games, search_query, sort_mode, sort_ascending):
    sorted_games = sort_games(games, sort_mode, sort_ascending)
    filtered_games = filter_games(sorted_games, search_query)
    return filtered_games

# Save last sort order and quit
def quit_steam():
    with open("config.json", "w") as f:
        config["sort_index"] = sort_index
        config["ascending"] = sort_ascending
        json.dump(config, f, indent=4)
    quit()

def get_key():
    if not msvcrt.kbhit():
        return ""  # Nessun tasto premuto, ritorna stringa vuota subito
    key = msvcrt.getch()
    if key == b'\xe0':  # tasto speciale (frecce)
        key2 = msvcrt.getch()
        if key2 == b'H': return "w"  # freccia su
        if key2 == b'P': return "s"  # freccia giù
    try:
        return key.decode("utf-8").lower()
    except:
        return ""

console = Console(record=True)

# Read config from config.json
with open("config.json", "r") as f:
    config = json.load(f)
steam_id = config["steam_id"]
steam_path = config["steam_path"]

games = get_games(steam_id, steam_path)

# UI state
selezionato = 0
max_height = os.get_terminal_size().lines - 6
max_width = os.get_terminal_size().columns - 6

# Sort options
sort_index = config['sort_index']
sort_ascending = config['ascending']
sort_modes = ["name", "category", "last_played"]

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

def compute_visible_games(games_list, selezionato, max_height, width):
    n = len(games_list)
    # Punto di partenza: cerca di mettere selezionato in cima
    start_index = selezionato
    
    while True:
        total_height = 0
        visible = []
        for i in range(start_index, n):
            h = estimate_entry_height(games_list[i]['name'], width)
            if total_height + h > max_height:
                break
            visible.append((i, games_list[i]))
            total_height += h
        
        # Se il gioco selezionato è fuori dalla finestra (dopo l'ultima riga)
        if selezionato < start_index:
            # scendi in lista spostando start_index giù
            start_index = selezionato
            continue
        
        if selezionato >= start_index + len(visible):
            # il selezionato è sotto la finestra, fai scroll down
            start_index += 1
            if start_index > selezionato:
                start_index = selezionato
            continue
        
        break  # selezionato è dentro la finestra
    
    return visible

def estimate_entry_height(entry, width=28):
    text = Text("➤ " + entry)
    lines = text.wrap(console, width, tab_size=4)
    return len(lines)

def render():
    layout = Layout()
    layout.split_column(
        Layout(name="main", ratio=8),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=3)
    )
    layout["main"]["left"].split_column(
        Layout(name="search",size=3),
        Layout(name="library")
    )
    
    max_height = os.get_terminal_size().lines - 6
    max_width = os.get_terminal_size().columns - 6
    
    left_width =  max_width*((layout["main"]["left"].ratio)/(layout["main"]["left"].ratio+layout["main"]["right"].ratio))
    visible_games = compute_visible_games(filtered_games, selezionato, max_height, int(left_width))

    tabella = Table.grid(padding=1)
    tabella.box = box.SIMPLE

    for i, gioco in visible_games:
        prefisso = "➤ " if i == selezionato else ""
        riga = Text(prefisso + str(gioco["name"]))
        if i == selezionato:
            riga.stylize("bold green")
        tabella.add_row(riga)


    search_panel = Panel(Text(f"Search: {search_query}_"), title="Search", subtitle=f"[dim]Sort by: {sort_modes[sort_index]} {"↑" if sort_ascending else "↓"}[/]")
    lib_panel = Panel(tabella, title="Library", box=box.DOUBLE)

    layout["main"]["left"]["search"].update(search_panel)
    layout["main"]["left"]["library"].update(lib_panel)

    # Footer con comandi
    footer_text = Text("[W/S] Move | [Enter] Start | [/] Search | [TAB] Sort | [R] Reverse | [Q] Exit")
    layout["footer"].update(Panel(footer_text))

    current_game = filtered_games[selezionato]
    info = f"[bold]{current_game['name']}[/bold]\n\n[dim]AppId:[/] {current_game['appid']}\n\n[dim]Path:[/] {current_game['exe']}\n\n[dim]Category:[/] {current_game['category']}\n\n[dim]Icon:[/] {current_game['icon']}"
    if(current_game['last_played'] != 0):
        last_played = datetime.fromtimestamp(current_game['last_played'])
        last_played = last_played.strftime("%b %d %Y %H:%M")
        info += f"\n\n[dim]Last Played:[/] {last_played}"

    icon_padding = 2
    right_width =  max_width*((layout["main"]["right"].ratio)/(layout["main"]["left"].ratio+layout["main"]["right"].ratio))
    right_width -= estimate_entry_height(info, int(right_width))
    icon_width = right_width + icon_padding
    
    try:
        ascii_icon = image_to_ascii(current_game["icon"], int(icon_width))
    except:
        ascii_icon = Text(f"[bold cyan]{current_game['name']}[/bold cyan]\n╭────╮\n│ :) │\n╰────╯")

    info_icon_layout = Layout()
    info_icon_layout.split_column(
        Layout(name="info"),
        Layout(name="icon")  # spazio fisso per icona ASCII
    )

    info_icon_layout["info"].update(Align.left(info))
    info_icon_layout["icon"].update(Align.right(ascii_icon))

    # Inserisci tutto nel pannello destro
    layout["right"].update(Panel(info_icon_layout, title="Details", box=box.DOUBLE))
    
    return layout

# Live rendering e input
with Live(render(), screen=True) as live:
    while True:
        key = get_key()

        if search_mode:
            if key == "\r": # Enter: return to normal mode
                search_mode = False
            elif key == "\x08": # Backspace: delete char
                search_query = search_query[:-1]
                selezionato = 0
            elif key.isprintable(): # OTHER: add to search_query
                search_query += key
                selezionato = 0
        else:
            if key == "q":  # Q: save confing and quit
                quit_steam()
            elif key == "/":    # /: search moed
                search_mode = True
            elif key == "\t":   # TAB: sort mode
                sort_index = (sort_index + 1) % len(sort_modes)
                selezionato = 0
            elif key == "r":    # R: reverse order
                sort_ascending = not sort_ascending
            elif key == "w":    # W: move down
                selezionato = (selezionato - 1) % len(filtered_games)
            elif key == "s":    # S: move up
                selezionato = (selezionato + 1) % len(filtered_games)
            elif key == "\r":   # Enter: start game
                try:
                    command = filtered_games[selezionato]["exe"]
                    subprocess.Popen(command, shell=True)
                    time.sleep(5)
                    games = get_games(steam_id, steam_path)
                except Exception as e:
                    console.print(f"[bold red]Errore:[/] {e}")

        filtered_games = update_games(games, search_query, sort_modes[sort_index], sort_ascending)
        if filtered_games.__len__() <= 0:
            filtered_games = no_result
        live.update(render())