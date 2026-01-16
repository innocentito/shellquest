# ShellQuest - Quick Start Guide

## Installation

```bash
cd ~/shellquest
./install.sh
```

Or manually:
```bash
pip3 install rich pyyaml click prompt-toolkit
pip3 install -e .
```

## Running the Game

```bash
# If installed via install.sh
shellquest

# Or directly
python3 -m shellquest

# Or from the directory
cd ~/shellquest
python3 -m shellquest
```

## How to Play

1. **Create or Select Player**: First time you'll create a username
2. **Choose Quiz Mode**:
   - Essential Commands: Learn the basics (cd, ls, pwd, grep, etc.)
   - Advanced Commands: Master advanced tools (coming soon!)
3. **Answer Questions**:
   - Multiple choice: Select A, B, C, or D
   - Fill in the blank: Type the answer
   - Other types: Follow the prompts
4. **Commands During Quiz**:
   - `H` - Get a hint (reduces points)
   - `S` - Skip question
   - `Q` - Quit to menu
5. **Level Up**: Earn XP, unlock achievements, track your progress!

## Features

- **Gamification**: XP, levels, streaks, achievements
- **Smart Learning**: Questions adapt to your weak areas
- **Beautiful UI**: Modern terminal interface with colors
- **Progress Tracking**: Your progress is automatically saved
- **Multiple Question Types**: Multiple choice, fill-in-blank, fix-the-error, and more

## Commands Database

Currently includes 15 essential shell commands:
- Navigation: cd, pwd
- File Operations: ls, cp, mv, rm, touch, mkdir
- Text Tools: cat, grep, head, tail, echo
- Help: man
- Permissions: chmod
- Search: find

More commands coming soon!

## Tips

- Practice regularly to maintain your streak 🔥
- Check your progress to see weak areas
- Read explanations carefully to learn
- Try to answer quickly for speed bonuses

## Troubleshooting

**Import Error**: Make sure you're in the shellquest directory or have installed it
**Missing Dependencies**: Run `pip3 install -r requirements.txt`
**Save Issues**: Check ~/.shellquest/saves/ directory exists

## Have Fun!

Master those shell commands and become a terminal wizard! 🧙‍♂️
