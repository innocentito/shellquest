# ShellQuest Comprehensive Test Scenarios

## Table of Contents
1. [Quick Play Mode Tests](#1-quick-play-mode-tests)
2. [Training Mode Tests](#2-training-mode-tests)
3. [Practice Mode Tests](#3-practice-mode-tests)
4. [Speed Round Tests](#4-speed-round-tests)
5. [Story Mode Tests](#5-story-mode-tests)
6. [Mystery Mode Tests](#6-mystery-mode-tests)
7. [Battle Mode Tests](#7-battle-mode-tests)
8. [Cross-Module Integration Tests](#8-cross-module-integration-tests)
9. [Currently Untestable Components](#9-currently-untestable-components)

---

## 1. Quick Play Mode Tests

### 1.1 Happy Path Tests

```
TEST: QP-HP-001 - Complete 10-Question Quick Quiz Successfully
STEPS:
  1. Start ShellQuest
  2. Create new player or select existing player
  3. Select "Quick Play" from main menu
  4. Select "Quick Quiz (10 Questions)"
  5. Answer all 10 questions correctly
  6. View session summary
EXPECTED:
  - Questions displayed one at a time with options
  - XP awarded for each correct answer (varies by difficulty, speed, streak)
  - Session summary shows 10/10 correct, 100% accuracy
  - XP added to player total
  - Progress saved to ~/.shellquest/saves/{username}.json
EDGE CASES:
  - What if questions pool has fewer than 10 questions?
  - What if all questions have been recently answered (recently_answered list)?
```

```
TEST: QP-HP-002 - Complete Marathon Mode (25 Questions)
STEPS:
  1. Navigate to Quick Play > Marathon
  2. Answer 25 questions with mix of correct/incorrect
  3. Complete session
EXPECTED:
  - All 25 questions presented
  - Streak resets on incorrect answers
  - Streak bonus (up to 3x) applies to XP calculation
  - Session summary reflects actual performance
EDGE CASES:
  - Player runs out of unique questions before 25
  - Very long answer times (>60 seconds per question)
```

```
TEST: QP-HP-003 - Use Hint During Quiz
STEPS:
  1. Start Quick Quiz
  2. Press 'H' to request hint
  3. View hint and answer question
EXPECTED:
  - Hint displayed for current question
  - XP reduced by 50% (hint_mult = 0.5) if hint used
  - Question still counts toward progress
EDGE CASES:
  - Question has no hint defined (hint is None)
  - Multiple hints requested on same question
```

```
TEST: QP-HP-004 - Use Premium Hint
STEPS:
  1. Ensure player has >= 40 credits
  2. Start quiz and press 'P' for premium hint
  3. Verify credit deduction and hint display
EXPECTED:
  - 40 credits deducted from player.credits
  - Premium hint displayed (specific or generic based on question type)
  - hint_used flag set, reducing XP by 50%
EDGE CASES:
  - Player has exactly 40 credits
  - Player has 39 credits (should fail with message)
  - Premium hint is None (should use generic hint)
```

```
TEST: QP-HP-005 - Skip Question
STEPS:
  1. Start quiz
  2. Press 'S' to skip question
EXPECTED:
  - Correct answer revealed
  - No XP awarded
  - Streak reset to 0
  - Question marked as answered incorrectly in command_stats
EDGE CASES:
  - Skipping all questions
  - Skipping last question in session
```

### 1.2 Edge Case Tests

```
TEST: QP-EC-001 - Empty Question Pool
STEPS:
  1. Manually empty questions YAML file
  2. Start Quick Quiz
EXPECTED:
  - "No questions available!" message displayed
  - Return to previous menu after 2 seconds
EDGE CASES:
  - File exists but has no questions
  - File has malformed YAML
```

```
TEST: QP-EC-002 - All Questions Recently Answered
STEPS:
  1. Answer all available questions
  2. Start new session immediately
EXPECTED:
  - Questions still presented (weight *= 0.1 but not blocked)
  - Weighted random selection still works
  - Fallback to random.choice if needed
EDGE CASES:
  - Exactly 50 questions in recently_answered list (max size)
  - Session questions overlap with recent history
```

```
TEST: QP-EC-003 - Maximum Streak Bonus
STEPS:
  1. Answer 10+ questions correctly in a row
EXPECTED:
  - streak_mult caps at 3.0 (streak * 0.2 capped at 3x)
  - Streak counter continues beyond 10
  - best_streak updated if current streak exceeds it
EDGE CASES:
  - Streak of 100+
  - Integer overflow (theoretically impossible in Python)
```

```
TEST: QP-EC-004 - Very Fast Answer (Speed Bonus)
STEPS:
  1. Answer question in under 5 seconds
EXPECTED:
  - speed_mult = 1.5 applied
  - XP calculation: base * diff_mult * streak_mult * 1.5 * hint_mult
EDGE CASES:
  - Answer in exactly 5.0 seconds (should be speed_mult = 1.2)
  - Answer in 0 seconds (automated input)
  - Negative time (clock manipulation)
```

```
TEST: QP-EC-005 - Multiple Choice Answer Formats
STEPS:
  1. Answer with letter (A, B, C, D)
  2. Answer with number (1, 2, 3, 4)
  3. Answer with full option text
EXPECTED:
  - All three formats accepted
  - Case-insensitive matching (a == A)
  - Full option text works for fill_blank questions
EDGE CASES:
  - Answer "5" for a 4-option question
  - Answer "e" for a 4-option question
  - Mixed case in full text answer
```

### 1.3 Negative Tests

```
TEST: QP-NEG-001 - Invalid Answer Input
STEPS:
  1. Enter empty string as answer
  2. Enter special characters only
  3. Enter very long string (1000+ characters)
EXPECTED:
  - Answer validated and marked incorrect if not matching
  - No crashes or exceptions
  - Application continues normally
EDGE CASES:
  - Control characters in answer
  - Unicode characters
  - Newline characters
```

```
TEST: QP-NEG-002 - Quit Mid-Session
STEPS:
  1. Start quiz with 10 questions
  2. Answer 5 questions
  3. Press 'Q' to quit
EXPECTED:
  - Session summary shown for completed questions
  - Progress saved for answered questions
  - Return to main menu
EDGE CASES:
  - Quit on first question
  - Quit on last question
```

```
TEST: QP-NEG-003 - Corrupted Save File
STEPS:
  1. Manually corrupt player JSON file
  2. Try to load player
EXPECTED:
  - Attempt to load from .bak backup file
  - If backup also corrupt, return None
  - Log warning messages
EDGE CASES:
  - Backup file doesn't exist
  - Backup is also corrupted
  - Save file has missing required fields
```

### 1.4 Stress Tests

```
TEST: QP-STR-001 - 100 Consecutive Quizzes
STEPS:
  1. Complete 100 quick quiz sessions back-to-back
EXPECTED:
  - Memory usage remains stable
  - Save file doesn't grow excessively
  - Performance doesn't degrade
  - XP accumulates correctly
EDGE CASES:
  - Disk full during save
  - Memory exhaustion
```

```
TEST: QP-STR-002 - Maximum XP Accumulation
STEPS:
  1. Accumulate 10,000,000+ XP
EXPECTED:
  - Level calculation works correctly (sqrt progression)
  - UI displays large numbers properly
  - JSON serialization handles large integers
EDGE CASES:
  - Level 100+ display
  - Progress percentage calculation with huge XP values
```

---

## 2. Training Mode Tests

### 2.1 Happy Path Tests

```
TEST: TM-HP-001 - Complete Command Training Session
STEPS:
  1. Navigate to Quick Play > Command Training
  2. Select a command with 40+ questions
  3. Answer up to 40 questions
  4. View training summary
EXPECTED:
  - Questions filtered to selected command only
  - Progress bar shows correct/needed ratio
  - Training summary shows accuracy and grade
  - Command mastery icon updates based on performance
EDGE CASES:
  - Command has fewer than 40 questions
  - All questions for command already answered recently
```

```
TEST: TM-HP-002 - Command Mastery Levels
STEPS:
  1. Answer 10+ questions for a command with 90%+ accuracy
  2. Check mastery icon in command training menu
EXPECTED:
  - Mastered (90%+): Green circle icon
  - Learning (60-89%): Yellow circle icon
  - Needs Practice (<60%): Red circle icon
  - Not Started (<5 attempts): White circle icon
EDGE CASES:
  - Exactly 5 questions answered (threshold)
  - Exactly 90% accuracy (edge of mastered)
  - Command with 0 questions answered
```

### 2.2 Edge Case Tests

```
TEST: TM-EC-001 - Command with No Questions
STEPS:
  1. Add a new command to essential.yaml without questions
  2. Try to train on that command
EXPECTED:
  - Command shouldn't appear in training menu
  - Or graceful handling if it does appear
EDGE CASES:
  - Command added mid-session
  - Questions deleted for existing command
```

```
TEST: TM-EC-002 - Training Session Exit Variations
STEPS:
  1. Exit with 'Q' at question 1
  2. Exit at question 20
  3. Complete all questions naturally
EXPECTED:
  - Summary shows only completed questions
  - Progress saved regardless of exit point
  - No data corruption
EDGE CASES:
  - Exit during answer input
  - Application crash during training
```

### 2.3 Negative Tests

```
TEST: TM-NEG-001 - Invalid Category Navigation
STEPS:
  1. Try to select non-existent command index
EXPECTED:
  - Prompt validates choices and rejects invalid input
  - No crash or undefined behavior
EDGE CASES:
  - Input "0" or negative numbers
  - Non-numeric input
```

---

## 3. Practice Mode Tests

### 3.1 Happy Path Tests

```
TEST: PM-HP-001 - Practice Mode Session
STEPS:
  1. Select Practice Mode from play menu
  2. Answer several questions
  3. Exit session
EXPECTED:
  - "Practice Mode" header displayed
  - No XP gained for correct answers (xp_gained = 0)
  - Hints are free (no credit cost for 'H')
  - Session accuracy tracked
EDGE CASES:
  - Very long practice session (100+ questions)
  - Practice mode with premium hints (still costs credits?)
```

```
TEST: PM-HP-002 - Free Hints in Practice
STEPS:
  1. Start practice mode
  2. Request hint with 'H'
  3. Verify no credit deduction
EXPECTED:
  - Hint displayed
  - Credits unchanged
  - Can request multiple hints
EDGE CASES:
  - Practice mode after running out of credits
```

### 3.2 Edge Case Tests

```
TEST: PM-EC-001 - Premium Hints Still Cost Credits
STEPS:
  1. Start practice mode
  2. Request premium hint with 'P'
EXPECTED:
  - 40 credits deducted
  - Error message if insufficient credits
  - Premium hint functionality same as regular mode
EDGE CASES:
  - Switch between regular hints and premium hints
```

### 3.3 Negative Tests

```
TEST: PM-NEG-001 - No XP Verification
STEPS:
  1. Note current XP before practice
  2. Complete 10 correct answers in practice mode
  3. Verify XP unchanged
EXPECTED:
  - XP exactly same as before practice
  - Credits may change (if premium hints used)
  - Command stats still updated
EDGE CASES:
  - Achievement unlocks during practice (should/shouldn't award XP?)
```

---

## 4. Speed Round Tests

### 4.1 Happy Path Tests

```
TEST: SR-HP-001 - Complete Speed Round
STEPS:
  1. Select Speed Round from play menu
  2. Answer questions quickly
  3. Complete when 60 seconds expire
EXPECTED:
  - Timer starts after ENTER pressed
  - Questions presented rapidly
  - 0.3 second pause between questions
  - Session summary shows questions answered within time
EDGE CASES:
  - Answer last question as timer expires
  - Very slow typist (only 1-2 questions)
```

```
TEST: SR-HP-002 - Maximum Questions in Speed Round
STEPS:
  1. Answer questions as fast as possible
  2. Try to maximize question count
EXPECTED:
  - Can answer many questions if fast
  - XP calculated with speed bonus for fast answers
  - Streak bonus accumulates
EDGE CASES:
  - Automated rapid input
  - Questions with very long text
```

### 4.2 Edge Case Tests

```
TEST: SR-EC-001 - Timer Boundary Conditions
STEPS:
  1. Start answer input at 59.9 seconds
  2. Finish input at 61 seconds
EXPECTED:
  - Question either counts or doesn't based on when answer submitted
  - No crash or unexpected behavior
  - Timer check happens after answer submission
EDGE CASES:
  - Exact 60 second boundary
  - System clock changes during round
```

```
TEST: SR-EC-002 - Quit During Speed Round
STEPS:
  1. Start speed round
  2. Enter 'Q' as answer
EXPECTED:
  - Speed round ends immediately
  - Summary shows questions completed before quit
EDGE CASES:
  - Quit on first question
```

### 4.3 Stress Tests

```
TEST: SR-STR-001 - Rapid Input Stress
STEPS:
  1. Use automated input to submit answers instantly
  2. See how many questions can be answered in 60 seconds
EXPECTED:
  - System handles rapid input without crashing
  - Questions selected correctly without repetition issues
  - Memory usage stable
EDGE CASES:
  - Question pool exhaustion within 60 seconds
```

---

## 5. Story Mode Tests

### 5.1 Happy Path Tests

```
TEST: ST-HP-001 - Complete First Chapter Level
STEPS:
  1. Select Story Mode from main menu
  2. Select first chapter (should be unlocked)
  3. Select first level
  4. Complete required questions correctly
EXPECTED:
  - Story intro displayed
  - Questions filtered by level's commands list
  - Level complete screen with XP reward
  - level.id added to player.completed_levels
EDGE CASES:
  - Level has no matching questions
  - Questions_needed > available questions
```

```
TEST: ST-HP-002 - Unlock Next Level
STEPS:
  1. Complete level 1 of a chapter
  2. Verify level 2 is now unlocked
EXPECTED:
  - Level 2 appears as selectable
  - Previous level shows checkmark
  - Unlock based on completed_levels list
EDGE CASES:
  - Skip to check if locked level can be accessed
```

```
TEST: ST-HP-003 - Complete Chapter
STEPS:
  1. Complete all levels in a chapter
EXPECTED:
  - Chapter complete celebration screen
  - chapter.id added to player.completed_chapters
  - Next chapter unlocked if requirement was this chapter
EDGE CASES:
  - Replay completed levels
  - Multiple completions of same chapter
```

```
TEST: ST-HP-004 - Boss Level
STEPS:
  1. Complete all regular levels in a chapter
  2. Start boss level
EXPECTED:
  - Boss introduction with boss_name and boss_description
  - Different visual styling (Theme.WARNING)
  - Same gameplay mechanics
EDGE CASES:
  - Boss level has boss=True but missing boss_name
```

### 5.2 Edge Case Tests

```
TEST: ST-EC-001 - Chapter Unlock Requirements
STEPS:
  1. Check locked chapter requirements
  2. Complete required chapter
  3. Verify unlock
EXPECTED:
  - Locked chapters show "Complete X to unlock"
  - After completing X, chapter becomes available
  - unlock_requirement can be None (always unlocked)
EDGE CASES:
  - Circular unlock requirements
  - Non-existent chapter reference
```

```
TEST: ST-EC-002 - Missing chapters.yaml
STEPS:
  1. Delete or rename chapters.yaml
  2. Start story mode
EXPECTED:
  - Empty chapter list or error message
  - Graceful handling without crash
  - Error logged
EDGE CASES:
  - Malformed YAML
  - Empty file
```

```
TEST: ST-EC-003 - Insufficient Questions for Level
STEPS:
  1. Create level requiring 50 questions
  2. Command only has 10 questions available
EXPECTED:
  - "Not enough questions for this level yet!" message
  - Return to level select after 2 seconds
EDGE CASES:
  - Exactly enough questions
  - 0 questions available
```

### 5.3 Negative Tests

```
TEST: ST-NEG-001 - Quit Story Level Mid-Progress
STEPS:
  1. Start a level requiring 10 correct answers
  2. Get 5 correct
  3. Press 'Q' to quit
EXPECTED:
  - Level NOT marked as complete
  - XP still awarded for correct answers
  - Can retry level
EDGE CASES:
  - Quit with 9/10 correct (one away from completion)
```

```
TEST: ST-NEG-002 - Fail Story Level
STEPS:
  1. Answer all questions incorrectly
  2. View failure screen
EXPECTED:
  - "LEVEL FAILED" screen
  - Level remains locked state (not added to completed)
  - Can retry
EDGE CASES:
  - Fail but answered some correctly
  - XP from correct answers still awarded
```

### 5.4 Regression Tests

```
TEST: ST-REG-001 - Story Progress Persistence
STEPS:
  1. Complete multiple levels
  2. Exit game
  3. Restart and check progress
EXPECTED:
  - completed_levels list preserved
  - completed_chapters list preserved
  - Unlock states consistent
EDGE CASES:
  - Corrupted save file
  - Old save format (version migration)
```

---

## 6. Mystery Mode Tests

### 6.1 Happy Path Tests

```
TEST: MY-HP-001 - Complete Mystery Case Successfully
STEPS:
  1. Select Mystery Mode from main menu
  2. Choose a case
  3. Complete all scenes with 60%+ clue collection
EXPECTED:
  - Case intro, setting, suspects displayed
  - Each scene presents challenges
  - Success conclusion with XP reward
  - case.id added to player.solved_mysteries
EDGE CASES:
  - Exactly 60% clues found
  - All clues found (100%)
```

```
TEST: MY-HP-002 - Clue Collection Tracking
STEPS:
  1. Start mystery case
  2. Answer some challenges correctly, some incorrectly
EXPECTED:
  - Correct answers add to clues_found list
  - Incorrect answers show "missed clue" message
  - Progress counter updates: "Clues: X/Y"
EDGE CASES:
  - First challenge failed
  - All challenges failed
```

```
TEST: MY-HP-003 - Multiple Choice in Mystery
STEPS:
  1. Encounter multiple choice challenge
  2. Answer with letter (A-D) or number (1-4)
EXPECTED:
  - Both formats accepted
  - Dynamic prompt shows valid options
  - Invalid letters/numbers rejected with message
EDGE CASES:
  - 3-option question (A-C only)
  - 5-option question (if exists)
```

```
TEST: MY-HP-004 - Command Builder Challenges
STEPS:
  1. Encounter command_builder type challenge
  2. Enter shell command
EXPECTED:
  - Free-text input accepted
  - Case-insensitive matching
  - Partial matching for complex commands
EDGE CASES:
  - Extra whitespace
  - Alternative correct answers
```

### 6.2 Edge Case Tests

```
TEST: MY-EC-001 - No Mystery Cases Available
STEPS:
  1. Delete all case_*.yaml files
  2. Start mystery mode
EXPECTED:
  - "No mystery cases available yet!" message
  - Return to main menu
EDGE CASES:
  - Files exist but are empty
  - Malformed YAML
```

```
TEST: MY-EC-002 - Case Already Solved
STEPS:
  1. Complete a case successfully
  2. Replay the same case
EXPECTED:
  - Case shows "SOLVED" status in selection
  - Can still replay
  - XP awarded again? (check behavior)
EDGE CASES:
  - Solved list contains invalid case IDs
```

```
TEST: MY-EC-003 - Missing solved_mysteries Attribute
STEPS:
  1. Load player from old save without solved_mysteries
  2. Complete a mystery
EXPECTED:
  - Attribute created if missing (hasattr check)
  - No AttributeError
EDGE CASES:
  - Migration from older version
```

### 6.3 Negative Tests

```
TEST: MY-NEG-001 - Fail Mystery Case
STEPS:
  1. Complete case with less than 60% clues
EXPECTED:
  - "CASE UNSOLVED" conclusion
  - 50 consolation XP awarded
  - Case NOT added to solved_mysteries
EDGE CASES:
  - 59% clues (just under threshold)
  - 0 clues found
```

```
TEST: MY-NEG-002 - Quit Mystery Mid-Case
STEPS:
  1. Start mystery
  2. Press 'Q' during a challenge
EXPECTED:
  - Return to case selection
  - No progress saved
  - No XP awarded
EDGE CASES:
  - Quit on final challenge
  - Quit after last scene but before conclusion
```

### 6.4 Stress Tests

```
TEST: MY-STR-001 - Complete All Mystery Cases
STEPS:
  1. Complete all 10 mystery cases
EXPECTED:
  - All marked as solved
  - Total XP accumulated correctly
  - No duplicate entries in solved_mysteries
EDGE CASES:
  - Replay solved cases multiple times
```

---

## 7. Battle Mode Tests

### 7.1 Happy Path Tests

```
TEST: BM-HP-001 - Host and Complete Battle
STEPS:
  1. Select Battle Mode > Host Game
  2. Choose 5 questions
  3. Wait for opponent connection
  4. Complete all rounds
EXPECTED:
  - Server starts on port 5555
  - Local IP displayed for opponent
  - Questions sent to client (without correct_answer)
  - Server validates client answers
  - Final scores and winner displayed
EDGE CASES:
  - Host wins
  - Client wins
  - Tie game
```

```
TEST: BM-HP-002 - Join and Complete Battle
STEPS:
  1. Have host start game
  2. Select Battle Mode > Join Game
  3. Enter host IP
  4. Complete all rounds
EXPECTED:
  - Connection established
  - Receive questions from host
  - Answers sent to host for validation
  - Results shown after each round
EDGE CASES:
  - Wrong IP format
  - Host not available
```

```
TEST: BM-HP-003 - Battle Scoring
STEPS:
  1. Complete battle with various answer speeds
EXPECTED:
  - Base points: 100 for correct
  - Speed bonus: 50 (<5s), 30 (<10s), 10 (<20s), 0 (>20s)
  - Incorrect: 0 points
EDGE CASES:
  - Both players answer incorrectly
  - Exactly 5/10/20 second boundaries
```

```
TEST: BM-HP-004 - Battle Record Tracking
STEPS:
  1. Complete several battles with wins/losses/ties
EXPECTED:
  - battles_won incremented on wins
  - battles_lost incremented on losses
  - battles_played always incremented
  - Ties don't affect win/loss counts
EDGE CASES:
  - Many ties in a row
```

### 7.2 Edge Case Tests

```
TEST: BM-EC-001 - Name Sanitization
STEPS:
  1. Create player with Rich markup in name: "[bold red]Hacker[/bold red]"
  2. Join battle
EXPECTED:
  - Markup stripped from name
  - Control characters removed
  - Name truncated to 32 characters
EDGE CASES:
  - Empty name after sanitization (defaults to "Player")
  - Only markup characters in name
```

```
TEST: BM-EC-002 - Connection Timeout
STEPS:
  1. Host game
  2. Don't connect within 5 minutes
EXPECTED:
  - "Timeout waiting for opponent" message
  - Return to battle menu
  - Sockets cleaned up properly
EDGE CASES:
  - Connect at 4:59 mark
```

```
TEST: BM-EC-003 - Network Disconnection Mid-Battle
STEPS:
  1. Start battle
  2. Disconnect network during question
EXPECTED:
  - Connection error handled
  - Sockets cleaned up with proper shutdown
  - Return to menu without crash
EDGE CASES:
  - Disconnect during answer submission
  - Disconnect before game over message
```

### 7.3 Negative Tests

```
TEST: BM-NEG-001 - Invalid Host IP
STEPS:
  1. Enter invalid IP format
EXPECTED:
  - Validation error or connection refused
  - Clear error message
  - Return to join menu
EDGE CASES:
  - "localhost" as IP
  - IPv6 address
  - Domain name instead of IP
```

```
TEST: BM-NEG-002 - Port Already in Use
STEPS:
  1. Run another service on port 5555
  2. Try to host battle
EXPECTED:
  - Error message about port
  - Graceful failure
EDGE CASES:
  - Previous battle socket not fully closed
```

```
TEST: BM-NEG-003 - Malformed Network Messages
STEPS:
  1. Connect with modified client sending invalid JSON
EXPECTED:
  - safe_json_loads returns None
  - Error logged
  - Battle terminates gracefully
EDGE CASES:
  - Empty message
  - Binary data
  - Truncated JSON
```

### 7.4 Security Tests

```
TEST: BM-SEC-001 - Answer Not Sent to Client
STEPS:
  1. Monitor network traffic during battle
  2. Check question message structure
EXPECTED:
  - correct_answer NOT included in question message to client
  - Only sent in result message AFTER both players answered
EDGE CASES:
  - Packet sniffing attack
```

```
TEST: BM-SEC-002 - Server-Side Answer Validation
STEPS:
  1. Modify client to claim all answers correct
  2. Submit to honest host
EXPECTED:
  - Host validates client's raw answer
  - Host's validation overrides client's claim
  - Points calculated based on server's validation
EDGE CASES:
  - Client sends different answer than claimed
```

### 7.5 Stress Tests

```
TEST: BM-STR-001 - Rapid Battle Succession
STEPS:
  1. Complete 20 battles in a row
EXPECTED:
  - Sockets properly cleaned up between battles
  - No socket leaks
  - Battle stats accumulate correctly
EDGE CASES:
  - Quick quit and rejoin
```

---

## 8. Cross-Module Integration Tests

### 8.1 Data Flow Tests

```
TEST: INT-DF-001 - XP to Level Integration
STEPS:
  1. Start with 0 XP
  2. Earn XP through various modes
  3. Verify level calculations
EXPECTED:
  - Level = floor(sqrt(XP/100)) + 1
  - L1: 0-99 XP, L2: 100-399 XP, L3: 400-899 XP
  - Level updates immediately after XP changes
EDGE CASES:
  - Level boundary values
  - Large XP jumps (completing mystery)
```

```
TEST: INT-DF-002 - Credits System Integration
STEPS:
  1. Earn credits through correct answers (10 per correct)
  2. Spend credits on premium hints
  3. Earn credits through achievements
EXPECTED:
  - Credits persist across sessions
  - Spending works in all modes
  - Achievement credit_reward properly awarded
EDGE CASES:
  - Negative credits (should be impossible)
  - Large credit accumulation
```

```
TEST: INT-DF-003 - Achievement Unlocks
STEPS:
  1. Meet achievement requirements
  2. Verify unlock triggers correctly
EXPECTED:
  - Achievement notification displayed
  - ID added to unlocked_achievements
  - XP reward added immediately
  - Credit reward added if applicable
EDGE CASES:
  - Same achievement unlocked twice (should be prevented)
  - Achievement with complex requirements
```

```
TEST: INT-DF-004 - Command Stats Aggregation
STEPS:
  1. Answer questions across all modes
  2. Check command_stats in player
EXPECTED:
  - Stats updated in: Quick Play, Training, Story Mode
  - Accuracy calculated correctly: correct/total
  - weak_areas and strong_areas derived properly
EDGE CASES:
  - Command with only 1-2 answers
  - Command stats reset scenario
```

### 8.2 State Persistence Tests

```
TEST: INT-SP-001 - Full State Save/Load Cycle
STEPS:
  1. Play all modes
  2. Exit game
  3. Restart and verify all state
EXPECTED:
  - username, level, xp
  - total_questions_answered, correct_answers
  - streak, best_streak
  - command_stats, recently_answered
  - completed_levels, completed_chapters
  - battles_won, battles_lost, battles_played
  - solved_mysteries
  - credits
  - unlocked_achievements
EDGE CASES:
  - Very large save file
  - Concurrent saves
```

```
TEST: INT-SP-002 - Atomic Save Operation
STEPS:
  1. Trigger save
  2. Kill process mid-save
  3. Restart and check data integrity
EXPECTED:
  - Either old save or new save complete
  - No partial/corrupted data
  - .tmp file cleaned up
  - .bak backup available
EDGE CASES:
  - Disk full during save
  - Permission denied
```

### 8.3 UI Component Integration

```
TEST: INT-UI-001 - Progress Display Consistency
STEPS:
  1. Check progress in main menu stats panel
  2. Check same stats in View Progress screen
  3. Verify consistency
EXPECTED:
  - XP, level, streak match everywhere
  - Progress percentage calculated consistently
  - Accuracy percentages match
EDGE CASES:
  - 0 questions answered (division by zero)
  - 100% accuracy display
```

```
TEST: INT-UI-002 - Achievement Display
STEPS:
  1. Unlock some achievements
  2. View achievements screen
EXPECTED:
  - Unlocked achievements show name/description
  - Locked achievements show "???"
  - Count shows X/Y unlocked
  - Rarity styling applied correctly
EDGE CASES:
  - 0 achievements unlocked
  - All achievements unlocked
```

### 8.4 Data Loader Integration

```
TEST: INT-DL-001 - Question Pool Building
STEPS:
  1. Check loaded questions
  2. Verify command_questions_cache
EXPECTED:
  - All questions from essential_questions.yaml loaded
  - All questions from advanced_questions.yaml loaded
  - Cache properly groups questions by command
EDGE CASES:
  - Question with unknown command
  - Duplicate question IDs
```

```
TEST: INT-DL-002 - Achievement Loading
STEPS:
  1. Check loaded achievements
  2. Verify requirement parsing
EXPECTED:
  - All achievements from achievements.yaml loaded
  - Various requirement types handled
  - XP and credit rewards parsed
EDGE CASES:
  - Malformed requirement
  - Missing required fields
```

---

## 9. Currently Untestable Components

### 9.1 Untestable Due to Architecture

```
COMPONENT: Terminal Clear/Splash Display
REASON: Uses clear_terminal() and time.sleep() for visual effects
IMPACT: Cannot verify splash screen timing or screen clearing
MITIGATION: Mock clear_terminal() and time.sleep() in unit tests
```

```
COMPONENT: Rich Console Output
REASON: UI uses Rich library for styled terminal output
IMPACT: Cannot easily assert on formatted console output
MITIGATION: Capture console output to string for testing
```

```
COMPONENT: User Input Prompts
REASON: Uses Rich Prompt.ask() which blocks for stdin
IMPACT: Cannot automate input in unit tests
MITIGATION: Mock Prompt.ask() or use pexpect for integration tests
```

### 9.2 Untestable Due to External Dependencies

```
COMPONENT: Network Battle Mode
REASON: Requires two separate processes on network
IMPACT: Cannot unit test full battle flow
MITIGATION:
  - Mock socket operations for unit tests
  - Use localhost for integration tests
  - Use Docker containers for full network tests
```

```
COMPONENT: File System Operations
REASON: Direct filesystem access for saves
IMPACT: Tests may modify actual user data
MITIGATION:
  - Use temporary directories
  - Mock Path operations
  - Clean up test data after tests
```

```
COMPONENT: System Time Operations
REASON: Uses time.time() for speed bonuses, datetime for saves
IMPACT: Cannot reliably test timing-dependent code
MITIGATION:
  - Freeze time with unittest.mock.patch
  - Use dependency injection for time functions
```

### 9.3 Untestable Due to Missing Infrastructure

```
COMPONENT: Achievement Speed Requirements
REASON: Achievement requirement type "speed" returns False with comment "Implemented in game engine"
IMPACT: Speed-based achievements cannot be unlocked
MITIGATION: Implement proper speed tracking in session data
```

```
COMPONENT: Achievement Perfect Sessions
REASON: Requirement type "perfect_sessions" returns False with comment "Implemented in game engine"
IMPACT: Perfect session achievements cannot be unlocked
MITIGATION: Track session history for perfect session count
```

```
COMPONENT: Mystery solved_mysteries Initialization
REASON: Uses hasattr check for backwards compatibility
IMPACT: Old saves may not have this field
MITIGATION: Add migration logic in state_manager load
```

### 9.4 Recommended Test Infrastructure

```
NEED: Test Fixtures
DETAILS:
  - Create test player with known state
  - Create test question pool with predictable ordering
  - Create test achievements with easy-to-trigger requirements
```

```
NEED: Mocking Framework Setup
DETAILS:
  - Mock random.shuffle for predictable option ordering
  - Mock time.time for consistent speed calculations
  - Mock Prompt.ask for automated input
  - Mock Console for output capture
```

```
NEED: Integration Test Environment
DETAILS:
  - Temporary save directory
  - Test data files separate from production
  - Network loopback testing setup
```

```
NEED: Coverage Targets
DETAILS:
  - Core logic: 90%+ coverage
  - UI components: 70%+ coverage
  - Network code: 80%+ coverage with mocks
```

---

## Appendix: Test Data Requirements

### A.1 Player States for Testing

```yaml
test_players:
  - new_player:
      username: "TestNewbie"
      level: 1
      xp: 0
      credits: 100

  - intermediate_player:
      username: "TestIntermediate"
      level: 5
      xp: 2500
      total_questions_answered: 100
      correct_answers: 75
      credits: 500

  - advanced_player:
      username: "TestAdvanced"
      level: 20
      xp: 40000
      best_streak: 25
      battles_won: 10
      solved_mysteries: ["case_001", "case_002"]
```

### A.2 Question Types to Test

```yaml
question_types_to_test:
  - multiple_choice: 4-option questions
  - fill_blank: Command completion questions
  - what_does_it_do: Command output prediction
  - fix_error: Syntax correction
  - command_builder: Free-form command writing
  - output_prediction: Expected output questions
```

### A.3 Achievement Types to Test

```yaml
achievement_types:
  - correct_answers: {type: correct_answers, count: N}
  - streak: {type: streak, count: N}
  - mastery: {type: mastery, difficulty: X, percentage: Y}
  - speed: {type: speed, questions: N} # Currently unimplemented
  - time_of_day: {type: time_of_day, start_hour: X, end_hour: Y}
  - perfect_sessions: {type: perfect_sessions, count: N} # Currently unimplemented
  - total_questions: {type: total_questions, count: N}
```

---

## Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2024-12-30 | Initial test scenario document |
