# Game Studio for Claude Code

**A whole AI game company, run from your terminal.** There's a producer who plans the work and a
creative director who guards the vision. A writers' room drafts the story, a narrative lead reviews
it, and three adversarial story auditors try to break it. A systems designer, an art director and a
character artist work alongside a UI designer, a voice director, engineers and QA. Every one of them is
a Claude Code sub-agent with a job description and a quality bar. They work in parallel off a shared
ticket board, review each other's work, and stop at milestone gates for **you**, the publisher, to
approve.

It comes with a **playable murder mystery** you can try right now, plus a format for making and
sharing your own.

## Install (one line)
```bash
claude plugin marketplace add per-simmons/claude-game-studio && claude plugin install game-studio@game-studio
```
In a Claude Code session, the equivalent is `/plugin marketplace add per-simmons/claude-game-studio`
followed by `/plugin install game-studio@game-studio`. To try it without installing, use
`claude --plugin-dir ./claude-game-studio`.

You'll need Claude Code and Python 3.9+. Nothing else is required on the free path.

## Make a game (about 5 questions)
```
/game-studio:new a jewel thief on a 1920s airship
```
The Producer asks five questions: premise, kind of game, length, free or pro path, and whether you
want to watch the studio work. Then it sets up a project folder with a board and a config, runs the
first cycle in parallel, and stops at **G0 Concept** for your approval.

| Command | What it does |
|---|---|
| `/game-studio:new` | Kick off a new game |
| `/game-studio:setup` | Configure image route, voice, LLM mode, the pro departments, the studio floor |
| `/game-studio:status` | Standup: `studio/STATUS.md` with done, next and blockers per department |
| `/game-studio:gate G1` | Milestone review packet: approve, change, or kill |
| `/game-studio:floor` | Watch the studio work: one terminal pane per employee |
| `/game-studio:case-pack play <pack>` | Play a mystery in your terminal |
| `/game-studio:case-pack new "<premise>"` | The studio writes a fair, tested mystery from one line |
| `/game-studio:case-pack lint <pack>` | Check a mystery against fair-play rules |

## Play the example now (free, offline)
```bash
python3 scripts/casepack/play.py examples/case-packs/the-locked-study          # ~10 min warm-up
python3 scripts/casepack/play.py examples/case-packs/dead-air-on-the-meridian  # 20–40 min
```
In **Dead Air on the Meridian**, a radio gossip king is murdered on a 1936 sleeper train stopped in a
snowbound pass. You have six frightened passengers and four hours until dawn. Everyone is hiding
something, and only one of them killed him. Talk to suspects in plain English, catch their lies with
evidence, and name the killer before the sheriff arrives.

## The studio
```
producer ──plans cycles, launches lanes in parallel, routes reviews, writes STATUS.md, runs gates
├─ creative-director   pillars, pitch, fun audit
├─ researcher          prior art, with sources
├─ writers-room ──▶ narrative-lead ──▶ story-auditor ×3 (speed-solve · plot holes · consistency)
├─ systems-designer    loops, decisions, clock, anti-jailbreak NPC design
├─ character-artist ──▶ art-director ◀── ui-designer, blender-artist (pro)
├─ vo-director         Fish Audio Drama 3 direction scripts
├─ engineer ×N         one git worktree per lane
├─ render-wrangler     RunPod GPU renders (pro)
└─ qa-lead ──bugs──▶ engineer
```
- **The board:** `studio/board.json`, managed by `scripts/board/board.py`. Tickets carry an owner,
  status, deps and a reviewer.
- **Review loops:** nobody approves their own work, and review notes are tracked round by round.
- **The gates:** G0 Concept → G1 Vertical slice → G2 Content complete → G3 Polish. Only you can
  approve one.

The full rulebook is in `skills/studio/references/operating-model.md`.

## Free path vs pro path
| | Free (default) | Pro (optional) |
|---|---|---|
| Story, design, QA | ✓ | ✓ |
| Art | 2D. The studio writes prompts for **any image generator** you use, or you point it at your own CLI | + Blender scenes and props built by script, + final renders on a rented **RunPod** GPU with a price ceiling and auto-shutdown |
| Voice | Placeholder voice | **Fish Audio Drama 3**, the default VO department. Add a key from **https://fish.audio** to hear directed performances: `[voice catches on the time]`, `<whisper>`, multi-speaker scenes, word-synced captions |
| Suspect brains | Offline, with authored lines (unbreakable) | Live free-text through an LLM key you provide |
| Keys needed | none | Only for what you turn on, kept in `.env` |

The plugin never calls a paid API that you haven't switched on in `studio/studio.config.json`.

## Make and share mysteries
A **case pack** is one folder holding `casepack.json`, `case-file.json` and a README. The format is in
`skills/studio/references/case-pack-format.md`.
```
/game-studio:case-pack new "a poisoned toast at a 1960s moon-landing party"
```
The writers' room drafts it, the narrative lead and three story auditors attack it, the linter checks
nine fairness rules, and the auto-solver proves it can be finished. Then zip the folder and share it.
Anyone can play it with `play.py`.

## Studio floor (great on camera)
```
/game-studio:floor            # iTerm2 grid on macOS, or tmux anywhere
/game-studio:floor --rehearse # practise the shot: no AI sessions, no cost
```
Each employee runs as its own `claude --agent game-studio:<role>` session in a colour-coded pane,
working its queue on the shared board, with a live board pane alongside.

## Licence
Code and studio templates are **MIT**. The example case packs are **CC BY 4.0**. Every story, name and
character in the examples is original.
