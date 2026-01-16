"""State management for saving and loading player progress."""

import json
import shutil
from pathlib import Path
from dataclasses import asdict
from typing import Optional, List
from datetime import datetime

from ..models.player import PlayerStats
from ..utils import logger, SaveError, LoadError


class StateManager:
    """Manages player state persistence."""

    def __init__(self):
        """Initialize state manager with save directory."""
        self.save_dir = Path.home() / ".shellquest" / "saves"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.current_player: Optional[PlayerStats] = None
        logger.debug(f"StateManager initialized with save_dir: {self.save_dir}")

    def save_progress(self, player: PlayerStats) -> bool:
        """
        Save player progress to JSON file.

        Uses atomic write with backup for safety.
        """
        save_path = self.save_dir / f"{player.username}.json"
        temp_path = save_path.with_suffix('.tmp')
        backup_path = save_path.with_suffix('.bak')

        try:
            save_data = {
                "version": "1.0.0",
                "player": asdict(player),
                "timestamp": datetime.now().isoformat()
            }

            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            # Backup existing save if it exists
            if save_path.exists():
                shutil.copy(save_path, backup_path)

            # Atomic rename
            temp_path.rename(save_path)

            logger.info(f"Progress saved for player: {player.username}")
            return True

        except PermissionError as e:
            logger.error(f"Permission denied saving to {save_path}: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error saving progress: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error saving progress: {e}")
            return False
        finally:
            # Clean up temp file if it still exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def load_progress(self, username: str) -> Optional[PlayerStats]:
        """
        Load player progress from JSON file.

        Returns None if save doesn't exist or is invalid.
        """
        save_path = self.save_dir / f"{username}.json"

        if not save_path.exists():
            logger.debug(f"No save file found for: {username}")
            return None

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            player_data = save_data['player']
            player = PlayerStats(**player_data)

            self.current_player = player
            logger.info(f"Progress loaded for player: {username}")
            return player

        except json.JSONDecodeError as e:
            logger.warning(f"Corrupted save file for {username}: {e}")
            return self._try_load_backup(save_path)
        except KeyError as e:
            logger.warning(f"Invalid save format for {username}, missing key: {e}")
            return self._try_load_backup(save_path)
        except TypeError as e:
            logger.warning(f"Type error loading {username}: {e}")
            return self._try_load_backup(save_path)

    def _try_load_backup(self, save_path: Path) -> Optional[PlayerStats]:
        """Attempt to load from backup file."""
        backup_path = save_path.with_suffix('.bak')

        if not backup_path.exists():
            logger.debug("No backup file available")
            return None

        logger.info("Attempting to load from backup...")

        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            player_data = save_data['player']
            player = PlayerStats(**player_data)

            self.current_player = player
            logger.info("Successfully loaded from backup")

            # Restore backup as main save
            shutil.copy(backup_path, save_path)

            return player
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Backup also corrupted: {e}")
            return None

    def create_new_player(self, username: str) -> PlayerStats:
        """Create a new player with default stats."""
        player = PlayerStats(username=username)
        self.current_player = player
        self.save_progress(player)
        logger.info(f"New player created: {username}")
        return player

    def list_saved_players(self) -> List[str]:
        """List all saved player usernames."""
        players = []
        for save_file in self.save_dir.glob("*.json"):
            if not save_file.name.endswith(('.tmp', '.bak')):
                players.append(save_file.stem)
        return sorted(players)

    def player_exists(self, username: str) -> bool:
        """Check if a save file exists for the username."""
        save_path = self.save_dir / f"{username}.json"
        return save_path.exists()

    def delete_save(self, username: str) -> bool:
        """Delete a player's save file."""
        save_path = self.save_dir / f"{username}.json"
        backup_path = save_path.with_suffix('.bak')

        try:
            if save_path.exists():
                save_path.unlink()
            if backup_path.exists():
                backup_path.unlink()
            logger.info(f"Save deleted for player: {username}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied deleting save: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error deleting save: {e}")
            return False
