#!/usr/bin/env python3
"""Studio board: the shared ticket board every employee (sub-agent) reads and writes.

Python 3.9+ standard library only. One JSON file (studio/board.json) is the source of truth;
studio/BOARD.md is a rendered view for humans and cameras. Every write takes an exclusive file
lock, so parallel employees can claim tickets safely.

Ticket lifecycle (mirrors a ShotGrid/ftrack-style asset status machine):
  backlog -> ready -> in_progress -> in_review -> approved -> done
                         ^               |
                         +-- changes_requested
  any -> blocked (with reason) ; blocked -> ready
Bugs (type=bug): new -> triaged -> assigned -> fixed -> verified -> closed (reason: fixed |
as-designed | waived | duplicate | cannot-reproduce). Severity A-D is kept apart from priority
P0-P3, and only the producer or qa-lead sets priority.

Usage (run from the game project root, or pass --board):
  board.py init --game "<title>"
  board.py add "<title>" --lane narrative --owner writers-room [--reviewer narrative-lead]
               [--deps T-001,T-002] [--milestone M1] [--priority P1] [--out path ...] [--type task|asset|review|gate]
  board.py bug "<title>" --severity B --repro "<steps from boot>" [--owner engineer] [--found-by qa-lead]
  board.py next --lane narrative            # first READY ticket whose deps are all done/approved
  board.py claim T-004 --by writers-room    # ready -> in_progress (fails if deps not met)
  board.py submit T-004 --by writers-room --note "draft at studio/NARRATIVE.md"   # -> in_review
  board.py review T-004 --by narrative-lead --approve [--note ...]   |  --changes "<notes>"
  board.py done T-004 --by producer
  board.py block T-004 --by engineer --reason "<why>"   |   board.py unblock T-004
  board.py bugstate B-002 fixed|verified|closed --by qa-lead [--reason fixed]
  board.py list [--lane X] [--status Y] [--milestone M1] [--json]
  board.py render                           # writes BOARD.md
  board.py standup                          # prints a per-lane yesterday/today/blockers digest
  board.py check                            # validates deps, cycles, owners, stale reviews
"""
import argparse
import datetime as dt
import fcntl
import json
import os
import sys
from contextlib import contextmanager

STATUSES = ["backlog", "ready", "in_progress", "in_review", "changes_requested", "approved", "done", "blocked"]
BUG_STATES = ["new", "triaged", "assigned", "fixed", "verified", "closed"]
CLOSE_REASONS = ["fixed", "as-designed", "waived", "duplicate", "cannot-reproduce"]
DONEISH = {"approved", "done", "closed", "verified"}
LANES = ["production", "creative", "research", "narrative", "systems", "art", "character", "blender",
         "render", "ui", "vo", "engineering", "qa"]


def now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def find_board(path):
    if path:
        return path
    here = os.getcwd()
    while True:
        cand = os.path.join(here, "studio", "board.json")
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(here)
        if parent == here:
            return os.path.join(os.getcwd(), "studio", "board.json")
        here = parent


