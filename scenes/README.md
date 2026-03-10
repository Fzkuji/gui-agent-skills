# Scene System — Loading Protocol

## For LLM Agents

### When you receive a GUI task:

```
1. SKILL.md tells you which scene to load
2. Read the scene YAML
3. Look at `exports:` — this is the interface (params + output)
4. Look at `meta_actions:` — these are the steps
5. Each step is either:
   - action: → look up in _actions.yaml for how to execute
   - ref: "#local_meta_action" → expand another meta action in same file
   - ref: "scenes/other.yaml#export" → load another scene file
6. Execute from top to bottom, following refs as needed
```

### Loading rules:

- **Only load what you need** — don't read all scenes upfront
- **Follow refs lazily** — only read a referenced scene when you reach that step
- **_actions.yaml is loaded last** — only when you're about to execute an atomic op
- **docs/core.md** — read once at the start if this is your first GUI task in the session

## Scene YAML Structure

```yaml
# Header
scene: scene-name
goal: "What this scene accomplishes"
depends_on:                              # Optional: scenes this one references
  - scenes/other.yaml

# Public interface — what other scenes see
exports:
  action_name:
    params:
      param1: "Description"
    output: "What the caller gets back"

# Internal implementation — only loaded when entering this scene
meta_actions:
  action_name:                           # Same name as export
    steps:
      - action: click                    # Atomic action from _actions.yaml
        target: "{x},{y}"
      - ref: "#other_meta_action"        # Local meta action
        params: { key: "value" }
      - ref: "scenes/other.yaml#export"  # Cross-scene reference
        params: { key: "value" }
        condition: "when to execute"     # Optional guard

  other_meta_action:
    desc: "What this does"
    steps: [...]
    lessons:                             # Hard-won lessons for this specific step
      - "Things that went wrong and how to avoid"

# Scene-level warnings
gotchas:
  - "Important caveats for this entire scene"
```

## Cross-Reference Syntax

```yaml
# Same file
- ref: "#meta_action_name"

# Another scene file
- ref: "scenes/1password.yaml#get_password"
  params:
    entry: "CityU"
```

## Dependency Graph

```
_actions.yaml (shared primitives)
    ↑
1password.yaml ← vpn-reconnect.yaml
    ↑
messaging.yaml (independent)
app-explore.yaml (independent)
```
