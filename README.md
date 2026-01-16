# 🚀 ShellQuest

Ein wunderschönes, feature-reiches Terminal-Lernspiel zum Meistern von bash/zsh Commands!

## ✨ Features

### 🎮 Gamification
- **XP & Leveling System**: Verdiene Experience Points und steige in Leveln auf
- **Streak System**: Baue Streaks auf für Bonus-Punkte (max 3x Multiplikator!)
- **15+ Achievements**: Schalte Erfolge frei (Common, Rare, Epic, Legendary)
- **Smart Difficulty**: Fragen passen sich deinen Schwächen an

### 🎨 Schönes Terminal-UI
- Moderne, farbenfrohe Benutzeroberfläche mit Rich Library
- Inspiriert von Gemini CLI und modernen Terminal-Tools
- Flicker-free rendering für smooth experience
- Animierte XP-Gewinne und Achievement-Unlocks

### 📚 Umfangreiche Command-Datenbank
- **15 Essential Commands**: cd, ls, pwd, grep, find, cp, mv, rm, cat, chmod, echo, man, mkdir, touch, head, tail
- **40+ Questions**: Verschiedene Frage-Typen
- **Multiple Question Types**:
  - Multiple Choice
  - Fill in the Blank
  - Fix the Error
  - Command Builder
  - What Does It Do

### 💾 Progress Tracking
- Automatisches Speichern deines Fortschritts
- Detaillierte Statistiken und Analytics
- Command-spezifische Mastery-Tracking
- Session-Summary nach jedem Quiz

## 🚀 Installation

### Schnellinstallation
```bash
cd ~/shellquest
./install.sh
```

### Manuelle Installation
```bash
cd ~/shellquest
pip3 install rich pyyaml click prompt-toolkit
pip3 install -e .
```

## 🎮 Spielen

```bash
# Nach Installation
shellquest

# Oder direkt
python3 -m shellquest

# Aus dem Verzeichnis
cd ~/shellquest
python3 -m shellquest
```

## 📖 Wie man spielt

### 1. Player erstellen/auswählen
Beim ersten Start erstellst du einen Usernamen. Danach kannst du zwischen gespeicherten Spielern wählen.

### 2. Quiz-Modus wählen
- **Essential Commands**: Lerne die Basics (cd, ls, pwd, grep, etc.)
- **Advanced Commands**: Für Fortgeschrittene (coming soon!)

### 3. Fragen beantworten
- Bei Multiple Choice: Wähle A, B, C oder D
- Bei Fill-in-the-blank: Tippe die Antwort
- Bei anderen Typen: Folge den Anweisungen

### 4. Commands während des Quiz
- `H` - Hint anzeigen (reduziert Punkte um 50%)
- `S` - Frage überspringen
- `Q` - Zurück zum Hauptmenü

### 5. Level Up!
- Verdiene XP für richtige Antworten
- Baue Streaks auf für Bonus-Punkte
- Schalte Achievements frei
- Tracke deinen Fortschritt

## 🏆 Achievement System

Schalte 15+ Achievements frei:
- **First Steps** (Common): Erste richtige Antwort
- **Streak Starter** (Common): 3er Streak
- **Streak Master** (Rare): 10er Streak
- **Unstoppable** (Epic): 20er Streak
- **Night Owl** (Uncommon): Spiele zwischen 00:00 - 04:00
- **Essential Expert** (Epic): Meistere alle Essential Commands
- Und viele mehr...

## 📊 XP & Leveling

### XP-Berechnung
```
Total XP = Base Points × Difficulty × Streak Bonus × Speed Bonus × Hint Penalty

- Base Points: 10-25 je nach Frage
- Difficulty: 1.0 (Essential) oder 1.5 (Advanced)
- Streak Bonus: 1.0 - 3.0 (max bei 10+ Streak)
- Speed Bonus: 1.5 (< 5s), 1.2 (< 10s), 1.0 (sonst)
- Hint Penalty: 0.5 wenn Hint benutzt, 1.0 sonst
```

### Level Progression
```
Level = √(XP / 100)

Level 1: 100 XP
Level 2: 400 XP
Level 3: 900 XP
Level 4: 1600 XP
Level 5: 2500 XP
...
```

## 🎯 Question Types

### Multiple Choice
Wähle die richtige Antwort aus 4 Optionen.

