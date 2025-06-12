from datetime import datetime
import re
import struct
import os
import vdf
from typing import List, Dict, Any

TYPE_END = 0x08
TYPE_STRING = 0x01
TYPE_INT32 = 0x02

def read_cstring_bytes(f) -> bytes:
    """Legge una stringa null-terminata come bytes."""
    buf = bytearray()
    while True:
        b = f.read(1)
        if not b or b == b'\x00':
            break
        buf.extend(b)
    return bytes(buf)

def decode_safe(b: bytes) -> str:
    """Decodifica sicura UTF-8, fallback Latin1."""
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return b.decode('latin1', errors='replace')

def get_shortcuts(path: str) -> List[Dict[str, Any]]:
    """Parsa shortcuts.vdf binario in modo robusto."""
    shortcuts = []

    known_keys = {
        "appname", "exe", "StartDir", "icon", "ShortcutPath", "LaunchOptions",
        "IsHidden", "AllowDesktopConfig", "AllowOverlay", "OpenVR", "Devkit",
        "DevkitGameID", "DevkitOverrideAppID", "LastPlayTime", "FlatpakAppID"
    }

    with open(path, 'rb') as f:
        # Cerca il primo marker valido (0x01 o 0x02) per saltare padding/corruzione iniziale
        while True:
            b = f.read(1)
            if not b:
                raise ValueError("File vuoto o marker non trovato.")
            if b[0] in (TYPE_STRING, TYPE_INT32, TYPE_END):
                f.seek(-1, 1)  # torna indietro di 1 byte
                break

        current = {}
        while True:
            marker = f.read(1)
            if not marker:
                break

            t = marker[0]

            if t == TYPE_END:
                if current:
                    shortcuts.append(current)
                    current = {}
                continue

            if t not in (TYPE_STRING, TYPE_INT32):
                continue  # ignora marker sconosciuti

            raw_key = read_cstring_bytes(f)
            # Pulisce i byte della chiave da caratteri non stampabili
            clean_key = bytes(b for b in raw_key if 0x20 <= b <= 0x7E)
            decoded_key = decode_safe(clean_key)
            
            # Cerca una chiave conosciuta anche se ci sono caratteri spuri
            key = None
            for known in known_keys:
                if known in decoded_key:
                    key = known
                    break

            if not key:
                parts = [p for p in decoded_key.split() if p.isidentifier()]
                key = parts[-1] if parts else decoded_key.strip()

            # ⚠️ Forza il tipo STRING se è "appname"
            if key == "appname":
                t = TYPE_STRING
            
            if t == TYPE_STRING:
                raw_val = read_cstring_bytes(f)
                val = decode_safe(raw_val)
            else:  # TYPE_INT32
                val_bytes = f.read(4)
                if len(val_bytes) < 4:
                    break  # evita crash su file tagliato
                val = struct.unpack('<I', val_bytes)[0]

            current[key] = val

    return shortcuts

def get_shortcut_last_playtime(games, gameprocess_log_path):
    pattern_add = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] AppID (\d+) adding PID (\d+) as a tracked process ""(.+?)""'

    for line in open(gameprocess_log_path, 'r', encoding='utf-8'):
        m = re.match(pattern_add, line)
        if m:
            timestamp, appid, pid, exe_path = m.groups()
            for game in games:
                if(game['exe'] == exe_path):
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    game["last_played"] = int(dt.timestamp())

def get_steam_libraries(steam_path):
    lib_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    with open(lib_path, encoding='utf-8') as f:
        data = vdf.load(f)

    libraries = []
    for k, v in data['libraryfolders'].items():
        if isinstance(v, dict):
            libraries.append(v['path'])
        else:
            libraries.append(v)
    return libraries

def get_installed_games(library_path):
    """
    Games structures:
    appid, universe, LauncherPath, name, StateFlags, installdir, LastUpdated, LastPlayed,
    SizeOnDisk, StagingSize, buildid, LastOwner, UpdateResult, BytesToDownload, BytesDownloaded,
    BytesToStage, BytesStaged, TargetBuildID', AutoUpdateBehavior, AllowOtherDownloadsWhileRunning,
    ScheduledAutoUpdate, InstalledDepots, InstallScripts, SharedDepots, UserConfig, MountedConfig
    """
    steamapps = os.path.join(library_path, "steamapps")
    games = []
    for fname in os.listdir(steamapps):
        if fname.startswith("appmanifest") and fname.endswith(".acf"):
            with open(os.path.join(steamapps, fname), encoding='utf-8') as f:
                appdata = vdf.load(f)
                info = appdata['AppState']
                games.append(info)
    return games
