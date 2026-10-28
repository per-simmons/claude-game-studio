---
name: setup
description: Configure the game studio for this machine. Checks tools, picks free vs pro path, image route, voice (Fish Audio Drama 3 default, off until a key is added), LLM mode, Blender, RunPod and studio-floor terminal, and writes studio/studio.config.json. Use for "/game-studio:setup", "configure the studio", "turn on Fish voices", "enable RunPod/Blender".
---

# /game-studio:setup

Work in the current game folder. If it has no `studio/`, copy in
`${CLAUDE_PLUGIN_ROOT}/templates/project/` first.

## 1. Check the tools, and report a ✓/✗ table
| Tool | How to check | Needed for |
|---|---|---|
| `python3` 3.9+ | `python3 --version` | **Required**: the board, the case-pack player and the linter |
| `git` | `git --version` | Recommended: parallel engineer worktrees |
| `claude` | `claude --version` | Floor mode: `claude --agent` |
| iTerm2 (macOS) or `tmux` | `ls /Applications/iTerm.app`, `command -v tmux` | Floor mode |
| `blender` | `command -v blender` | Pro only |
| `runpodctl` | `command -v runpodctl` | Pro only |
| `node` 20+ | `node --version` | Only if you build the web engine |

## 2. Ask, then write `studio/studio.config.json`
Keep it to one message with defaults the user can accept.
- **Path:** `free` (the default) or `pro`.
- **Images** (`image.provider`):
  - **`manual`** (the default). The studio writes prompts to `art/prompts/`, and you paste them into
    any image generator. This works with every tool and needs no key.
  - **`command`**. A command you supply, with `{prompt_file}` and `{out}` placeholders.
- **Voice:** the VO department is **Fish Audio Drama 3**.
  - It directs performances with plain-English stage directions: `[voice catches on the time]`,
    `<whisper>`, multi-speaker scenes, and word timestamps for captions.
  - To turn it on, create an account and API key at **https://fish.audio**, put `FISH_API_KEY=…` in
    `.env`, and set `voice.enabled: true`.
  - Until then the game uses a free placeholder voice. **Setup never calls the Fish API.**
- **Suspect brains** (`llm.mode`): `offline` (the default; authored lines, free, unbreakable) or
  `live` (free-text conversation through an LLM key the user provides in `.env`).
- **Pro departments:**
  - `blender.enabled`, with the path to the binary.
  - `runpod.enabled`, `runpod.max_price` (default 0.40 $/hr), `runpod.max_minutes` (default 20), and
    the key name `RUNPOD_API_KEY` (or an `env_file`).
  - Before the first real job, offer the smoke test:
    `${CLAUDE_PLUGIN_ROOT}/scripts/pro/runpod/runpod-blender-render.sh`, using
    `make_test_blend.py`. It costs about $0.01.
- **The floor** (`floor.terminal`): `iterm2`, `tmux` or `print`, plus `floor.roles` and optional
  `floor.bounds` (which screen rectangle to fill).
- **Recording guard** (`pro.respect_recording`): pause heavy local work while a screen recorder runs.

## 3. Keys
- Never write a key into the config, and never print one.
- Keys live in `.env`, which is gitignored, with names taken from `.env.example`.

## 4. Hands-off runs (optional)
Offer to add this to the project's `.claude/settings.json`, so employees can use the board without
asking each time:
```json
{ "permissions": { "allow": ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board/board.py:*)", "Bash(python3 */scripts/board/board.py:*)"] } }
```

## 5. Finish
Print the config summary and the next command: `/game-studio:new` or `/game-studio:case-pack play …`.
