#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
from datetime import datetime
from rich.console import Console, Group
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
import os
import msvcrt

console = Console()
games = get_games()

# Stato UI
selezionato = 0
term_height = os.get_terminal_size().lines

# Sort
sort_ascending = True
sort_modes = ["name", "category", "last_played"]
sort_index = 0

def sort_games(games, sort_mode, sort_ascending):
    sorted_list = sorted(games, key=lambda g: g[sort_mode], reverse=sort_ascending)
    return sorted_list

# Search
filtered_games = sort_games(games, sort_modes[sort_index], sort_ascending)
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

def filter_games(games, query):
    filter =  [g for g in games if query.lower() in g["name"].lower()]
    return filter

def get_key():
    key = msvcrt.getch()
    if key == b'\xe0':  # tasto speciale (frecce)
        key2 = msvcrt.getch()
        if key2 == b'H': return "w"  # freccia su
        if key2 == b'P': return "s"  # freccia giù
    try:
        return key.decode("utf-8").lower()
    except:
        return ""
    
def compute_visible_games(games_list, selezionato, max_height):
    n = len(games_list)
    # Punto di partenza: cerca di mettere selezionato in cima
    start_index = selezionato
    
    while True:
        total_height = 0
        visible = []
        for i in range(start_index, n):
            h = estimate_entry_height(games_list[i])
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

def estimate_entry_height(gioco, width=28):
    text = Text("➤ " + gioco["name"])
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

    # Colonna sinistra
    term_height = os.get_terminal_size().lines
    max_height = term_height - 6  # spazio per padding, titoli ecc.
    
    visible_games = compute_visible_games(filtered_games, selezionato, max_height)

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
    layout["main"]["left"].split_column(
        Layout(name="search",size=3),
        Layout(name="library")
    )
    layout["main"]["left"]["search"].update(search_panel)
    layout["main"]["left"]["library"].update(lib_panel)

    # Footer con comandi
    footer_text = Text("[W/S] Move | [Enter] Start | [/] Search | [TAB] Sort | [R] Reverse | [Q] Exit")
    layout["footer"].update(Panel(footer_text))

    # Colonna destra: info gioco selezionato
    icon_padding = 1
    icon_width = max(60, max_height)
    # Crea il layout verticale per info e icona
    info_icon_layout = Layout()
    info_icon_layout.split_column(
        Layout(name="info"),
        Layout(name="icon", size=int(icon_width/2)+icon_padding)  # spazio fisso per icona ASCII
    )

    current_game = filtered_games[selezionato]
    info = f"[bold]{current_game['name']}[/bold]\n\n[dim]AppId:[/] {current_game['appid']}\n\n[dim]Path:[/] {current_game['exe']}\n\n[dim]Category:[/] {current_game['category']}\n\n[dim]Icon:[/] {current_game['icon']}"
    if(current_game['last_played'] != 0):
        last_played = datetime.fromtimestamp(current_game['last_played'])
        last_played = last_played.strftime("%b %d %Y %H:%M")
        info += f"\n\n[dim]Last Played:[/] {last_played}"
    
    try:
        ascii_icon = image_to_ascii(current_game["icon"], icon_width)
    except:
        ascii_icon = f"[bold cyan]{current_game['name']}[/bold cyan]\n╭────╮\n│ :) │\n╰────╯"
    ascii_icon = Padding(ascii_icon, (0,icon_padding+1,0,0))

    info_icon_layout["info"].update(Align.left(info))
    info_icon_layout["icon"].update(Align.right(ascii_icon))

    # Inserisci tutto nel pannello destro
    layout["right"].update(Panel(info_icon_layout, title="Details", box=box.DOUBLE))
    
    return layout

# Live rendering e input
with Live(render(), screen=True) as live:
    while True:
        key = get_key()
        term_height = os.get_terminal_size().lines

        if search_mode:
            if key == "\r":  # Enter: return to normal mode
                search_mode = False
                live.update(render())
            elif key == "\x08":  # Backspace: delete char
                search_query = search_query[:-1]
                sorted_games = sort_games(games, sort_modes[sort_index], sort_ascending)
                filtered_games = filter_games(sorted_games, search_query)
                if filtered_games.__len__() <= 0:
                    filtered_games = no_result
                selezionato = 0
                live.update(render())
            elif key.isprintable():
                search_query += key
                sorted_games = sort_games(games, sort_modes[sort_index], sort_ascending)
                filtered_games = filter_games(sorted_games, search_query)
                if filtered_games.__len__() <= 0:
                    filtered_games = no_result
                selezionato = 0
                live.update(render())
        else:
            if key == "q":
                quit()
            elif key == "/":  # /: search moed
                search_mode = True
                sorted_games = sort_games(games, sort_modes[sort_index], sort_ascending)
                filtered_games = filter_games(sorted_games, search_query)
                live.update(render())
            elif key == "\t":  # TAB: sort mode
                sort_index = (sort_index + 1) % len(sort_modes)
                sorted_games = sort_games(games, sort_modes[sort_index], sort_ascending)
                filtered_games = filter_games(sorted_games, search_query)
                selezionato = 0
                live.update(render())
            elif key == "r":   # R: reverse order
                sort_ascending = not sort_ascending
                sorted_games = sort_games(games, sort_modes[sort_index], sort_ascending)
                filtered_games = filter_games(sorted_games, search_query)
                live.update(render())
            elif key == "w":
                selezionato = (selezionato - 1) % len(filtered_games)
                live.update(render())
            elif key == "s":
                selezionato = (selezionato + 1) % len(filtered_games)
                live.update(render())
            elif key == "\r": # Enter: start game
                try:
                    command = filtered_games[selezionato]["exe"]
                    subprocess.Popen(command, shell=True)
                except Exception as e:
                    console.print(f"[bold red]Errore:[/] {e}")