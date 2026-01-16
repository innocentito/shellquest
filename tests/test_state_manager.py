"""Unit tests for the StateManager."""

import pytest
import json
import tempfile
from pathlib import Path
from shellquest.core.state_manager import StateManager
from shellquest.models.player import PlayerStats


@pytest.fixture
def temp_save_dir(tmp_path):
    """Create a temporary save directory."""
    return tmp_path / "saves"


@pytest.fixture
def state_manager(temp_save_dir):
    """Create a StateManager with temporary directory."""
    manager = StateManager()
    manager.save_dir = temp_save_dir
    temp_save_dir.mkdir(parents=True, exist_ok=True)
    return manager


@pytest.fixture
def sample_player():
    """Create a sample player."""
    player = PlayerStats(username="TestPlayer")
    player.xp = 500
    player.level = 3
    player.credits = 150
    player.streak = 5
    return player


class TestSaveProgress:
    """Tests for save_progress method."""

    def test_save_creates_file(self, state_manager, sample_player):
        """Test that save creates a JSON file."""
        result = state_manager.save_progress(sample_player)
        assert result is True

        save_path = state_manager.save_dir / "TestPlayer.json"
        assert save_path.exists()

    def test_save_contains_correct_data(self, state_manager, sample_player):
        """Test that saved data is correct."""
        state_manager.save_progress(sample_player)

        save_path = state_manager.save_dir / "TestPlayer.json"
        with open(save_path, 'r') as f:
            data = json.load(f)

        assert data['player']['username'] == "TestPlayer"
        assert data['player']['xp'] == 500
        assert data['player']['level'] == 3
        assert data['player']['credits'] == 150

    def test_save_creates_backup(self, state_manager, sample_player):
        """Test that saving twice creates a backup."""
        state_manager.save_progress(sample_player)
        sample_player.xp = 1000
        state_manager.save_progress(sample_player)

        backup_path = state_manager.save_dir / "TestPlayer.bak"
        assert backup_path.exists()

    def test_save_is_atomic(self, state_manager, sample_player):
        """Test that no temp file remains after save."""
        state_manager.save_progress(sample_player)

        temp_path = state_manager.save_dir / "TestPlayer.tmp"
        assert not temp_path.exists()


class TestLoadProgress:
    """Tests for load_progress method."""

    def test_load_existing_player(self, state_manager, sample_player):
        """Test loading an existing player."""
        state_manager.save_progress(sample_player)

        loaded = state_manager.load_progress("TestPlayer")
        assert loaded is not None
        assert loaded.username == "TestPlayer"
        assert loaded.xp == 500
        assert loaded.credits == 150

    def test_load_nonexistent_player(self, state_manager):
        """Test loading a player that doesn't exist."""
        loaded = state_manager.load_progress("DoesNotExist")
        assert loaded is None

    def test_load_sets_current_player(self, state_manager, sample_player):
        """Test that load sets current_player."""
        state_manager.save_progress(sample_player)
        state_manager.load_progress("TestPlayer")

        assert state_manager.current_player is not None
        assert state_manager.current_player.username == "TestPlayer"

    def test_load_corrupted_file_tries_backup(self, state_manager, sample_player):
        """Test that corrupted file falls back to backup."""
        # Save valid data first
        state_manager.save_progress(sample_player)

        # Save again to create backup
        sample_player.xp = 1000
        state_manager.save_progress(sample_player)

        # Corrupt main file
        save_path = state_manager.save_dir / "TestPlayer.json"
        with open(save_path, 'w') as f:
            f.write("not valid json{{{")

        # Should load from backup
        loaded = state_manager.load_progress("TestPlayer")
        assert loaded is not None
        # Backup has original 500 XP
        assert loaded.xp == 500


class TestCreateNewPlayer:
    """Tests for create_new_player method."""

    def test_create_returns_player(self, state_manager):
        """Test that create returns a PlayerStats."""
        player = state_manager.create_new_player("NewPlayer")
        assert isinstance(player, PlayerStats)
        assert player.username == "NewPlayer"

    def test_create_saves_player(self, state_manager):
        """Test that create saves the player."""
        state_manager.create_new_player("NewPlayer")

        save_path = state_manager.save_dir / "NewPlayer.json"
        assert save_path.exists()

    def test_create_sets_current_player(self, state_manager):
        """Test that create sets current_player."""
        state_manager.create_new_player("NewPlayer")
        assert state_manager.current_player.username == "NewPlayer"

    def test_new_player_has_defaults(self, state_manager):
        """Test that new player has default values."""
        player = state_manager.create_new_player("NewPlayer")
        assert player.level == 1
        assert player.xp == 0
        assert player.credits == 100


