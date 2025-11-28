# Oracle CLI command reference

Complete reference for all Oracle CLI commands with detailed options, parameters, and examples.

## Quick reference

| Command | Purpose | Key options |
|---------|---------|-------------|
| `closed` | Ask yes/no questions | `-q`, `-l` (likelihood) |
| `muse` | Get thematic inspiration words | `-t` (theme), `-c` (count) |
| `twist` | Generate plot twists | No required options |
| `chaos-roll` | Roll chaos dice | `-d` (dice) |

## Global options

All commands support these global options:

### Output format

```bash
--format, -f [text|json]
```

Control output format. Default: `text`

- `text`: Human-readable colored output
- `json`: Structured JSON for programmatic use

### Random seed

```bash
--seed, -s INTEGER
```

Set random seed for deterministic output. Useful for:
- Testing and reproducibility
- LLM integration
- Debugging

Example:

```bash
oracle closed -q "Is it safe?" -s 42
# Always produces same result with seed 42
```

## Commands

### closed

Ask a closed (yes/no) question with likelihood modifiers.

**Syntax:**

```bash
oracle closed --question "QUESTION" [--likelihood LIKELIHOOD] [OPTIONS]
```

**Required options:**

- `--question, -q TEXT`: The yes/no question to ask

**Optional parameters:**

- `--likelihood, -l [very_unlikely|unlikely|even|likely|very_likely]`: Likelihood of positive answer (default: `even`)
- `--seed, -s INTEGER`: Random seed for deterministic output
- `--format, -f [text|json]`: Output format (default: `text`)

**How it works:**

1. Rolls 1d6
2. Applies modifier based on likelihood:
   - `very_unlikely`: -2
   - `unlikely`: -1
   - `even`: 0
   - `likely`: +1
   - `very_likely`: +2
3. Clamps result to [1, 6]
4. Returns YES/NO answer with scenario and tone context

**Examples:**

```bash
# Basic yes/no question
oracle closed -q "Is the door locked?"

# With likelihood modifier
oracle closed -q "Does the guard notice me?" -l very_unlikely

# Get structured JSON output
oracle closed -q "Is it safe?" -l likely -f json

# Deterministic result
oracle closed -q "Will it rain?" -l even -s 123
```

**Example output (text):**

```
YES (and...)
Roll: 5 + 1 = 6
Scenario: Positive outcome with additional benefit
Tone: Fortunate
```

**Example output (json):**

```json
{
  "type": "closed",
  "question": "Is the door locked?",
  "likelihood": "likely",
  "roll": {
    "base": 4,
    "modifier": 1,
    "final": 5
  },
  "result": {
    "answer": "yes",
    "detail": "and...",
    "scenario": "Positive with benefit",
    "tone": "Fortunate"
  }
}
```

### muse

Get inspiration words from thematic d20 tables.

**Syntax:**

```bash
oracle muse --theme THEME [--theme THEME ...] [--count COUNT] [OPTIONS]
```

**Required options:**

- `--theme, -t TEXT`: Theme(s) to use (can be specified multiple times)

**Optional parameters:**

- `--count, -c INTEGER`: Number of words to generate (default: 1)
- `--seed, -s INTEGER`: Random seed for deterministic output
- `--format, -f [text|json]`: Output format (default: `text`)

**Available themes:**

- `Change`: Transformation and alteration words
- `Divine`: Spiritual and mystical concepts
- `Monstrous`: Creatures and fearsome elements
- `Place`: Locations and structures
- `Social`: Relationships and society
- `Sorcery`: Magic and supernatural
- `Swords`: Conflict and combat
- `Talk`: Communication and dialogue
- `Treasure`: Valuable items and quests
- `Wilderness`: Natural environments

**How it works:**

1. Rolls d20 for each word requested
2. When multiple themes specified, cycles through them round-robin
3. Returns thematic word from the rolled table entry

**Examples:**

```bash
# Single word from one theme
oracle muse -t Change

# Multiple words from one theme
oracle muse -t Swords -c 5

# Alternate between two themes
oracle muse -t Wilderness -t Treasure -c 6
# Generates: Wilderness, Treasure, Wilderness, Treasure, Wilderness, Treasure

# Three themes with round-robin
oracle muse -t Sorcery -t Divine -t Monstrous -c 9

# JSON output for parsing
oracle muse -t Social -t Talk -c 3 -f json

# Deterministic inspiration
oracle muse -t Change -c 3 -s 42
```

**Example output (text):**

```
Swords (d20=14): Encounter
Sorcery (d20=7): Trickery
Swords (d20=19): Attack
```

**Example output (json):**

```json
{
  "type": "muse",
  "results": [
    {
      "theme": "Change",
      "roll": 12,
      "word": "Break"
    },
    {
      "theme": "Change",
      "roll": 8,
      "word": "Affect"
    }
  ]
}
```

### twist

Generate a plot twist by combining random subject and action.

**Syntax:**

```bash
oracle twist [OPTIONS]
```

**Optional parameters:**

- `--seed, -s INTEGER`: Random seed for deterministic output
- `--format, -f [text|json]`: Output format (default: `text`)

**How it works:**

