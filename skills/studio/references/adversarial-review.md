# Adversarial review: the prompts that broke Case 1 and then fixed it

Run all three as **independent sub-agents in parallel** on the narrative bible. They read it and never
edit it. The Narrative Designer applies the fixes and logs them in the bible's review section. Then
run reviewer C again on the revision.

## A. The speed-solver and exploiter
> You are an adversarial playtester. Read <bible>. Do not edit.
> **Pass 1, genre-savvy player.** See only what a player sees at the start. Using genre
> meta-knowledge (least-likely suspect, helpful assistant, neighbouring rooms, conspicuous absences),
> list each early signal that gives the culprit away and rate how much it leaks, 1–5. Compute the
> SHORTEST action path to a valid accusation: count the actions and estimate game minutes and real
> minutes. If it's under 10 real minutes, it's too easy.
> **Pass 2, exploiter.** Brute-force the accusation. Present every card against every claim. Find
> universal-key questions. Try LLM jailbreak angles. Find any single clue that trivialises the case.
> Return prioritised fixes (P0/P1/P2) with exact text. Keep them fair (Knox, Van Dine, the Three Clue
> Rule) and preserve the twist. Under 1,500 words.

## B. The story editor
> Read <bible>. Do not edit. Hunt for plot holes:
> (1) a minute-by-minute physical walk-through. Could each person really be there, and who would see
> whom?
> (2) motive and causality: why didn't X do the obvious thing?
> (3) period accuracy and anachronisms;
> (4) physical clue logic;
> (5) IP risk, comparing structurally with the famous works of the subgenre (name them) and flagging
> stacked combinations;
> (6) sensitivity in period portrayal and in sponsored-content risk.
> Return P0/P1/P2 holes with minimal fixes and exact replacement text. Under 1,500 words.

## C. The consistency auditor (run after the fixes)
> Read <bible>, revision N. Do not edit. Find contradictions the revision introduced: timeline vs
> character sections vs evidence vs lies vs the solution key vs the branching map vs endings. Check
> that every ID referenced exists. Check that each proof category has at least 3 independent routes
> with the optional branches off. Re-check the minimal-path claim and Act I leaks. Return concrete
> issues with exact fix text, under 700 words, or say it's clean.

**What these found on Case 1** (so you know what to expect):
- A first-room clue named the killer.
- A "universal key" question opened every alibi.
- A conspicuous absence gave the killer away.
- A witness at the end of the corridor would have seen everything.
- Two characters would have walked into each other.
- A forgotten crew member was also a witness.
- A stack of elements echoed a famous train novel.
- A period-sensitivity problem.
