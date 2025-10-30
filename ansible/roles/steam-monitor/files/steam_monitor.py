#!/usr/bin/env python3
"""
Steam Monitor for Sunshine
Automatically detects installed Steam games and registers them in Sunshine for streaming.

Features:
- Real-time detection with inotify
- Automatic filtering of tools, DLCs, and Proton
- Steam API integration for metadata
- Cover art download (portrait 600x900)
- Auto-removal of uninstalled games
- Atomic updates to apps.json
"""

import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
import shutil

try:
    import vdf
    import requests
    from inotify_simple import INotify, flags
except ImportError as e:
    print(f"ERROR: Missing required Python package: {e}", file=sys.stderr)
    print("Install with: pip install --user vdf requests inotify-simple", file=sys.stderr)
    sys.exit(1)

# Configuration (will be set by environment or defaults)
STEAM_LIBRARY_PATH = Path(os.getenv("STEAM_LIBRARY_PATH", "~/.local/share/Steam/steamapps")).expanduser()
SUNSHINE_APPS_FILE = Path(os.getenv("SUNSHINE_APPS_FILE", "~/.config/sunshine/apps.json")).expanduser()
COVERS_DIR = Path(os.getenv("COVERS_DIR", "~/.local/share/sunshine/covers")).expanduser()
STATE_FILE = Path(os.getenv("STATE_FILE", "~/.local/state/steam_monitor_state.json")).expanduser()

# Steam API configuration
STEAM_API_BASE = "https://store.steampowered.com/api"
STEAM_API_TIMEOUT = int(os.getenv("STEAM_API_TIMEOUT", "10"))
STEAM_API_RATE_LIMIT_MS = int(os.getenv("STEAM_API_RATE_LIMIT_MS", "200"))

# Cover URLs (portrait 600x900)
COVER_URLS = [
    "https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_600x900_2x.jpg",
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900_2x.jpg",
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
]

# Filtering configuration
EXCLUDE_TOOLS = os.getenv("EXCLUDE_TOOLS", "true").lower() == "true"
EXCLUDE_DLC = os.getenv("EXCLUDE_DLC", "true").lower() == "true"
MIN_SIZE_MB = int(os.getenv("MIN_SIZE_MB", "50"))
REMOVE_UNINSTALLED = os.getenv("REMOVE_UNINSTALLED", "true").lower() == "true"