@contextmanager
def locked(path, write=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lock = open(path + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
    try:
        data = json.load(open(path)) if os.path.exists(path) else None
        box = {"data": data}
        yield box
        if write and box["data"] is not None:
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(box["data"], f, indent=2)
            os.replace(tmp, path)
            render(box["data"], os.path.join(os.path.dirname(path), "BOARD.md"))
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def die(msg):
    print("board: " + msg, file=sys.stderr)
    sys.exit(1)


def get(data, tid):
    for t in data["tickets"]:
        if t["id"] == tid:
            return t
    die("no ticket %s" % tid)


def note(t, by, text, kind="note"):
    t.setdefault("notes", []).append({"at": now(), "by": by, "kind": kind, "text": text})
    t["updated"] = now()


def deps_met(data, t):
    missing = []
    for d in t.get("deps", []):
        dt_ = next((x for x in data["tickets"] if x["id"] == d), None)
        if dt_ is None or dt_["status"] not in DONEISH:
            missing.append(d)
    return missing


def new_id(data, prefix):
    n = 1 + max([int(t["id"].split("-")[1]) for t in data["tickets"] if t["id"].startswith(prefix + "-")] or [0])
    return "%s-%03d" % (prefix, n)


def render(data, out):
    lines = ["# Studio board: %s" % data.get("game", "untitled"),
             "", "_Rendered %s from board.json. Do not edit by hand; use `board.py`._" % now(), "",
             "Milestone: **%s**" % data.get("milestone", "M0"), ""]
    cols = ["ready", "in_progress", "in_review", "changes_requested", "blocked", "approved", "done"]
    for c in cols:
        ts = [t for t in data["tickets"] if t["status"] == c and t.get("type") != "bug"]
        if not ts:
            continue
        lines.append("## %s (%d)" % (c.replace("_", " ").upper(), len(ts)))
        lines.append("| id | lane | owner | title | deps | reviewer | round |")
        lines.append("|---|---|---|---|---|---|---|")
        for t in ts:
            lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                t["id"], t.get("lane", ""), t.get("owner", ""), t["title"], ",".join(t.get("deps", [])),
                t.get("reviewer") or "", t.get("review_round", 0)))
        lines.append("")
    bugs = [t for t in data["tickets"] if t.get("type") == "bug" and t["status"] != "closed"]
    if bugs:
        lines += ["## OPEN BUGS (%d)" % len(bugs), "| id | sev | pri | state | owner | title |", "|---|---|---|---|---|---|"]
        for b in bugs:
            lines.append("| %s | %s | %s | %s | %s | %s |" % (b["id"], b.get("severity", ""), b.get("priority", ""),
                                                       b["status"], b.get("owner", ""), b["title"]))
        lines.append("")
    backlog = [t for t in data["tickets"] if t["status"] == "backlog"]
    if backlog:
        lines += ["## BACKLOG (%d)" % len(backlog)] + ["- %s %s (%s)" % (t["id"], t["title"], t.get("lane", "")) for t in backlog] + [""]
    with open(out, "w") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--game", required=True)
    p = sub.add_parser("add"); p.add_argument("title"); p.add_argument("--lane", required=True)
    p.add_argument("--owner", required=True); p.add_argument("--reviewer"); p.add_argument("--deps", default="")
    p.add_argument("--milestone"); p.add_argument("--priority", default="P2"); p.add_argument("--out", nargs="*", default=[])
    p.add_argument("--type", default="task", choices=["task", "asset", "review", "gate"]); p.add_argument("--status", default="ready")
    p.add_argument("--desc", default="")
    p = sub.add_parser("bug"); p.add_argument("title"); p.add_argument("--severity", required=True, choices=list("ABCD"))
    p.add_argument("--repro", required=True); p.add_argument("--owner", default="engineer"); p.add_argument("--found-by", default="qa-lead")
    p.add_argument("--priority", default="P1")
    p = sub.add_parser("next"); p.add_argument("--lane"); p.add_argument("--owner")
    for name in ("claim", "submit", "done", "unblock"):
        p = sub.add_parser(name); p.add_argument("id"); p.add_argument("--by", default="producer"); p.add_argument("--note", default="")
    p = sub.add_parser("review"); p.add_argument("id"); p.add_argument("--by", required=True)
    g = p.add_mutually_exclusive_group(required=True); g.add_argument("--approve", action="store_true"); g.add_argument("--changes")
    p.add_argument("--note", default="")
    p = sub.add_parser("block"); p.add_argument("id"); p.add_argument("--by", required=True); p.add_argument("--reason", required=True)
    p = sub.add_parser("bugstate"); p.add_argument("id"); p.add_argument("state", choices=BUG_STATES)
    p.add_argument("--by", required=True); p.add_argument("--reason", choices=CLOSE_REASONS); p.add_argument("--note", default="")
    p = sub.add_parser("milestone"); p.add_argument("name")
    p = sub.add_parser("list"); p.add_argument("--lane"); p.add_argument("--status"); p.add_argument("--milestone"); p.add_argument("--json", action="store_true")
    sub.add_parser("render"); sub.add_parser("standup"); sub.add_parser("check")
    a = ap.parse_args()
    path = find_board(a.board)

    if a.cmd == "init":
        if os.path.exists(path):
            die("board already exists at %s" % path)
        with locked(path) as box:
            box["data"] = {"game": a.game, "milestone": "M0", "created": now(), "tickets": []}
        print(path)
        return

    with locked(path, write=a.cmd not in ("list", "next", "standup", "check")) as box:
        data = box["data"]
        if data is None:
            die("no board at %s (run: board.py init --game ...)" % path)
        c = a.cmd
        if c == "add":
            t = {"id": new_id(data, "T"), "title": a.title, "type": a.type, "lane": a.lane, "owner": a.owner,
                 "reviewer": a.reviewer, "deps": [d for d in a.deps.split(",") if d], "milestone": a.milestone or data["milestone"],
                 "priority": a.priority, "status": a.status, "outputs": a.out, "desc": a.desc, "review_round": 0,
                 "created": now(), "updated": now(), "notes": []}
            data["tickets"].append(t); print(t["id"])
        elif c == "bug":
            t = {"id": new_id(data, "B"), "title": a.title, "type": "bug", "lane": "engineering", "owner": a.owner,
                 "severity": a.severity, "priority": a.priority, "status": "new", "repro": a.repro,
                 "found_by": a.found_by, "milestone": data["milestone"], "created": now(), "updated": now(), "notes": []}
            data["tickets"].append(t); print(t["id"])
        elif c == "next":
            for t in data["tickets"]:
                if t["status"] in ("ready", "changes_requested") and (not a.lane or t.get("lane") == a.lane) \
                        and (not a.owner or t.get("owner") == a.owner) and not deps_met(data, t):
                    print(json.dumps(t, indent=2)); return
            print("{}")
        elif c == "claim":
            t = get(data, a.id)
            if t["status"] not in ("ready", "changes_requested"):
                die("%s is %s, not ready" % (t["id"], t["status"]))
            miss = deps_met(data, t)
            if miss:
                die("%s waits on %s" % (t["id"], ",".join(miss)))
            t["status"] = "in_progress"; t["owner"] = a.by; note(t, a.by, a.note or "claimed", "claim")
        elif c == "submit":
            t = get(data, a.id); t["status"] = "in_review" if t.get("reviewer") else "approved"
            note(t, a.by, a.note or "submitted", "submit")
        elif c == "review":
            t = get(data, a.id)
            if t["status"] != "in_review":
                die("%s is not in review" % t["id"])
            if a.by == t.get("owner"):
                die("owners cannot review their own work")
            t["review_round"] = t.get("review_round", 0) + 1
            if a.approve:
                t["status"] = "approved"; note(t, a.by, a.note or "approved", "approve")
            else:
                t["status"] = "changes_requested"; note(t, a.by, a.changes, "changes")
        elif c == "done":
            t = get(data, a.id); t["status"] = "done"; note(t, a.by, a.note or "done", "done")
        elif c == "block":
            t = get(data, a.id); t["prev_status"] = t["status"]; t["status"] = "blocked"; note(t, a.by, a.reason, "block")
        elif c == "unblock":
            t = get(data, a.id); t["status"] = t.pop("prev_status", "ready"); note(t, a.by, a.note or "unblocked", "unblock")
        elif c == "bugstate":
            t = get(data, a.id)
            if a.state == "closed" and not a.reason:
                die("closing a bug needs --reason")
            t["status"] = a.state
            if a.reason:
                t["close_reason"] = a.reason
            note(t, a.by, a.note or a.state, "bug")
        elif c == "milestone":
            data["milestone"] = a.name; print("milestone ->", a.name)
        elif c == "list":
            ts = [t for t in data["tickets"] if (not a.lane or t.get("lane") == a.lane)
                  and (not a.status or t["status"] == a.status) and (not a.milestone or t.get("milestone") == a.milestone)]
            if a.json:
                print(json.dumps(ts, indent=2))
            else:
                for t in ts:
                    print("%-6s %-18s %-14s %-16s %s" % (t["id"], t["status"], t.get("lane", ""), t.get("owner", ""), t["title"]))
        elif c == "render":
            render(data, os.path.join(os.path.dirname(path), "BOARD.md")); print("rendered")
        elif c == "standup":
            today = dt.date.today().isoformat()
            lanes = sorted({t.get("lane", "") for t in data["tickets"]})
            for ln in lanes:
                ts = [t for t in data["tickets"] if t.get("lane") == ln]
                moved = [t for t in ts if any(n["at"].startswith(today) for n in t.get("notes", []))]
                doing = [t for t in ts if t["status"] in ("in_progress", "changes_requested")]
                blocked = [t for t in ts if t["status"] == "blocked"]
                print("### %s" % ln)
                print("- moved today: " + (", ".join("%s (%s)" % (t["id"], t["status"]) for t in moved) or "nothing"))
                print("- doing next: " + (", ".join("%s %s" % (t["id"], t["title"]) for t in doing) or "nothing in progress"))
                print("- blockers: " + (", ".join("%s: %s" % (t["id"], t["notes"][-1]["text"]) for t in blocked) or "none"))
        elif c == "check":
            ids = {t["id"] for t in data["tickets"]}
            problems = []
            for t in data["tickets"]:
                for d in t.get("deps", []):
                    if d not in ids:
                        problems.append("%s depends on missing %s" % (t["id"], d))
                if t["status"] == "in_review" and not t.get("reviewer"):
                    problems.append("%s in review with no reviewer" % t["id"])
                if t.get("review_round", 0) >= 3 and t["status"] == "changes_requested":
                    problems.append("%s on review round %d: escalate to producer" % (t["id"], t["review_round"]))
            # cycle check
            graph = {t["id"]: t.get("deps", []) for t in data["tickets"]}
            seen, stack = set(), set()

            def visit(n):
                if n in stack:
                    problems.append("dependency cycle at %s" % n); return
                if n in seen:
                    return
                seen.add(n); stack.add(n)
                for m in graph.get(n, []):
                    visit(m)
                stack.discard(n)
            for n in graph:
                visit(n)
            print("\n".join(problems) or "board OK")
            sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
