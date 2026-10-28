# The studio operating model

The model copies how real studios run production, and it's built only on Claude Code features that
exist. Sources are listed at the bottom.

## 1. The org chart
The **Producer** runs every cycle. Departments are named sub-agents (`agents/*.md` in this plugin,
invoked as `game-studio:<name>`).

| Lane | Employee (agent) | Reviews whom | Reviewed by |
|---|---|---|---|
| production | `producer` | gates, all lanes | **you** (the publisher) at gates |
| creative | `creative-director` | pillars, fun audit, gate packets | you |
| research | `researcher` | n/a | creative-director |
| narrative | `writers-room` | n/a | `narrative-lead` |
| narrative | `narrative-lead` | writers-room; owns the bible | `story-auditor` (adversarial) + you |
| narrative | `story-auditor` | the bible (speed-solve, plot holes, consistency) | n/a |
| systems | `systems-designer` | n/a | creative-director |
| art | `character-artist` | n/a | `art-director` |
| art | `art-director` | character-artist, blender-artist, ui-designer (visuals) | you at the art gate |
| blender *(pro)* | `blender-artist` | n/a | art-director |
| render *(pro)* | `render-wrangler` | n/a | art-director (look) + producer (cost) |
| ui | `ui-designer` | n/a | art-director (look) + qa-lead (usability) |
| vo | `vo-director` | n/a | narrative-lead (words) + qa-lead (lint) |
| engineering | `engineer` (one per lane; each in its own git worktree) | n/a | qa-lead |
| qa | `qa-lead` | engineer (files bugs), every build | producer |

**Rule: nobody approves their own work.** `board.py review` refuses it.

## 2. The board (`studio/board.json`, rendered to `studio/BOARD.md`)
- Every piece of work is a ticket with an **owner, lane, status, deps, reviewer, milestone,
  priority and outputs**. Bugs also carry **severity A–D** (A: crash or softlock or leak; B: must fix;
  C: minor; D: suggestion), kept separate from **priority P0–P3**. Only the producer and the qa-lead
  set priority.
- **The status machine**, after the ShotGrid/ftrack-style asset states:
  `backlog → ready → in_progress → in_review → approved → done`, with
  `in_review → changes_requested → in_progress`, and `blocked` from anywhere.
- **Bug lifecycle:** `new → triaged → assigned → fixed → verified → closed`. Closing needs a reason
  code: fixed, as-designed, waived, duplicate or cannot-reproduce. Verification is a regression check
  from a clean boot.
- Only `scripts/board/board.py` writes the board. It takes a file lock, so parallel employees can claim
  tickets safely. Nobody edits BOARD.md by hand.
- Review notes are tracked per round. A new version is checked against the previous round's notes
  (`review_round`). On round 3 the ticket is escalated to the Producer.

## 3. Cadence
| Real studio | This studio |
|---|---|
| **Release** (a set of sprints toward near-shippable) | **Milestone** (M0 Concept, M1 Vertical slice, M2 Content complete, M3 Polish/ship) |
| **Sprint** (2–4 weeks, frozen goal, playable at the end) | **Cycle**: the Producer plans N tickets, the lanes work in parallel, reviews, a demo, a retro. The goal is frozen once planned. Each cycle ends with *something you can look at or play* |
| **Sprint planning** | `producer` writes a cycle goal and tickets with deps |
| **Daily scrum** | `STATUS.md`, written by the producer every cycle (and on request) from `board.py standup`: done, next, blockers per lane |
| **Sprint review / demo** | The producer sends you a demo packet: screenshots, a play link, or a CLI transcript |
| **Retrospective** | Three lines in STATUS.md: keep, change, try |
| **Greenlight / stage gate** | **◆ Gates G0–G3** (below). Only you can pass one |
| **Postmortem** | `studio/POSTMORTEM.md` at ship: what went right and what went wrong, with 5 of each |

## 4. Gates (you approve)
| Gate | Name | Acceptance criteria (written before the work starts) |
|---|---|---|
| **G0** | Concept | One-sheet, 3–4 pillars, the premise, the core loop in 60 seconds, the target session length, the risks. For mysteries: the twist in one line, and the story-auditor's speed-solve estimate |
| **G1** | Vertical slice (greenlight) | One act or level fully playable at near-final quality, **including menus and settings**. Every system working. Red team and fun-audit P0 items 1, 2, 3, 9 and 10 pass. The first-60-seconds check (`playtest-protocol.md` §2a) answers 5/5 for 3 fresh personas. A 90-second capture |
| **G2** | Content complete (beta) | All content in. All endings reachable. Linter PASS. **Zero open severity-A bugs.** Full fun audit P0 passes |
| **G3** | Polish / ship (gold) | Zero bug bounce (no open bugs older than one cycle, nothing above C). Art and VO finals. Cert-style checklist (README, licence, setup on a clean machine). Postmortem written |

