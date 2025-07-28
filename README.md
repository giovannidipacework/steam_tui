# Steam TUI Rich

A modern Text User Interface (TUI) for your Steam library, featuring themes, search, sorting, and ASCII art game icons.

## Requirements

- Python 3.10+
- [Rich](https://github.com/Textualize/rich)
- [Pillow](https://python-pillow.org/)
- [matplotlib](https://matplotlib.org/)
- [vdf](https://github.com/ValvePython/vdf)
- [readchar](https://github.com/magmax/python-readchar)

Install dependencies with:

```sh
pip install -r requirements.txt
```

## Getting Started

1. Configure the `config.json` file with your `steam_id` and Steam installation path (`steam_path`).
2. Start the interface with:

```sh
start_steam_tui_rich.bat
```

or

```sh
python steam_tui_rich.py
```

## Features

- Navigate your Steam library using the keyboard (W/S to move, Enter to launch a game)
- Instant search for games
- Sort by name, category, or last played
- Customizable themes (`themes/` folder)
- Detailed view and ASCII art icons for games

## Project Structure

- `steam_tui_rich.py`: Main TUI interface
- `steam_tui.py`: Logic to retrieve games from the Steam library
- `parser.py`: Steam configuration file parser
- `imag_proc.py`: Image to ASCII art conversion
- `icon_search.py`: Game image search and classification
- `load_themes.py`: Theme loader
- `themes/`: Customizable JSON themes

## Notes

- Make sure Steam is installed and the paths in `config.json` are correct.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.