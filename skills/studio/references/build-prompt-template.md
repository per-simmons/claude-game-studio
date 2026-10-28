# Build-prompt template (Producer + Engineer lead)

This is the handoff prompt a fresh build agent, or team, builds from. It's self-contained: it points
at the approved design documents and never re-explains them. Worked example:
`examples/case-packs/dead-air-on-the-meridian/BUILD-PROMPT.md`.

```markdown
# BUILD PROMPT: "<title>"
## 0. Mission — what it is, the core skill, the quality bar ("exceptional"; filmable)
## 1. Source documents — table: file | what | authority (design/content/eng/voice/art truth). "Don't redesign."
## 2. Hard rules — external APIs off/on, IP, competitor names, blind/tool-agnostic UI, image gen route
   (from config), LLM route + offline mode, never steal focus, recording guard (optional), don't touch other agents,
   GPU cost caps, facts from sources
## 3. File layout — exact tree under <your-game>/ (prompt.md copy, docs/ mirrors, content/, server/,
   src/, scripts/, tests/, blender/, art/, bin/, qa/)
## 4. Team — lanes with ownership + start milestone
## 5. Milestones — M0 scaffold · M1 content-as-data + linter · M2 first playable (CLI + placeholder) ·
   M3 VERTICAL SLICE (stop for the publisher) · M4 full content · M5 art (stop for the publisher) · M6 external-service-ready
   behind a flag · M7 QA + fun audit + video mode. Each with checkbox acceptance criteria.
## 6. QA gates — unit, content linter, headless e2e with screenshots, speedrun/brute-force thresholds,
   red-team, latency, fun audit, vision QA of screenshots
## 7. Definition of done
## 8. Reporting — per-milestone README append; final ≤300-word report; no claims without evidence
```

**Rules for writing it:**
- Every acceptance criterion is checkable by a test, a screenshot or a number.
- The first stop is the **vertical slice**: all systems working in one act, at near-final quality.
- Put the **offline/deterministic mode** in M2, so every bot and QA gate runs without paid APIs.
- Copy the prompt into the build folder as `prompt.md` (convention: the build folder keeps the prompt it was built from).
