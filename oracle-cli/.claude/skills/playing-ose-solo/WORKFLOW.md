# OSE Solo Game Loop

Copy this checklist to track the current scene:

```
Scene Progress:

  - [ ] 1. Read Boxed Text (STOP: Do not reveal secrets yet)
  - [ ] 2. Establish Player Intent
  - [ ] 3. Check Scene Expectation (Twist)
  - [ ] 4. Resolve Action (Oracle/Muse)
  - [ ] 5. Update State (Chaos Dice/Resources)
```

## Step 1: Read boxed text

Read *only* the flavor text. Do not read DM secrets (traps, monster stats) until interaction occurs.

## Step 2: Establish intent

Wait for the user to declare exactly what they are doing (e.g., "I search the chest" or "I enter the room").

## Step 3: Check scene expectation

Before resolving the main action, ask yourself: "Is the scene/monster behaving exactly as the module describes?"

1. Run: `oracle closed --question "Is the scene as expected?"`
2. If **No**, Run: `oracle twist`
3. Incorporate the twist immediately.

## Step 4: Resolve action

* **Binary checks**: Use `oracle closed`.
* **Open details**: Use `oracle muse` (Pick themes from [REFERENCE.md](REFERENCE.md)).
* **Interpretation**:
  * *Yes, but...*: Success with a complication.
  * *No, because...*: Failure with a clear cause.

## Step 5: Update state

If specific timed triggers exist (e.g., "wandering monsters every 2 turns"), manage the Chaos Dice:

* Run: `oracle chaos-roll --dice [2|4|6]`.
