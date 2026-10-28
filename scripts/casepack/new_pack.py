#!/usr/bin/env python3
"""Scaffold an empty case pack.

    python3 scripts/casepack/new_pack.py <dir> [--title "My Case"] [--premise "..."]

Writes casepack.json, a case-file.json skeleton (one of everything, with TODOs) and a README.md.
The skeleton is deliberately incomplete: run lint.py on it to see what's left to write.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "new-case"


def skeleton(pack_id, title, premise):
    line = lambda i, t, d=None: dict({"id": i, "text": t}, **({"direction": d} if d else {}))  # noqa: E731
    return {
        "meta": {"id": pack_id, "title": title, "version": "0.1.0", "setting": "TODO: where and when.",
                 "ip_notes": "TODO: what you deliberately kept distant from existing works.",
                 "content_rating": "TODO"},
        "clock": {"start": 1320, "deadline": 1500, "time_base": "local time",
                  "costs": {"ASK": 3, "FOLLOW_UP": 2, "PRESS": 4, "REASSURE": 3, "THREATEN": 4, "SMALL_TALK": 1,
                            "PRESENT": 5, "CONFRONT": 5, "EXAMINE": 4, "SEARCH": 10, "FETCH": 2},
                  "scheduled": [], "withdraw_after_misses": 3, "withdraw_minutes": 20},
        "places": [{"id": "P-SCENE", "name": "the scene", "hotspots": [
            {"id": "body", "label": "the body", "reveals": ["E-FIRST"]}]}],
        "characters": [
            {"id": "CH-VIC", "name": "TODO Victim", "role": "victim", "accusable": False,
             "public": {"summary": "TODO", "public_facts": []}, "secret": {"summary": "TODO"},
             "voice": {"design_instruction": "Not heard."},
             "baseline": {"composure": 50, "trust": 50, "direction": ""}, "tells": {}},
            {"id": "CH-KIL", "name": "TODO Killer", "role": "killer", "aliases": [],
             "public": {"summary": "TODO", "public_facts": []}, "secret": {"summary": "TODO"},
             "voice": {"design_instruction": "TODO"},
             "baseline": {"composure": 80, "trust": 50, "direction": "calm"},
             "tells": {"lie": "TODO"},
             "locks": [{"id": "alibi", "category": "alibi"}, {"id": "motive", "category": "motive"},
                       {"id": "physical", "category": "physical"}]},
            {"id": "CH-PAR", "name": "TODO Partner", "role": "partner", "accusable": False,
             "public": {"summary": "Your partner.", "public_facts": []}, "secret": {"summary": "None."},
             "voice": {"design_instruction": "TODO"},
             "baseline": {"composure": 80, "trust": 70, "direction": "practical"}, "tells": {}}],
        "cards": [
            {"id": "E-FIRST", "kind": "evidence", "title": "TODO first clue", "description": "TODO",
             "role": "supporting", "act": 1, "keywords": []},
            {"id": "C-ALIBI", "kind": "contradiction", "title": "TODO alibi falls", "description": "TODO",
             "role": "essential", "proof_category": "alibi", "act": 2},
            {"id": "C-MOTIVE", "kind": "contradiction", "title": "TODO motive", "description": "TODO",
             "role": "essential", "proof_category": "motive", "act": 2},
            {"id": "C-PHYSICAL", "kind": "contradiction", "title": "TODO physical proof", "description": "TODO",
             "role": "essential", "proof_category": "physical", "act": 2}],
        "claims": [{"id": "CL-KIL-1", "speaker": "CH-KIL", "text": "TODO the killer's alibi", "is_true": False,
                    "heard_via": "B-KIL-WHERE"}],
        "contradictions": [{"id": "C-X-ALIBI", "claim": "CL-KIL-1", "cards": ["E-FIRST"],
                            "result_beat": "B-KIL-CRACK", "creates_card": "C-ALIBI", "composure_delta": -15,
                            "opens_lock": "alibi"}],
        "links": [],
        "storylets": [
            {"id": "B-KIL-WHERE", "char": "CH-KIL", "topic": "whereabouts", "mode": "authored",
             "lines": [line("L-KIL-WHERE-1", "TODO: where I was.", "rehearsed")], "utters_claims": ["CL-KIL-1"]},
            {"id": "B-KIL-CRACK", "char": "CH-KIL", "topic": "whereabouts", "mode": "authored", "intents": ["PRESENT"],
             "lines": [line("L-KIL-CRACK-1", "TODO: the crack.", "a breath too long")]},
            {"id": "B-PAR-HINT", "char": "CH-PAR", "topic": "*", "mode": "authored", "priority": -1,
             "intents": ["ASK", "FOLLOW_UP", "SMALL_TALK"], "lines": [line("L-PAR-HINT-1", "TODO: a hint.")]},
            {"id": "B-END-TRUE", "char": "CH-PAR", "topic": "*", "mode": "authored", "intents": ["ACCUSE"],
             "lines": [line("L-END-TRUE-1", "TODO: the true ending.")]},
            {"id": "B-END-WRONG", "char": "CH-PAR", "topic": "*", "mode": "authored", "intents": ["ACCUSE"],
             "lines": [line("L-END-WRONG-1", "TODO: right person, weak case.")]},
            {"id": "B-END-TIME", "char": "CH-PAR", "topic": "*", "mode": "authored", "intents": ["SCHEDULED"],
             "lines": [line("L-END-TIME-1", "TODO: out of time.")]}],
        "solution": {"who": "CH-KIL", "how": ["TODO how"], "when": ["TODO when"], "why": ["TODO why"],
                     "proof": {"alibi": ["C-ALIBI"], "motive": ["C-MOTIVE"], "physical": ["C-PHYSICAL"]},
                     "decoys": {"how": [], "when": [], "why": []}},
        "endings": [
            {"id": "END-TRUE", "title": "TODO", "condition": "TRUE_SOLUTION", "beat": "B-END-TRUE", "epilogue_choices": []},
            {"id": "END-WEAK", "title": "TODO", "condition": "RIGHT_WHO_WRONG_CASE", "beat": "B-END-WRONG"},
            {"id": "END-TIME", "title": "TODO", "condition": "TIMEOUT", "beat": "B-END-TIME"}],
        "timeline": [{"t": 1290, "event": "TODO: the murder.", "who": ["CH-KIL", "CH-VIC"]}],
        "hunch": [],
        "refusals": {"*": {"META": [line("R-META-1", "I don't follow you.", "puzzled")],
                           "DEMAND_CONFESSION": [line("R-CONF-1", "Confess? To what?", "offended")],
                           "*": [line("R-ANY-1", "I've nothing more to say about that.", "closed")]}},
        "topics": [{"id": "whereabouts", "label": "Where they were",
                    "keywords": ["where", "were you", "tonight", "alibi", "doing"]}],
        "choices": [],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scaffold an empty case pack.")
    ap.add_argument("dir")
    ap.add_argument("--title")
    ap.add_argument("--premise", default="TODO: one-line premise.")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    a = ap.parse_args(argv)
    d = os.path.abspath(a.dir)
    pack_id = slug(os.path.basename(d))
    title = a.title or os.path.basename(d).replace("-", " ").title()
    os.makedirs(d, exist_ok=True)
    manifest = {
        "format": "casepack/1", "id": pack_id, "title": title, "premise": a.premise,
        "blurb": "TODO: a spoiler-free blurb.", "version": "0.1.0", "authors": ["TODO"],
        "license": "CC-BY-4.0", "content_rating": "TODO", "play_minutes": [20, 40],
        "case_file": "case-file.json",
        "voices": {"provider_default": "placeholder", "fish_voice_ids": {}},
        "art": {"style": "TODO", "portraits": "art/portraits", "scenes": "art/scenes"},
        "spoiler_files": ["NARRATIVE.md", "case-file.json"],
        "lint": {"passed": False, "linter_version": "1", "min_path_actions": 16},
    }
    readme = ("# %s\n\n%s\n\nTODO: a spoiler-free blurb.\n\n## How to play\n\n```bash\n"
              "python3 scripts/casepack/play.py %s\n```\n\nCheck it: `python3 scripts/casepack/lint.py %s`\n\n"
              "`case-file.json` holds the solution. Don't read it before you play.\n" % (title, a.premise, a.dir, a.dir))
    files = {"casepack.json": manifest, "case-file.json": skeleton(pack_id, title, a.premise), "README.md": readme}
    for name, content in files.items():
        path = os.path.join(d, name)
        if os.path.exists(path) and not a.force:
            print("exists, skipped: %s (use --force)" % path)
            continue
        with open(path, "w", encoding="utf-8") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                json.dump(content, f, indent=2, ensure_ascii=False)
                f.write("\n")
        print("wrote %s" % path)
    print("Next: fill in the TODOs, then run  python3 scripts/casepack/lint.py %s" % a.dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
