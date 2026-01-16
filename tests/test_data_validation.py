"""Tests for data file validation - ensures all YAML files are complete and valid."""

import pytest
import yaml
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"


class TestCommandsData:
    """Validate commands YAML files."""

    def test_essential_commands_exists(self):
        """Test essential commands file exists."""
        path = DATA_DIR / "commands" / "essential.yaml"
        assert path.exists(), "essential.yaml not found"

    def test_essential_commands_valid_yaml(self):
        """Test essential commands is valid YAML."""
        path = DATA_DIR / "commands" / "essential.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert 'commands' in data

    def test_essential_commands_have_required_fields(self):
        """Test all essential commands have required fields."""
        path = DATA_DIR / "commands" / "essential.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        required_fields = ['name', 'category', 'difficulty', 'syntax', 'description']

        for cmd in data['commands']:
            for field in required_fields:
                assert field in cmd, f"Command {cmd.get('name', 'unknown')} missing field: {field}"

    def test_essential_commands_count(self):
        """Test we have a reasonable number of essential commands."""
        path = DATA_DIR / "commands" / "essential.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        count = len(data['commands'])
        assert count >= 10, f"Expected at least 10 essential commands, got {count}"


class TestQuestionsData:
    """Validate questions YAML files."""

    def test_essential_questions_exists(self):
        """Test essential questions file exists."""
        path = DATA_DIR / "questions" / "essential_questions.yaml"
        assert path.exists(), "essential_questions.yaml not found"

    def test_essential_questions_valid_yaml(self):
        """Test essential questions is valid YAML."""
        path = DATA_DIR / "questions" / "essential_questions.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert 'questions' in data

    def test_essential_questions_have_required_fields(self):
        """Test all questions have required fields."""
        path = DATA_DIR / "questions" / "essential_questions.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        required_fields = ['id', 'type', 'command', 'difficulty', 'question_text',
                          'correct_answer', 'explanation', 'points']

        for q in data['questions']:
            for field in required_fields:
                assert field in q, f"Question {q.get('id', 'unknown')} missing field: {field}"

    def test_questions_have_unique_ids(self):
        """Test all question IDs are unique."""
        path = DATA_DIR / "questions" / "essential_questions.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        ids = [q['id'] for q in data['questions']]
        assert len(ids) == len(set(ids)), "Duplicate question IDs found"

    def test_multiple_choice_have_options(self):
        """Test multiple choice questions have options."""
        path = DATA_DIR / "questions" / "essential_questions.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for q in data['questions']:
            if q['type'] == 'multiple_choice':
                assert 'options' in q, f"MC question {q['id']} missing options"
                assert len(q['options']) >= 2, f"MC question {q['id']} needs at least 2 options"

    def test_questions_count(self):
        """Test we have enough questions."""
        path = DATA_DIR / "questions" / "essential_questions.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        count = len(data['questions'])
        assert count >= 50, f"Expected at least 50 questions, got {count}"


class TestStoryData:
    """Validate story mode YAML files."""

    def test_chapters_file_exists(self):
        """Test chapters file exists."""
        path = DATA_DIR / "story" / "chapters.yaml"
        assert path.exists(), "chapters.yaml not found"

    def test_chapters_valid_yaml(self):
        """Test chapters is valid YAML."""
        path = DATA_DIR / "story" / "chapters.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert 'chapters' in data

    def test_chapters_have_required_fields(self):
        """Test all chapters have required fields."""
        path = DATA_DIR / "story" / "chapters.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        required_fields = ['id', 'name', 'description', 'icon', 'commands', 'levels']

        for chapter in data['chapters']:
            for field in required_fields:
                assert field in chapter, f"Chapter {chapter.get('id', 'unknown')} missing field: {field}"

    def test_levels_have_required_fields(self):
        """Test all levels have required fields."""
        path = DATA_DIR / "story" / "chapters.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        required_fields = ['id', 'name', 'description', 'story', 'commands',
                          'questions_needed', 'xp_reward']

        for chapter in data['chapters']:
            for level in chapter['levels']:
                for field in required_fields:
                    assert field in level, f"Level {level.get('id', 'unknown')} missing field: {field}"

    def test_chapters_count(self):
        """Test we have multiple chapters."""
        path = DATA_DIR / "story" / "chapters.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        count = len(data['chapters'])
        assert count >= 3, f"Expected at least 3 chapters, got {count}"

    def test_unlock_requirements_valid(self):
        """Test unlock requirements reference existing chapters."""
        path = DATA_DIR / "story" / "chapters.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        chapter_ids = {ch['id'] for ch in data['chapters']}

        for chapter in data['chapters']:
            req = chapter.get('unlock_requirement')
            if req:
                assert req in chapter_ids, f"Chapter {chapter['id']} requires non-existent chapter: {req}"