# Excluded patterns
EXCLUDED_PATTERNS = [
    r'^Proton.*',
    r'^SteamLinuxRuntime.*',
    r'^Steam.*Tools',
    r'^Steamworks Common.*',
    r'^Steamworks SDK.*',
]

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class SteamMonitor:
    """Monitors Steam library and syncs games to Sunshine."""

    def __init__(self):
        self.state = self.load_state()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SteamMonitor/1.0'})

        # Ensure directories exist
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SUNSHINE_APPS_FILE.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict:
        """Load previous state from file."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}")

        return {
            "version": "1.0",
            "last_scan": None,
            "known_games": {}
        }

    def save_state(self):
        """Save current state to file."""
        try:
            self.state["last_scan"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def scan_steam_manifests(self) -> Dict[str, Dict]:
        """Scan Steam library for installed games."""
        games = {}

        if not STEAM_LIBRARY_PATH.exists():
            logger.error(f"Steam library path does not exist: {STEAM_LIBRARY_PATH}")
            return games

        for manifest_file in STEAM_LIBRARY_PATH.glob("appmanifest_*.acf"):
            try:
                appid = manifest_file.stem.split('_')[1]
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    data = vdf.load(f)
                    app_state = data.get('AppState', {})
                    games[appid] = {
                        'name': app_state.get('name', f'Game {appid}'),
                        'installdir': app_state.get('installdir', ''),
                        'size_bytes': int(app_state.get('SizeOnDisk', 0)),
                        'manifest_file': str(manifest_file)
                    }
            except Exception as e:
                logger.warning(f"Failed to parse {manifest_file}: {e}")

        return games

    def is_excluded(self, game_info: Dict) -> tuple[bool, str]:
        """Check if game should be excluded based on filters."""
        name = game_info['name']
        size_mb = game_info['size_bytes'] / (1024 * 1024)

        # Check size
        if size_mb < MIN_SIZE_MB:
            return True, f"too small ({size_mb:.1f}MB < {MIN_SIZE_MB}MB)"

        # Check excluded patterns
        if EXCLUDE_TOOLS:
            for pattern in EXCLUDED_PATTERNS:
                if re.match(pattern, name, re.IGNORECASE):
                    return True, f"matches excluded pattern: {pattern}"

        return False, ""

    def get_steam_api_details(self, appid: str) -> Optional[Dict]:
        """Fetch game details from Steam API."""
        url = f"{STEAM_API_BASE}/appdetails?appids={appid}"

        for attempt in range(3):
            try:
                time.sleep(STEAM_API_RATE_LIMIT_MS / 1000.0)  # Rate limiting
                response = self.session.get(url, timeout=STEAM_API_TIMEOUT)
                response.raise_for_status()

                data = response.json()
                if data.get(appid, {}).get('success'):
                    return data[appid]['data']
                else:
                    logger.warning(f"[API] {appid}: API returned success=false")
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"[API] {appid}: Timeout (attempt {attempt + 1}/3)")
            except requests.exceptions.RequestException as e:
                logger.warning(f"[API] {appid}: Request failed: {e}")

            if attempt < 2:
                time.sleep(2 ** attempt)  # Exponential backoff

        return None

    def is_game_playable(self, game_info: Dict, api_details: Optional[Dict]) -> tuple[bool, str]:
        """Determine if this is a playable game (not DLC, tool, etc)."""
        # Check API details if available
        if api_details and EXCLUDE_DLC:
            app_type = api_details.get('type', '').lower()
            if app_type in ['dlc', 'demo', 'tool', 'config', 'application']:
                return False, f"type is '{app_type}'"

        return True, ""

    def download_cover(self, appid: str) -> Optional[Path]:
        """Download cover art for game."""
        cover_path = COVERS_DIR / f"{appid}.jpg"

        if cover_path.exists():
            return cover_path

        for url_template in COVER_URLS:
            url = url_template.format(appid=appid)
            try:
                response = self.session.get(url, timeout=30, stream=True)
                if response.status_code == 200:
                    with open(cover_path, 'wb') as f:
                        shutil.copyfileobj(response.raw, f)

                    size_kb = cover_path.stat().st_size / 1024
                    logger.info(f"[COVER] {appid}: Downloaded ({size_kb:.1f}KB)")
                    return cover_path
            except Exception as e:
                logger.debug(f"[COVER] {appid}: Failed to download from {url}: {e}")

        logger.warning(f"[COVER] {appid}: No cover found from any source")
        return None

    def load_sunshine_apps(self) -> Dict:
        """Load current Sunshine apps.json."""
        if not SUNSHINE_APPS_FILE.exists():
            return {"env": {"PATH": "$(PATH):$(HOME)/.local/bin"}, "apps": []}

        try:
            with open(SUNSHINE_APPS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {SUNSHINE_APPS_FILE}: {e}")
            return {"env": {"PATH": "$(PATH):$(HOME)/.local/bin"}, "apps": []}

    def save_sunshine_apps(self, apps_data: Dict):
        """Save Sunshine apps.json atomically."""
        # Backup existing file
        if SUNSHINE_APPS_FILE.exists():
            backup_path = SUNSHINE_APPS_FILE.with_suffix('.json.backup')
            shutil.copy2(SUNSHINE_APPS_FILE, backup_path)

        # Write to temporary file
        tmp_path = SUNSHINE_APPS_FILE.with_suffix('.json.tmp')
        try:
            with open(tmp_path, 'w') as f:
                json.dump(apps_data, f, indent=2)

            # Atomic rename
            tmp_path.rename(SUNSHINE_APPS_FILE)
            logger.debug(f"Saved {SUNSHINE_APPS_FILE}")
        except Exception as e:
            logger.error(f"Failed to save {SUNSHINE_APPS_FILE}: {e}")
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def add_game_to_sunshine(self, appid: str, game_info: Dict):
        """Add a game to Sunshine apps.json."""
        # Check if already excluded
        excluded, reason = self.is_excluded(game_info)
        if excluded:
            logger.info(f"[SKIP] {appid}: {game_info['name']} - {reason}")
            return

        # Get API details
        logger.info(f"[NEW] {appid}: {game_info['name']}")
        api_details = self.get_steam_api_details(appid)

        # Check if playable
        playable, reason = self.is_game_playable(game_info, api_details)
        if not playable:
            logger.info(f"[SKIP] {appid}: {game_info['name']} - {reason}")
            return

        # Download cover
        cover_path = self.download_cover(appid)

        # Load current apps
        apps_data = self.load_sunshine_apps()

        # Check if game already exists
        for app in apps_data['apps']:
            if f"steam://rungameid/{appid}" in app.get('cmd', ''):
                logger.info(f"[EXISTS] {appid}: {game_info['name']} already in Sunshine")
                return

        # Create app entry
        new_app = {
            "name": game_info['name'],
            "output": "",
            "cmd": f"steam steam://rungameid/{appid}",
            "exclude-global-prep-cmd": "false",
            "elevated": "false",
            "auto-detach": "false",
            "image-path": str(cover_path) if cover_path else ""
        }

        # Add to apps list
        apps_data['apps'].append(new_app)

        # Save
        self.save_sunshine_apps(apps_data)

        # Update state
        self.state['known_games'][appid] = {
            "name": game_info['name'],
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "in_sunshine": True
        }
        self.save_state()

        logger.info(f"[SUNSHINE] Added '{game_info['name']}' to Sunshine")
        self.reload_sunshine()

    def remove_game_from_sunshine(self, appid: str):
        """Remove a game from Sunshine apps.json."""
        game_name = self.state['known_games'].get(appid, {}).get('name', appid)

        # Load current apps
        apps_data = self.load_sunshine_apps()

        # Filter out the game
        original_count = len(apps_data['apps'])
        apps_data['apps'] = [
            app for app in apps_data['apps']
            if f"steam://rungameid/{appid}" not in app.get('cmd', '')
        ]

        if len(apps_data['apps']) < original_count:
            self.save_sunshine_apps(apps_data)
            logger.info(f"[REMOVED] {appid}: {game_name} from Sunshine")

            # Remove cover
            cover_path = COVERS_DIR / f"{appid}.jpg"
            if cover_path.exists():
                cover_path.unlink()

            # Update state
            if appid in self.state['known_games']:
                del self.state['known_games'][appid]
            self.save_state()

            self.reload_sunshine()

    def reload_sunshine(self):
        """Reload Sunshine service to apply changes."""
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', '--user', 'reload-or-restart', 'sunshine.service'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.debug("[SUNSHINE] Service reloaded")
            else:
                logger.warning(f"[SUNSHINE] Failed to reload: {result.stderr}")
        except Exception as e:
            logger.warning(f"[SUNSHINE] Failed to reload service: {e}")

    def sync_all_games(self):
        """Sync all installed games with Sunshine."""
        logger.info("Starting full sync...")

        # Scan current Steam library
        current_games = self.scan_steam_manifests()
        logger.info(f"Found {len(current_games)} games in Steam library")

        # Detect removed games
        if REMOVE_UNINSTALLED:
            known_appids = set(self.state['known_games'].keys())
            current_appids = set(current_games.keys())
            removed_appids = known_appids - current_appids

            if removed_appids:
                logger.info(f"Removing {len(removed_appids)} uninstalled games")
                for appid in removed_appids:
                    self.remove_game_from_sunshine(appid)

        # Detect new games
        for appid, game_info in current_games.items():
            if appid not in self.state['known_games']:
                self.add_game_to_sunshine(appid, game_info)

        logger.info("Sync complete")

    def watch_steam_library(self):
        """Watch Steam library for changes using inotify."""
        logger.info(f"Watching {STEAM_LIBRARY_PATH} for changes...")

        inotify = INotify()
        watch_flags = flags.CLOSE_WRITE | flags.DELETE | flags.MOVED_TO | flags.MOVED_FROM
        wd = inotify.add_watch(str(STEAM_LIBRARY_PATH), watch_flags)

        logger.info("Steam monitor started - waiting for changes")

        while True:
            try:
                for event in inotify.read(timeout=1000):
                    filename = event.name
                    if not filename or not filename.startswith('appmanifest_'):
                        continue

                    appid = filename.split('_')[1].split('.')[0]

                    if event.mask & (flags.CLOSE_WRITE | flags.MOVED_TO):
                        logger.info(f"[INOTIFY] Detected new/modified manifest: {filename}")
                        # Small delay to ensure file is fully written
                        time.sleep(1)
                        games = self.scan_steam_manifests()
                        if appid in games:
                            self.add_game_to_sunshine(appid, games[appid])

                    elif event.mask & (flags.DELETE | flags.MOVED_FROM):
                        logger.info(f"[INOTIFY] Detected removed manifest: {filename}")
                        if REMOVE_UNINSTALLED:
                            self.remove_game_from_sunshine(appid)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                time.sleep(5)


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Steam Monitor for Sunshine - Starting")
    logger.info("=" * 60)
    logger.info(f"Steam library: {STEAM_LIBRARY_PATH}")
    logger.info(f"Sunshine apps: {SUNSHINE_APPS_FILE}")
    logger.info(f"Covers dir: {COVERS_DIR}")
    logger.info(f"Exclude tools: {EXCLUDE_TOOLS}")
    logger.info(f"Exclude DLC: {EXCLUDE_DLC}")
    logger.info(f"Remove uninstalled: {REMOVE_UNINSTALLED}")
    logger.info("=" * 60)

    monitor = SteamMonitor()

    # Initial sync
    monitor.sync_all_games()

    # Start watching
    try:
        monitor.watch_steam_library()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        logger.info("Steam monitor stopped")


if __name__ == '__main__':
    main()