### Fill in the Blank
Ergänze den fehlenden Teil des Commands.

### Fix the Error
Korrigiere einen fehlerhaften Command.

### Command Builder
Baue einen Command aus der Beschreibung.

### What Does It Do
Erkläre was ein Command macht.

## 📁 Projekt-Struktur

```
shellquest/
├── shellquest/              # Main package
│   ├── core/               # Game logic
│   │   ├── game_engine.py  # Main orchestrator
│   │   ├── quiz_engine.py  # Question selection
│   │   ├── scoring_system.py # XP & levels
│   │   └── state_manager.py # Save/load
│   ├── models/             # Data models
│   │   ├── command.py
│   │   ├── question.py
│   │   ├── player.py
│   │   └── achievement.py
│   ├── ui/                 # User interface
│   │   ├── theme.py        # Colors & styles
│   │   └── components.py   # UI components
│   ├── data/              # Data loading
│   │   ├── loader.py
│   │   └── validator.py
│   └── utils/             # Utilities
├── data/                   # Game data (YAML)
│   ├── commands/
│   │   └── essential.yaml
│   ├── questions/
│   │   └── essential_questions.yaml
│   └── achievements.yaml
├── saves/                  # (auto-created)
└── tests/                  # Unit tests
```

## 🎨 UI Preview

```
╭────────────────────────────────────────╮
│         🚀 ShellQuest v1.0             │
│      Master Bash/Zsh Like a Pro        │
╰────────────────────────────────────────╯

╭─ Player Stats ─────────────────────────╮
│ CmdMaster        Level: 5 ⭐           │
│ XP: 625/900  [███████░░░] 69%         │
│ Streak: 3 🔥  Accuracy: 85%            │
╰────────────────────────────────────────╯

╭─ Main Menu ────────────────────────────╮
│  1  🎯 Quick Quiz (Essential)          │
│  2  🚀 Quick Quiz (Advanced)           │
│  3  📊 View Progress                   │
│  4  👋 Quit                            │
╰────────────────────────────────────────╯
```

## 💡 Tipps

1. **Regelmäßig spielen**: Halte deine Streak am Leben! 🔥
2. **Schnell antworten**: Speed Bonus für < 10 Sekunden
3. **Hints sparen**: 50% Punktabzug, nur wenn nötig
4. **Progress checken**: Sieh deine schwachen Bereiche
5. **Erklärungen lesen**: Lerne aus deinen Fehlern

## 🔧 Technische Details

### Dependencies
- **Rich** (>=13.0.0): Terminal UI
- **PyYAML** (>=6.0): Data loading
- **Click** (>=8.0.0): CLI framework
- **Prompt Toolkit** (>=3.0.0): Advanced prompts

### Requirements
- Python 3.8+
- Terminal mit Farbunterstützung
- ~5 MB Speicherplatz

### Save Location
Fortschritt wird gespeichert in: `~/.shellquest/saves/`

## 🐛 Troubleshooting

**Import Error**
```bash
cd ~/shellquest
pip3 install -e .
```

**Missing Dependencies**
```bash
pip3 install -r requirements.txt
```

**Permission Denied**
```bash
chmod +x install.sh
```

**Save Issues**
```bash
# Save directory wird automatisch erstellt
# Bei Problemen manuell erstellen:
mkdir -p ~/.shellquest/saves
```

## 🎯 Roadmap

### v1.1 (Geplant)
- [ ] Advanced Commands Database (50+ Commands)
- [ ] More Question Types (Output Prediction)
- [ ] Command Reference Browser
- [ ] Export Progress to Markdown

### v1.2 (Geplant)
- [ ] Daily Challenges
- [ ] Timed Challenge Mode
- [ ] Leaderboard (local)
- [ ] Detailed Learning Analytics

### v2.0 (Future)
- [ ] Interactive Terminal Simulator
- [ ] Custom Question Packs
- [ ] Multiplayer Mode
- [ ] Achievement Showcase (export)

## 📄 License

MIT License - feel free to use, modify, and distribute!

## 🙏 Credits

Erstellt mit:
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- Python & Love ❤️

## 🎉 Have Fun!

Viel Spaß beim Lernen! Werde zum Shell-Command Master! 🧙‍♂️

---

**Made with Claude Code** 🤖