class TestMysteryData:
    """Validate mystery mode YAML files."""

    def test_mystery_cases_exist(self):
        """Test mystery case files exist."""
        mystery_dir = DATA_DIR / "mystery"
        cases = list(mystery_dir.glob("case_*.yaml"))
        assert len(cases) >= 1, "No mystery case files found"

    def test_all_cases_valid_yaml(self):
        """Test all mystery cases are valid YAML."""
        mystery_dir = DATA_DIR / "mystery"

        for case_file in mystery_dir.glob("case_*.yaml"):
            with open(case_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert data is not None, f"{case_file.name} is empty"
            assert 'case' in data, f"{case_file.name} missing 'case' section"

    def test_cases_have_required_fields(self):
        """Test all mystery cases have required fields."""
        mystery_dir = DATA_DIR / "mystery"

        case_required = ['id', 'title', 'subtitle', 'difficulty', 'intro', 'setting']

        for case_file in mystery_dir.glob("case_*.yaml"):
            with open(case_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for field in case_required:
                assert field in data['case'], f"{case_file.name} missing case field: {field}"

    def test_cases_have_suspects(self):
        """Test all mystery cases have suspects."""
        mystery_dir = DATA_DIR / "mystery"

        suspect_required = ['id', 'name', 'role', 'description', 'alibi', 'motive']

        for case_file in mystery_dir.glob("case_*.yaml"):
            with open(case_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert 'suspects' in data, f"{case_file.name} missing suspects"
            assert len(data['suspects']) >= 2, f"{case_file.name} needs at least 2 suspects"

            for suspect in data['suspects']:
                for field in suspect_required:
                    assert field in suspect, f"{case_file.name} suspect missing field: {field}"

    def test_cases_have_scenes(self):
        """Test all mystery cases have scenes."""
        mystery_dir = DATA_DIR / "mystery"

        scene_required = ['id', 'title', 'location', 'narrative', 'objective', 'challenges']

        for case_file in mystery_dir.glob("case_*.yaml"):
            with open(case_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert 'scenes' in data, f"{case_file.name} missing scenes"
            assert len(data['scenes']) >= 1, f"{case_file.name} needs at least 1 scene"

            for scene in data['scenes']:
                for field in scene_required:
                    assert field in scene, f"{case_file.name} scene missing field: {field}"

    def test_cases_have_conclusions(self):
        """Test all mystery cases have conclusions."""
        mystery_dir = DATA_DIR / "mystery"

        for case_file in mystery_dir.glob("case_*.yaml"):
            with open(case_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert 'conclusion' in data, f"{case_file.name} missing conclusion"
            assert 'success' in data['conclusion'], f"{case_file.name} missing success conclusion"
            assert 'failure' in data['conclusion'], f"{case_file.name} missing failure conclusion"

    def test_cases_have_rewards(self):
        """Test all mystery cases have rewards."""
        mystery_dir = DATA_DIR / "mystery"

        for case_file in mystery_dir.glob("case_*.yaml"):
            with open(case_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert 'rewards' in data, f"{case_file.name} missing rewards"
            assert 'xp' in data['rewards'], f"{case_file.name} missing xp reward"


class TestAchievementsData:
    """Validate achievements YAML file."""

    def test_achievements_file_exists(self):
        """Test achievements file exists."""
        path = DATA_DIR / "achievements.yaml"
        assert path.exists(), "achievements.yaml not found"

    def test_achievements_valid_yaml(self):
        """Test achievements is valid YAML."""
        path = DATA_DIR / "achievements.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert 'achievements' in data

    def test_achievements_have_required_fields(self):
        """Test all achievements have required fields."""
        path = DATA_DIR / "achievements.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        required_fields = ['id', 'name', 'description', 'icon', 'requirement', 'rarity', 'xp_reward']

        for ach in data['achievements']:
            for field in required_fields:
                assert field in ach, f"Achievement {ach.get('id', 'unknown')} missing field: {field}"

    def test_achievements_have_unique_ids(self):
        """Test all achievement IDs are unique."""
        path = DATA_DIR / "achievements.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        ids = [a['id'] for a in data['achievements']]
        assert len(ids) == len(set(ids)), "Duplicate achievement IDs found"

    def test_achievements_valid_rarity(self):
        """Test all achievements have valid rarity."""
        path = DATA_DIR / "achievements.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        valid_rarities = {'common', 'uncommon', 'rare', 'epic', 'legendary'}

        for ach in data['achievements']:
            assert ach['rarity'] in valid_rarities, f"Achievement {ach['id']} has invalid rarity: {ach['rarity']}"

    def test_achievements_count(self):
        """Test we have enough achievements."""
        path = DATA_DIR / "achievements.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        count = len(data['achievements'])
        assert count >= 5, f"Expected at least 5 achievements, got {count}"


class TestDataIntegrity:
    """Cross-file data integrity tests."""

    def test_question_commands_exist(self):
        """Test all question commands reference existing commands."""
        # Load ALL commands (essential + advanced)
        command_names = set()

        for difficulty in ["essential", "advanced"]:
            cmd_path = DATA_DIR / "commands" / f"{difficulty}.yaml"
            if cmd_path.exists():
                with open(cmd_path, 'r', encoding='utf-8') as f:
                    cmd_data = yaml.safe_load(f)
                if cmd_data and 'commands' in cmd_data:
                    command_names.update(cmd['name'] for cmd in cmd_data['commands'])

        # Check ALL questions
        for difficulty in ["essential", "advanced"]:
            q_path = DATA_DIR / "questions" / f"{difficulty}_questions.yaml"
            if q_path.exists():
                with open(q_path, 'r', encoding='utf-8') as f:
                    q_data = yaml.safe_load(f)
                if q_data and 'questions' in q_data:
                    for q in q_data['questions']:
                        assert q['command'] in command_names, f"Question {q['id']} references unknown command: {q['command']}"

    def test_story_commands_exist(self):
        """Test all story commands reference existing commands."""
        # Load ALL commands
        command_names = set()

        for difficulty in ["essential", "advanced"]:
            cmd_path = DATA_DIR / "commands" / f"{difficulty}.yaml"
            if cmd_path.exists():
                with open(cmd_path, 'r', encoding='utf-8') as f:
                    cmd_data = yaml.safe_load(f)
                if cmd_data and 'commands' in cmd_data:
                    command_names.update(cmd['name'] for cmd in cmd_data['commands'])

        # Check story
        story_path = DATA_DIR / "story" / "chapters.yaml"
        with open(story_path, 'r', encoding='utf-8') as f:
            story_data = yaml.safe_load(f)

        for chapter in story_data['chapters']:
            for cmd in chapter['commands']:
                assert cmd in command_names, f"Chapter {chapter['id']} references unknown command: {cmd}"

            for level in chapter['levels']:
                for cmd in level['commands']:
                    assert cmd in command_names, f"Level {level['id']} references unknown command: {cmd}"