1. Rolls d6 for subject
2. Rolls d6 for action
3. Combines them into a plot twist phrase

**Examples:**

```bash
# Generate random twist
oracle twist

# Deterministic twist
oracle twist -s 42

# JSON format
oracle twist -f json
```

**Example output (text):**

```
A mysterious stranger arrives
Subject: 3, Action: 5
```

**Example output (json):**

```json
{
  "type": "twist",
  "rolls": {
    "subject": 3,
    "action": 5
  },
  "result": "A mysterious stranger arrives"
}
```

### chaos-roll

Roll chaos dice and track the chaos pool.

**Syntax:**

```bash
oracle chaos-roll --dice DICE [OPTIONS]
```

**Required options:**

- `--dice, -d INTEGER`: Number of d6s to roll (current pool size)

**Optional parameters:**

- `--seed, -s INTEGER`: Random seed for deterministic output
- `--format, -f [text|json]`: Output format (default: `text`)

**How it works:**

1. Rolls N d6s (where N is your current chaos pool)
2. Counts how many sixes were rolled
3. Next pool size = current pool - sixes rolled
4. If pool reaches 0, an event is triggered!

**Pool mechanics:**

- Start with a pool size (typically 6)
- Each scene, roll the pool
- Remove one die for each six rolled
- When pool hits 0, a random event occurs
- After an event, reset pool to starting size

**Examples:**

```bash
# Roll starting pool of 6
oracle chaos-roll -d 6

# Roll current pool of 4
oracle chaos-roll -d 4

# Deterministic roll
oracle chaos-roll -d 6 -s 123

# JSON output
oracle chaos-roll -d 3 -f json
```

**Example output (text):**

```
Rolls: [4, 2, 6, 1, 5, 6]
Sixes: 2
Next Pool: 4
No event triggered
```

**Example output when event triggers:**

```
Rolls: [6, 6, 3]
Sixes: 2
Next Pool: 1
No event triggered

# Next roll:
Rolls: [6]
Sixes: 1
Next Pool: 0
⚠ EVENT TRIGGERED! ⚠
```

**Example output (json):**

```json
{
  "type": "chaos",
  "input_pool": 6,
  "rolls": [4, 2, 6, 1, 5, 6],
  "sixes": 2,
  "next_pool": 4,
  "triggered": false
}
```

## Combining commands

The Oracle CLI is designed to work well in shell scripts and with other tools.

### Shell script example

```bash
#!/bin/bash

# Ask if the party encounters danger
DANGER=$(oracle closed -q "Do we encounter danger?" -l likely -f json)
ANSWER=$(echo $DANGER | jq -r '.result.answer')

if [ "$ANSWER" = "yes" ]; then
  echo "Danger ahead!"

  # What kind of danger?
  oracle muse -t Monstrous -t Swords -c 2

  # Generate a twist
  oracle twist
fi
```

### Python integration example

```python
import json
import subprocess

def ask_oracle(question, likelihood="even"):
    """Ask the oracle a yes/no question."""
    result = subprocess.run(
        ["oracle", "closed", "-q", question, "-l", likelihood, "-f", "json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def get_inspiration(theme, count=1):
    """Get muse inspiration."""
    result = subprocess.run(
        ["oracle", "muse", "-t", theme, "-c", str(count), "-f", "json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Use the oracles
answer = ask_oracle("Is the temple abandoned?", "likely")
print(f"Answer: {answer['result']['answer']}")

if answer['result']['answer'] == 'yes':
    words = get_inspiration("Place", 3)
    print("The temple is:", [r['word'] for r in words['results']])
```

## Tips and tricks

### Using seeds for consistent results

Seeds are useful when you want reproducible results:

```bash
# Save the seed in your session notes
oracle closed -q "Does the ritual succeed?" -s 12345

# Later, can verify the same result
oracle closed -q "Does the ritual succeed?" -s 12345
```

### Round-robin themes for variety

The muse command cycles through themes, which is great for mixed inspiration:

```bash
# Get balanced wilderness and treasure words
oracle muse -t Wilderness -t Treasure -c 10
# Returns: W, T, W, T, W, T, W, T, W, T
```

### JSON output for tooling

Use JSON format when integrating with other tools:

```bash
# Parse with jq
oracle closed -q "Success?" -f json | jq '.result.answer'

# Save results
oracle muse -t Change -c 5 -f json > inspiration.json

# Pipe to other tools
oracle twist -f json | jq -r '.result'
```

### Chaos pool tracking

Track your chaos pool in a file:

```bash
# Store current pool
echo "6" > chaos_pool.txt

# Roll and update
POOL=$(cat chaos_pool.txt)
oracle chaos-roll -d $POOL -f json > last_chaos.json
NEXT=$(jq -r '.next_pool' last_chaos.json)
echo $NEXT > chaos_pool.txt

# Check for events
if [ $NEXT -eq 0 ]; then
  echo "EVENT! Rolling twist..."
  oracle twist
  echo "6" > chaos_pool.txt  # Reset pool
fi
```

## Getting help

View help for any command:

```bash
oracle --help
oracle closed --help
oracle muse --help
oracle twist --help
oracle chaos-roll --help
```