class TestListSavedPlayers:
    """Tests for list_saved_players method."""

    def test_list_empty_directory(self, state_manager):
        """Test listing with no saves."""
        players = state_manager.list_saved_players()
        assert players == []

    def test_list_multiple_players(self, state_manager):
        """Test listing multiple players."""
        state_manager.create_new_player("Alice")
        state_manager.create_new_player("Bob")
        state_manager.create_new_player("Charlie")

        players = state_manager.list_saved_players()
        assert len(players) == 3
        assert "Alice" in players
        assert "Bob" in players
        assert "Charlie" in players

    def test_list_excludes_temp_and_backup(self, state_manager, sample_player):
        """Test that temp and backup files are excluded."""
        state_manager.save_progress(sample_player)
        sample_player.xp = 1000
        state_manager.save_progress(sample_player)

        # Create a temp file manually
        temp_path = state_manager.save_dir / "TestPlayer.tmp"
        temp_path.touch()

        players = state_manager.list_saved_players()
        assert len(players) == 1
        assert players[0] == "TestPlayer"

    def test_list_is_sorted(self, state_manager):
        """Test that player list is sorted."""
        state_manager.create_new_player("Zoe")
        state_manager.create_new_player("Alice")
        state_manager.create_new_player("Mike")

        players = state_manager.list_saved_players()
        assert players == ["Alice", "Mike", "Zoe"]


class TestPlayerExists:
    """Tests for player_exists method."""

    def test_exists_true(self, state_manager, sample_player):
        """Test player_exists returns True for existing player."""
        state_manager.save_progress(sample_player)
        assert state_manager.player_exists("TestPlayer") is True

    def test_exists_false(self, state_manager):
        """Test player_exists returns False for nonexistent player."""
        assert state_manager.player_exists("NoSuchPlayer") is False


class TestDeleteSave:
    """Tests for delete_save method."""

    def test_delete_removes_file(self, state_manager, sample_player):
        """Test that delete removes the save file."""
        state_manager.save_progress(sample_player)
        save_path = state_manager.save_dir / "TestPlayer.json"
        assert save_path.exists()

        result = state_manager.delete_save("TestPlayer")
        assert result is True
        assert not save_path.exists()

    def test_delete_removes_backup(self, state_manager, sample_player):
        """Test that delete also removes backup."""
        state_manager.save_progress(sample_player)
        sample_player.xp = 1000
        state_manager.save_progress(sample_player)

        backup_path = state_manager.save_dir / "TestPlayer.bak"
        assert backup_path.exists()

        state_manager.delete_save("TestPlayer")
        assert not backup_path.exists()

    def test_delete_nonexistent_succeeds(self, state_manager):
        """Test deleting nonexistent player succeeds."""
        result = state_manager.delete_save("NoSuchPlayer")
        assert result is True


class TestDataIntegrity:
    """Tests for data integrity after save/load cycles."""

    def test_complex_player_data_preserved(self, state_manager):
        """Test that complex player data is preserved."""
        player = PlayerStats(username="Complex")
        player.xp = 5000
        player.level = 8
        player.streak = 15
        player.best_streak = 20
        player.credits = 500
        player.unlocked_achievements = ["ach1", "ach2"]
        player.command_stats = {"ls": {"correct": 10, "total": 12}}
        player.essential_progress = {"ls": True, "cd": True}
        player.solved_mysteries = ["case1"]

        state_manager.save_progress(player)
        loaded = state_manager.load_progress("Complex")

        assert loaded.xp == 5000
        assert loaded.level == 8
        assert loaded.streak == 15
        assert loaded.best_streak == 20
        assert loaded.credits == 500
        assert loaded.unlocked_achievements == ["ach1", "ach2"]
        assert loaded.command_stats["ls"]["correct"] == 10
        assert loaded.essential_progress["ls"] is True
        assert "case1" in loaded.solved_mysteries