A gate packet is ≤ 300 words: decisions needed (each with a recommendation), evidence links,
risks, and a **kill/continue** recommendation. Killing a weak direction early is allowed and
encouraged, the way Supercell celebrates a cancelled game.

## 5. Parallel lanes (who can run at once)
```
G0  research ∥ creative-director (pillars)                        → gate packet
M1  narrative (writers-room → narrative-lead → story-auditor ×3) ∥ systems-designer
    then art-director ∥ vo-director ∥ engineer (scaffold + offline engine)
    then character-artist ∥ ui-designer ∥ engineer lanes (worktrees) ∥ blender-artist (pro)
    qa-lead from the first build onward
M2  content lanes ∥ engineer lanes ∥ art finals (render-wrangler, pro) ; qa bugs → engineer
M3  polish lanes ; qa zero-bug-bounce ; producer postmortem
```
**Dependencies are tickets.** Nothing starts before its deps are approved.

## 6. Which Claude Code features this uses (only real ones)
- **Sub-agents** (`agents/*.md` with name, description, tools, model) are run by the Producer through
  the Agent tool. **Several Agent calls in one message run in parallel.** Each sub-agent has its own
  context window and returns one report.
- **Git worktrees for parallel engineers.** `isolation: worktree` on an agent definition, or
  `claude -w <name>` for a manual session, gives each engineer lane its own checkout and branch. The
  Producer merges.
- **Nesting.** The Producer does all the spawning. Departments don't spawn departments, which keeps the
  org chart flat and the cost predictable. (Agent-team teammates can't spawn teammates at all.)
- **Studio floor mode** (optional, for filming): every employee runs as its own interactive
  `claude --agent game-studio:<role>` session in a colour-coded iTerm2 or tmux pane, and each one works
  its queue on the shared board. See `floor` below. Coordination is **only through the board file**,
  so it works the same in every terminal.
- **Agent teams** (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) are an alternative floor:
  native split panes, a shared task list and messaging. Use them only if you've enabled the flag.
  The board stays the source of truth either way.

## 7. Studio floor protocol (each employee, in its own pane)
```
loop:
  t = board.py next --owner <me>          (or --lane <my lane>)
  if none: write "idle" in STATUS.md, wait 60 s (or end if the producer said end of cycle)
  board.py claim t --by <me>
  do the work → write outputs → board.py submit t --by <me> --note "<what, where>"
  if I'm a reviewer: board.py list --status in_review --lane <lanes I review> → review each one
```
The pane title is the role. The background colour is the lane colour. Every board transition prints
one line, so the camera can see work move.

## Sources
Studio practice:
- Clinton Keith, *Agile Game Development*, via https://cs.ccsu.edu/~stan/classes/CS415/notes/02-Scrum.html
- Scrum Guide: https://scrumguides.org/scrum-guide.html
- Milestone criteria (Mullich): https://www.gamedeveloper.com/production/milestones-and-glass-houses-preventing-your-development-schedule-from-shattering-part-1
- Vertical slice bar: https://beckinteractivepartners.substack.com/p/the-vertical-slice-meta-part-1-we
- Asset statuses: https://caveacademy.com/wiki/production/production-statuses/
- Art review loop: https://www.gamedeveloper.com/art/2d-game-art-work-feedbacking-and-management-tool
- Writers' room: https://www.gamedeveloper.com/design/leading-a-game-writer-s-room
- Table reads: https://gdcvault.com/play/1035928/Page-to-Booth-Table-Reading
- Bug lifecycle and severity: https://www.moddb.com/tutorials/mod-testers-handbook
- Zero Bug Bounce: https://docs.microsoft.com/en-us/archive/blogs/somasegar/zero-bug-bounce/
- Supercell cells: https://supercell.com/en/news/level-two-freedom-and-responsibility/7623/
- Valve cabals: https://media.steampowered.com/apps/valve/Valve_Handbook_LowRes.pdf
- Fortnite Battle Royale built by a borrowed team in about 2 months: https://www.pcgamer.com/fortnite-battle-royale-was-developed-in-just-two-months-and-wasnt-originally-going-to-be-free-to-play/

Claude Code:
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/agent-teams.md
- https://code.claude.com/docs/en/worktrees.md
- https://code.claude.com/docs/en/plugins/manifest-reference.md
