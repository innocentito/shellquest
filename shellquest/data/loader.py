"""Data loader for YAML command and question files."""

import yaml
from pathlib import Path
from typing import List

from ..models.command import Command, CommandOption, CommandExample
from ..models.question import Question
from ..models.achievement import Achievement
from ..utils import logger, DataLoadError


class DataLoader:
    """Loads game data from YAML files."""

    def __init__(self, data_dir: Path = None):
        """Initialize data loader with data directory path."""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)

        # Initialize cache storage
        self._commands_cache = {}
        self._questions_cache = {}
        self._achievements_cache = None

        logger.debug(f"DataLoader initialized with data_dir: {self.data_dir}")

    def load_commands(self, difficulty: str = "essential") -> List[Command]:
        """Load commands from YAML file."""
        # Check cache first
        if difficulty in self._commands_cache:
            logger.debug(f"Returning cached {difficulty} commands")
            return self._commands_cache[difficulty]

        file_path = self.data_dir / "commands" / f"{difficulty}.yaml"

        if not file_path.exists():
            logger.warning(f"Commands file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.warning(f"Empty commands file: {file_path}")
                return []

            commands = []
            for cmd_data in data.get('commands', []):
                try:
                    options = [
                        CommandOption(opt['name'], opt['description'])
                        for opt in cmd_data.get('common_options', [])
                    ]

                    examples = [
                        CommandExample(ex['command'], ex['explanation'])
                        for ex in cmd_data.get('examples', [])
                    ]

                    command = Command(
                        name=cmd_data['name'],
                        category=cmd_data['category'],
                        difficulty=cmd_data['difficulty'],
                        syntax=cmd_data['syntax'],
                        description=cmd_data['description'],
                        common_options=options,
                        examples=examples,
                        tags=cmd_data.get('tags', []),
                        related_commands=cmd_data.get('related_commands', []),
                        tips=cmd_data.get('tips', [])
                    )
                    commands.append(command)
                except KeyError as e:
                    logger.warning(f"Skipping command with missing field {e}: {cmd_data.get('name', 'unknown')}")
                    continue

            # Store in cache
            self._commands_cache[difficulty] = commands
            logger.info(f"Loaded {len(commands)} {difficulty} commands")
            return commands

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return []
        except PermissionError as e:
            logger.error(f"Permission denied reading {file_path}: {e}")
            return []

    def load_questions(self, difficulty: str = "essential") -> List[Question]:
        """Load questions from YAML file."""
        # Check cache first
        if difficulty in self._questions_cache:
            logger.debug(f"Returning cached {difficulty} questions")
            return self._questions_cache[difficulty]

        file_path = self.data_dir / "questions" / f"{difficulty}_questions.yaml"

        if not file_path.exists():
            logger.warning(f"Questions file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.warning(f"Empty questions file: {file_path}")
                return []

            questions = []
            for q_data in data.get('questions', []):
                try:
                    question = Question(
                        id=q_data['id'],
                        type=q_data['type'],
                        command=q_data['command'],
                        difficulty=q_data['difficulty'],
                        question_text=q_data['question_text'],
                        correct_answer=q_data['correct_answer'],
                        explanation=q_data['explanation'],
                        points=q_data['points'],
                        options=q_data.get('options'),
                        hint=q_data.get('hint'),
                        premium_hint=q_data.get('premium_hint')
                    )
                    questions.append(question)
                except KeyError as e:
                    logger.warning(f"Skipping question with missing field {e}: {q_data.get('id', 'unknown')}")
                    continue

            # Store in cache
            self._questions_cache[difficulty] = questions
            logger.info(f"Loaded {len(questions)} {difficulty} questions")
            return questions

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return []
        except PermissionError as e:
            logger.error(f"Permission denied reading {file_path}: {e}")
            return []

    def load_achievements(self) -> List[Achievement]:
        """Load achievements from YAML file."""
        # Check cache first
        if self._achievements_cache is not None:
            logger.debug("Returning cached achievements")
            return self._achievements_cache

        file_path = self.data_dir / "achievements.yaml"

        if not file_path.exists():
            logger.warning(f"Achievements file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.warning(f"Empty achievements file: {file_path}")
                return []

            achievements = []
            for ach_data in data.get('achievements', []):
                try:
                    achievement = Achievement(
                        id=ach_data['id'],
                        name=ach_data['name'],
                        description=ach_data['description'],
                        icon=ach_data['icon'],
                        requirement=ach_data['requirement'],
                        rarity=ach_data['rarity'],
                        xp_reward=ach_data['xp_reward'],
                        credit_reward=ach_data.get('credit_reward', 0)
                    )
                    achievements.append(achievement)
                except KeyError as e:
                    logger.warning(f"Skipping achievement with missing field {e}: {ach_data.get('id', 'unknown')}")
                    continue

            # Store in cache
            self._achievements_cache = achievements
            logger.info(f"Loaded {len(achievements)} achievements")
            return achievements

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return []
        except PermissionError as e:
            logger.error(f"Permission denied reading {file_path}: {e}")
            return []

    def load_all_commands(self) -> List[Command]:
        """Load both essential and advanced commands."""
        essential = self.load_commands("essential")
        advanced = self.load_commands("advanced")
        return essential + advanced

    def load_all_questions(self) -> List[Question]:
        """Load both essential and advanced questions."""
        essential = self.load_questions("essential")
        advanced = self.load_questions("advanced")
        return essential + advanced

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._commands_cache = {}
        self._questions_cache = {}
        self._achievements_cache = None
        logger.info("Cache cleared")
