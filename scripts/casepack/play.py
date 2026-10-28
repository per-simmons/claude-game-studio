#!/usr/bin/env python3
"""Play a case pack in your terminal. Free, offline, standard library only.

    python3 scripts/casepack/play.py <pack-dir>
    python3 scripts/casepack/play.py <pack-dir> --autoplay-solution      # watch it solve itself
    python3 scripts/casepack/play.py <pack-dir> --script cmds.txt         # replay typed commands
    options: --seed N   --no-color   --log events.jsonl

Type `help` in the game for the commands.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E  # noqa: E402

PALETTE = ["\033[38;5;214m", "\033[38;5;81m", "\033[38;5;177m", "\033[38;5;114m", "\033[38;5;209m",
           "\033[38;5;147m", "\033[38;5;222m", "\033[38;5;44m", "\033[38;5;204m", "\033[38;5;156m"]
RESET, BOLD, DIM, ITAL = "\033[0m", "\033[1m", "\033[2m", "\033[3m"
RED, GREEN, YELLOW, MAGENTA, CYAN, GREY = ("\033[38;5;203m", "\033[38;5;120m", "\033[38;5;221m",
                                           "\033[38;5;176m", "\033[38;5;87m", "\033[38;5;245m")

HELP = """\
GETTING AROUND
  look                      where you are, what you can examine, who's here
  go <place>                walk somewhere (free)
  examine <thing>           look closely at something        (x <thing>)
  search                    search the room you're in
TALKING
  talk <name>               start talking to someone          (bye to stop)
  then just type a question:   where were you at ten?   tell me about the maps
  ask <topic>  follow  press [topic]  reassure  threaten
  present <card> to <claim> show evidence that contradicts what they said
  confront <claim> <claim>  set two statements against each other
THINKING
  notebook [people|evidence|claims|transcript]     (nb)
  find <word>               search everything you've heard and found
  board                     your cards; link <card> <card> to connect two
  time                      the clock, and the deadline
  wait [minutes]            let time pass
DECIDING
  choose                    decisions that are open to you
  accuse                    name the killer (a short guided form)
  quit
Cards and claims can be named by ID (E-GLOVE, CL-TOB-LIB) or by a word from them (glove)."""


def shown_role(ch):
    """Never reveal the killer: players see 'suspect'."""
    return "suspect" if ch.get("role") == "killer" else ch.get("role")


class Reader:
    def __init__(self, script=None, echo=False):
        self.lines = None
        if script:
            with open(script, encoding="utf-8") as f:
                self.lines = [ln.rstrip("\n") for ln in f if not ln.lstrip().startswith("#")]
        self.echo = echo

    def read(self, prompt):
        if self.lines is not None:
            if not self.lines:
                raise EOFError
            ln = self.lines.pop(0)
            print(prompt + ln)
            return ln
        return input(prompt)


class UI:
    def __init__(self, eng, color=True, reader=None, log=None, width=96):
        self.eng = eng
        self.case = eng.case
        self.color = color
        self.reader = reader or Reader()
        self.s, self._opening = eng.start()
        self.log = log
        self.width = width
        self.talking = None
        self.colors = {}
        for i, ch in enumerate(self.case.chars):
            self.colors[ch.get("id")] = PALETTE[i % len(PALETTE)]
        self.quit = False

    # -- output ------------------------------------------------------------------------------
    def c(self, code, text):
        return "%s%s%s" % (code, text, RESET) if self.color else text

    def wrap(self, text, indent=""):
        return textwrap.fill(text, width=self.width, initial_indent=indent, subsequent_indent=indent + "  ")

    def p(self, text=""):
        print(text)

    def render(self, out):
        for o in out:
            k = o["kind"]
            if k == "line":
                spk = o.get("speaker")
                name = o.get("name") or spk
                if spk == "HUNCH":
                    tag = self.c(MAGENTA + BOLD, "HUNCH")
                    body = self.c(MAGENTA + ITAL, o.get("text", ""))
                else:
                    tag = self.c(self.colors.get(spk, CYAN) + BOLD, name.upper())
                    body = o.get("text", "")
                d = o.get("direction")
                dtxt = (" " + self.c(GREY + ITAL, "[%s]" % d)) if d else ""
                self.p(self.wrap("%s%s %s" % (tag, dtxt, body)))
            elif k == "card":
                self.p(self.c(GREEN, "  + New card  %s  %s" % (o["id"], o.get("title", ""))))
                if o.get("description"):
                    self.p(self.c(GREY, self.wrap(o["description"], "      ")))
            elif k == "claim":
                self.p(self.c(YELLOW, "  + Claim noted  %s  %s: \"%s\"" % (
                    o["id"], self.case.short_name(o.get("speaker")), o.get("text", ""))))
            elif k == "broken":
                self.p(self.c(RED + BOLD, "  ! Contradiction! %s is broken." % o["claim"]))
            elif k == "miss":
                self.p(self.c(RED, "  x That didn't land. (%s's trust drops; misses in a row: %d)" % (
                    self.case.short_name(o["char"]), o["streak"])))
            elif k == "withdrawn":
                self.p(self.c(RED, "  x %s has had enough of you and won't talk until %s." % (
                    o["name"], E.fmt_clock(o["until"]))))
                if self.talking == o["char"]:
                    self.talking = None
            elif k == "lock":
                self.p(self.c(CYAN, "  * Something gives in %s: the %s lock is open." % (o["name"], o["lock"])))
            elif k == "flag":
                pass
            elif k in ("info", "error"):
                self.p(self.c(RED if k == "error" else GREY, "  " + o["text"]))
            elif k == "moved":
                self.p(self.c(GREY, "  You go to %s." % o["name"]))
            elif k == "ending":
                self.p()
                self.p(self.c(BOLD, "=" * 60))
                self.p(self.c(BOLD, "  ENDING: %s" % o.get("title")))
                self.p(self.c(BOLD, "=" * 60))

    def apply(self, ev, show=True):
        s2, out = self.eng.step(self.s, ev)
        ok = not (s2 is self.s and any(o["kind"] == "error" for o in out))
        if self.log and ok:
            self.log.write(json.dumps({"seq": s2.actions, "clock": s2.clock, "event": ev}) + "\n")
            self.log.flush()
        self.s = s2
        if show:
            self.render(out)
        return out

    # -- resolution helpers -------------------------------------------------------------------
    def find_char(self, text, talkable=True, exact=False):
        t = E.norm(text)
        if not t:
            return None
        names = {}
        for ch in self.case.chars:
            cid = ch.get("id")
            if talkable and not self.case.talkable(cid):
                continue
            opts = {E.norm(cid), E.norm(cid.split("-", 1)[-1]), E.norm(ch.get("name", ""))}
            opts |= {E.norm(a) for a in ch.get("aliases", []) or []}
            for part in E.norm(ch.get("name", "")).split():
                if len(part) > 2:
                    opts.add(part)
            for o in opts:
                if o:
                    names[o] = cid
        if t in names:
            return names[t]
        if exact:
            m = difflib.get_close_matches(t, list(names), n=1, cutoff=0.85)
            return names[m[0]] if m else None
        for o, cid in names.items():
            if o in ("you", "me", "i"):
                continue
            if o and (t.startswith(o + " ") or (" " + o + " ") in (" " + t + " ")):
                return cid
        m = difflib.get_close_matches(t, list(names), n=1, cutoff=0.75)
        return names[m[0]] if m else None

    def find_card(self, text, pool=None):
        pool = list(self.s.seen) if pool is None else pool
        t = text.strip()
        for cid in pool:
            if cid.lower() == t.lower() or cid.lower().split("-", 1)[-1] == t.lower():
                return cid
        hit = self.eng.match_card(self.s, t, pool=pool)
        if hit:
            return hit
        titles = {E.norm(self.case.card_by_id[c].get("title", "")): c for c in pool if c in self.case.card_by_id}
        m = difflib.get_close_matches(E.norm(t), list(titles), n=1, cutoff=0.6)
        return titles[m[0]] if m else None

    def find_claim(self, text, speaker=None):
        t = text.strip()
        for clid in self.s.heard:
            if clid.lower() == t.lower() or clid.lower().split("-", 1)[-1] == t.lower():
                return clid
        return self.eng.match_claim(self.s, t, speaker=speaker) or \
            (self.eng.match_claim(self.s, t) if speaker else None)

    def find_topic(self, text):
        t = E.norm(text)
        for tp in self.case.topics:
            if t and t in (E.norm(tp.get("id", "")), E.norm(tp.get("label", ""))):
                return tp.get("id")
        hit = self.eng.match_topic(self.s, text)
        if hit:
            return hit
        labels = {E.norm(tp.get("label", "")): tp.get("id") for tp in self.case.topics}
        m = difflib.get_close_matches(t, list(labels), n=1, cutoff=0.6)
        return labels[m[0]] if m else None

    def find_place(self, text):
        t = E.norm(text)
        opts = {}
        for p in self.case.places:
            opts[E.norm(p.get("id"))] = p.get("id")
            opts[E.norm(p.get("name", ""))] = p.get("id")
            for w in E.norm(p.get("name", "")).split():
                if w not in E.STOP and len(w) > 2:
                    opts.setdefault(w, p.get("id"))
        if t in opts:
            return opts[t]
        for k, v in opts.items():
            if t and (t in k or k in t) and len(k) > 2:
                return v
        m = difflib.get_close_matches(t, list(opts), n=1, cutoff=0.6)
        return opts[m[0]] if m else None

    def find_hotspot(self, text):
        t = E.norm(text)
        here, elsewhere = [], []
        for key, (place, hs) in self.case.hotspots.items():
            names = [E.norm(hs.get("id", "")), E.norm(hs.get("label", ""))]
            score = 0
            for n in names:
                if not n:
                    continue
                if t == n:
                    score = max(score, 10)
                elif t and (t in n or n in t):
                    score = max(score, 5)
                else:
                    common = (set(t.split()) - E.STOP) & (set(n.split()) - E.STOP)
                    score = max(score, len(common) * 2)
            if score:
                (here if place.get("id") == self.s.location else elsewhere).append((score, key))
        for pool in (here, elsewhere):
            if pool:
                return max(pool, key=lambda x: x[0])[1]
        allnames = {E.norm(hs.get("label") or hs.get("id")): k for k, (p, hs) in self.case.hotspots.items()}
        m = difflib.get_close_matches(t, list(allnames), n=1, cutoff=0.6)
        return allnames[m[0]] if m else None

    # -- prompt ------------------------------------------------------------------------------
    def prompt(self):
        clk = self.c(BOLD, E.fmt_clock(self.s.clock))
        where = (self.case.place_by_id.get(self.s.location) or {}).get("name", "")
        who = (" > " + self.c(self.colors.get(self.talking, CYAN), self.case.short_name(self.talking))) if self.talking else ""
        return "\n[%s] %s%s> " % (clk, where, who)

    # -- screens -----------------------------------------------------------------------------
    def intro(self):
        c, m = self.case, self.case.manifest
        self.p(self.c(BOLD, "=" * 60))
        self.p(self.c(BOLD, "  " + c.title.upper()))
        self.p(self.c(BOLD, "=" * 60))
        if c.meta.get("setting"):
            self.p(self.wrap(c.meta["setting"]))
        if m.get("blurb"):
            self.p()
            self.p(self.wrap(m["blurb"]))
        victim = next((ch for ch in c.chars if ch.get("role") == "victim"), None)
        if victim:
            self.p()
            self.p(self.wrap("The victim: %s. %s" % (victim.get("name"), (victim.get("public") or {}).get("summary", ""))))
        self.p()
        self.p(self.wrap("It is %s. The case closes at %s." % (E.fmt_clock(c.start), E.fmt_clock(c.deadline))))
        partner = next((ch for ch in c.chars if ch.get("role") == "partner"), None)
        if partner:
            self.p(self.wrap("Your partner, %s, is with you. Talk to %s when you're stuck." % (
                partner.get("name"), c.short_name(partner.get("id")))))
        self.p(self.c(GREY, "Type help for commands. Type look to get your bearings."))
        if self._opening:
            self.p()
            self.render(self._opening)

    def look(self):
        place = self.case.place_by_id.get(self.s.location) or {}
        self.p(self.c(BOLD, "You are in %s." % place.get("name", "?")))
        spots = place.get("hotspots", []) or []
        if spots:
            items = []
            for h in spots:
                lab = h.get("label") or h.get("id")
                done = all(x in self.s.seen for x in h.get("reveals", []) or [])
                items.append(lab + (" (done)" if done else ""))
            self.p("  You can examine: " + "; ".join(items))
            if any((h.get("action") or "") in E.SEARCH_ACTIONS for h in spots):
                self.p("  This room can be searched (search).")
        others = [p.get("name") for p in self.case.places if p.get("id") != self.s.location]
        if others:
            self.p("  Elsewhere: " + "; ".join(others))
        people = sorted((ch for ch in self.case.chars if self.case.talkable(ch.get("id"))),
                        key=lambda ch: (ch.get("role") == "partner", ch.get("name", "")))
        self.p("  People: " + "; ".join("%s (%s)" % (ch.get("name"), shown_role(ch)) for ch in people))

    def time(self):
        left = self.case.deadline - self.s.clock
        self.p("It's %s. The case closes at %s: %d minutes left. Actions so far: %d." % (
            E.fmt_clock(self.s.clock), E.fmt_clock(self.case.deadline), left, self.s.actions))
        costs = self.case.costs
        if costs:
            self.p(self.c(GREY, "  Costs (minutes): " + ", ".join("%s %s" % (k.lower(), v) for k, v in costs.items() if v)))

    def notebook(self, section=""):
        section = section.strip().lower()
        if section in ("", "people", "p"):
            self.p(self.c(BOLD, "PEOPLE"))
            for ch in sorted(self.case.chars, key=lambda ch: (ch.get("role") != "victim", ch.get("role") == "partner",
                                                              ch.get("name", ""))):
                cid = ch.get("id")
                if not self.case.talkable(cid) and ch.get("role") != "victim":
                    continue
                st = self.s.chars.get(cid, {})
                extra = ""
                if self.case.talkable(cid) and ch.get("role") != "partner":
                    extra = "  [%s]" % self.eng.band(st.get("composure", 50))
                    if self.eng.withdrawn(self.s, cid):
                        extra += " (won't talk until %s)" % E.fmt_clock(st["withdrawn_until"])
                self.p("  " + self.c(self.colors.get(cid, ""), ch.get("name")) + " (%s)%s" % (shown_role(ch), extra))
                self.p(self.c(GREY, self.wrap((ch.get("public") or {}).get("summary", ""), "      ")))
        if section in ("", "evidence", "cards", "e"):
            self.p(self.c(BOLD, "EVIDENCE & TESTIMONY"))
            if not self.s.seen:
                self.p("  (nothing yet)")
            for cid in self.s.seen:
                cd = self.case.card_by_id[cid]
                self.p("  %s  %s  %s" % (self.c(GREEN, cid), cd.get("title"), self.c(GREY, "(" + cd.get("kind", "") + ")")))
                self.p(self.c(GREY, self.wrap(cd.get("description", ""), "      ")))
        if section in ("", "claims", "c"):
            self.p(self.c(BOLD, "CLAIMS"))
            if not self.s.heard:
                self.p("  (nobody has told you anything yet)")
            for clid in self.s.heard:
                cl = self.case.claim_by_id[clid]
                mark = self.c(RED, " BROKEN") if clid in self.s.broken else ""
                self.p("  %s  %s: \"%s\"%s" % (self.c(YELLOW, clid), self.case.short_name(cl.get("speaker")),
                                               cl.get("text"), mark))
        if section in ("transcript", "t"):
            self.p(self.c(BOLD, "TRANSCRIPT"))
            for ln in self.s.transcript[-40:]:
                self.p(self.wrap("  %s %s: %s" % (E.fmt_clock(ln["t"]), ln["name"], ln["text"])))
        if section and section not in ("people", "p", "evidence", "cards", "e", "claims", "c", "transcript", "t"):
            self.p("Sections: people, evidence, claims, transcript.")

    def find(self, word):
        w = word.strip().lower()
        if not w:
            self.p("find <word>")
            return
        n = 0
        for ln in self.s.transcript:
            if w in ln["text"].lower():
                self.p(self.wrap("  %s %s: %s" % (E.fmt_clock(ln["t"]), ln["name"], ln["text"])))
                n += 1
        for cid in self.s.seen:
            cd = self.case.card_by_id[cid]
            if w in (cd.get("title", "") + " " + cd.get("description", "")).lower():
                self.p("  card %s  %s" % (cid, cd.get("title")))
                n += 1
        for clid in self.s.heard:
            if w in self.case.claim_by_id[clid].get("text", "").lower():
                self.p("  claim %s  %s" % (clid, self.case.claim_by_id[clid].get("text")))
                n += 1
        if not n:
            self.p("  Nothing mentions %r." % word)

    def board(self):
        self.p(self.c(BOLD, "THE BOARD"))
        for kind in ("evidence", "testimony", "contradiction"):
            ids = [c for c in self.s.seen if self.case.card_by_id[c].get("kind") == kind]
            if ids:
                self.p("  %s: %s" % (kind, ", ".join("%s (%s)" % (c, self.case.card_by_id[c].get("title")) for c in ids)))
        if self.s.links_made:
            self.p("  links made: " + ", ".join(self.s.links_made))
        self.p(self.c(GREY, "  link <card> <card> to connect two cards (free)."))

    def choose(self, arg):
        avail = self.eng.available_choices(self.s)
        if not avail:
            self.p("  No decisions are open right now.")
            return
        parts = arg.split()
        if len(parts) < 2:
            for i, ch in enumerate(avail, 1):
                self.p("  %d. %s" % (i, ch.get("prompt")))
                for j, o in enumerate(ch.get("options", []), 1):
                    self.p("       %d) %s" % (j, o.get("label")))
            if len(avail) == 1 and len(parts) == 1 and parts[0].isdigit():
                parts = ["1", parts[0]]
            else:
                try:
                    ans = self.reader.read("  choose <decision> <option> (or Enter to skip): ").split()
                except EOFError:
                    return
                if len(ans) == 1 and len(avail) == 1:
                    ans = ["1"] + ans
                if len(ans) < 2:
                    return
                parts = ans
        try:
            ch = avail[int(parts[0]) - 1]
            o = ch.get("options", [])[int(parts[1]) - 1]
        except (ValueError, IndexError):
            self.p("  Pick by number, e.g. choose 1 2.")
            return
        self.apply({"type": "CHOOSE", "choice": ch.get("id"), "option": o.get("id")})

    def pick(self, label, options, allow_free=False):
        for i, o in enumerate(options, 1):
            self.p("    %d) %s" % (i, o))
        while True:
            ans = self.reader.read("  %s: " % label).strip()
            if ans.isdigit() and 1 <= int(ans) <= len(options):
                return options[int(ans) - 1]
            if allow_free and ans:
                return ans
            self.p("    Type a number from the list.")

    def accuse(self):
        c = self.case
        people = sorted((ch.get("id") for ch in c.chars if c.accusable(ch.get("id"))), key=c.name_of)
        proof = [x for x in self.s.seen if c.card_by_id[x].get("kind") == "contradiction"]
        if len(proof) < 3:
            self.p("  You need three contradiction cards (C-...) to make an accusation; you have %d." % len(proof))
            self.p("  Catch people out with present <card> to <claim>, or link cards on the board.")
            return
        try:
            self.p(self.c(BOLD, "ACCUSATION") + self.c(GREY, "  (it ends the case)"))
            ans = self.reader.read("  Are you sure? (yes/no): ").strip().lower()
            if not ans.startswith("y"):
                return
            self.p("  WHO did it?")
            who = self.pick("who", [c.name_of(x) for x in people])
            who_id = people[[c.name_of(x) for x in people].index(who)]
            self.p("  HOW?")
            how = self.pick("how", self.eng.accusation_options("how"), allow_free=True)
            self.p("  WHEN?")
            when = self.pick("when", self.eng.accusation_options("when"), allow_free=True)
            self.p("  WHY?")
            why = self.pick("why", self.eng.accusation_options("why"), allow_free=True)
            self.p("  PROOF: pick three contradiction cards (e.g. 1 2 3)")
            for i, x in enumerate(proof, 1):
                self.p("    %d) %s  %s" % (i, x, c.card_by_id[x].get("title")))
            while True:
                nums = re.findall(r"\d+", self.reader.read("  proof: "))
                picks = [proof[int(n) - 1] for n in nums if 1 <= int(n) <= len(proof)]
                if len(set(picks)) == 3:
                    break
                self.p("    Pick exactly three different numbers.")
        except EOFError:
            return
        self.apply({"type": "ACCUSE", "who": who_id, "how": how, "when": when, "why": why, "proof": picks})

    def finish(self):
        """Epilogue choice + case report."""
        end = next((e for e in self.case.endings if e.get("id") == self.s.ending), {})
        opts = end.get("epilogue_choices") or []
        if opts:
            self.p()
            self.p(self.c(BOLD, "  One last decision:"))
            try:
                choice = self.pick("choose", opts)
                self.apply({"type": "EPILOGUE", "choice": choice})
                self.p("  " + choice + ".")
            except EOFError:
                pass
        self.report()

    def report(self):
        s, c = self.s, self.case
        cards = [x for x in c.card_by_id if c.card_by_id[x].get("kind") != "contradiction"]
        self.p()
        self.p(self.c(BOLD, "CASE REPORT"))
        self.p("  Ending: %s" % next((e.get("title") for e in c.endings if e.get("id") == s.ending), s.ending))
        self.p("  Time used: %d minutes (%s to %s)" % (s.clock - c.start, E.fmt_clock(c.start), E.fmt_clock(s.clock)))
        self.p("  Actions: %d" % s.actions)
        self.p("  Clues found: %d of %d" % (sum(1 for x in cards if x in s.seen), len(cards)))
        self.p("  Lies broken: %d of %d" % (len(s.broken), sum(1 for x in c.claims if not x.get("is_true"))))
        if s.epilogue:
            self.p("  Epilogue: %s" % s.epilogue)

    # -- command dispatch --------------------------------------------------------------------
    def handle(self, line):
        raw = line.strip()
        if not raw:
            return
        low = raw.lower()
        cmd, _, arg = low.partition(" ")
        rest = raw[len(cmd):].strip()
        talk_target = self.talking
        if cmd in ("help", "?", "h"):
            self.p(HELP)
        elif cmd in ("quit", "exit", "q"):
            self.quit = True
        elif cmd in ("look", "l") and not arg.startswith("at "):
            self.look()
        elif cmd == "go" or low.startswith("go to "):
            pid = self.find_place(re.sub(r"^(to|the)\s+", "", arg))
            if not pid:
                self.p("  Go where? " + "; ".join(p.get("name") for p in self.case.places))
            else:
                self.talking = None
                self.apply({"type": "GO", "place": pid})
        elif cmd in ("examine", "x", "inspect", "check", "read") or low.startswith("look at "):
            target = re.sub(r"^(at|the)\s+", "", arg if cmd != "look" else arg[3:])
            key = self.find_hotspot(target)
            if not key:
                self.p("  Examine what? Try look.")
            else:
                self.apply({"type": "EXAMINE", "hotspot": key})
        elif cmd == "search":
            pid = self.find_place(arg) if arg else self.s.location
            self.apply({"type": "SEARCH", "place": pid})
        elif cmd in ("talk", "interview", "speak") or low.startswith("talk to "):
            name = re.sub(r"^(to|with)\s+", "", arg)
            cid = self.find_char(name)
            if not cid:
                self.p("  Talk to whom? " + ", ".join(self.case.short_name(ch.get("id")) for ch in self.case.chars
                                                       if self.case.talkable(ch.get("id"))))
                return
            out = self.apply({"type": "MEET", "char": cid}, show=False)
            self.render([o for o in out if o["kind"] != "clock"])
            if self.eng.withdrawn(self.s, cid):
                return
            self.talking = cid
            labels = [t.get("label") for t in self.case.topics if t.get("id") in self.eng.open_topics(self.s)]
            self.p(self.c(GREY, "  You're talking to %s. Ask anything. Topics people respond to: %s. (bye to stop)" % (
                self.case.name_of(cid), ", ".join(labels))))
        elif cmd in ("bye", "leave", "done", "goodbye"):
            self.talking = None
            self.p(self.c(GREY, "  You step away."))
        elif cmd in ("ask", "follow", "press", "reassure", "threaten", "smalltalk", "chat") and talk_target is None:
            self.p("  Talk to someone first: talk <name>.")
        elif cmd == "ask":
            q = re.sub(r"^(about|him about|her about|them about)\s+", "", arg)
            topic = self.find_topic(q) if q else None
            self.apply({"type": "TALK", "char": talk_target, "intent": "ASK" if topic else "SMALL_TALK", "topic": topic})
        elif cmd == "follow":
            self.apply({"type": "TALK", "char": talk_target, "intent": "FOLLOW_UP",
                        "topic": self.find_topic(re.sub(r"^up\s*(on|about)?\s*", "", arg)) if arg else None})
        elif cmd in ("press", "reassure", "threaten"):
            topic = self.find_topic(arg) if arg else None
            self.apply({"type": "TALK", "char": talk_target, "intent": cmd.upper(), "topic": topic})
        elif cmd in ("smalltalk", "chat"):
            self.apply({"type": "TALK", "char": talk_target, "intent": "SMALL_TALK"})
        elif cmd in ("present", "show"):
            self.present(rest)
        elif cmd == "confront":
            self.confront(rest)
        elif cmd in ("notebook", "nb", "notes"):
            self.notebook(arg)
        elif cmd == "find":
            self.find(rest)
        elif cmd == "board":
            self.board()
        elif cmd == "link":
            self.link(rest)
        elif cmd in ("time", "clock"):
            self.time()
        elif cmd == "wait":
            n = int(arg) if arg.isdigit() else 10
            self.apply({"type": "WAIT", "minutes": n})
        elif cmd == "choose":
            self.choose(arg)
        elif cmd == "accuse":
            self.accuse()
        else:
            # "Iris, where were you?" addresses someone directly
            m = re.match(r"^([A-Za-z][\w .'-]{0,30}?)[,:]\s*(.+)$", raw)
            if m and self.find_char(m.group(1), exact=True):
                cid = self.find_char(m.group(1), exact=True)
                if cid != self.talking:
                    self.handle("talk " + m.group(1))
                    if self.talking != cid:
                        return
                self.say(m.group(2))
            elif self.talking:
                self.say(raw)
            else:
                self.p("  I don't know that command. Type help (or talk <name> to question someone).")

    def say(self, text):
        out = self.apply({"type": "SAY", "char": self.talking, "text": text}, show=False)
        intent = next((o["event"] for o in out if o["kind"] == "intent"), None)
        if intent:
            what = intent.get("intent") or intent.get("type")
            tl = (self.case.topic_by_id.get(intent.get("topic")) or {}).get("label")
            self.p(self.c(GREY, "  (%s%s)" % (what.lower().replace("_", " "), (" - " + tl) if tl else "")))
        self.render([o for o in out if o["kind"] != "intent"])

    def present(self, rest):
        m = re.match(r"^(.+?)\s+(?:to|against|at)\s+(.+)$", rest, re.I)
        card_txt, tgt_txt = (m.group(1), m.group(2)) if m else (rest, "")
        card = self.find_card(card_txt)
        if not card:
            self.p("  Present which card? (notebook evidence)")
            return
        ev = {"type": "PRESENT", "card": card}
        if tgt_txt:
            claim = self.find_claim(tgt_txt, speaker=self.talking)
            cid = self.find_char(tgt_txt)
            if tgt_txt.strip().upper().startswith("CL-") or (claim and not cid):
                if not claim:
                    self.p("  You haven't heard that claim.")
                    return
                ev["claim"] = claim
            elif cid:
                ev["char"] = cid
            else:
                self.p("  Present it to which claim? (notebook claims)")
                return
        elif self.talking:
            ev["char"] = self.talking
        else:
            self.p("  present <card> to <claim>   e.g. present glove to CL-TOB-NEVER")
            return
        self.apply(ev)
        tgt = ev.get("char") or (self.case.claim_by_id.get(ev.get("claim")) or {}).get("speaker")
        if tgt and not self.eng.withdrawn(self.s, tgt):
            self.talking = tgt

    def confront(self, rest):
        parts = re.split(r"\s+(?:with|and|vs|against)\s+|\s+", rest.strip(), maxsplit=1)
        if len(parts) < 2:
            self.p("  confront <claim> <claim>   e.g. confront CL-NOR-1 CL-HAR-2")
            return
        a, b = self.find_claim(parts[0]), self.find_claim(parts[1])
        if not a or not b:
            self.p("  Name two claims you've heard (notebook claims).")
            return
        self.apply({"type": "CONFRONT", "a": a, "b": b})

    def link(self, rest):
        parts = re.split(r"\s+(?:and|with|to|\+)\s+|\s*\+\s*", rest.strip())
        if len(parts) != 2:
            parts = rest.split()
        if len(parts) != 2:
            self.p("  link <card> <card>")
            return
        a, b = self.find_card(parts[0]), self.find_card(parts[1])
        if not a or not b or a == b:
            self.p("  Name two different cards you have (board).")
            return
        self.apply({"type": "LINK", "a": a, "b": b})

    # -- loops -------------------------------------------------------------------------------
    def run(self):
        self.intro()
        while not self.quit and not self.s.ending:
            try:
                line = self.reader.read(self.prompt())
            except (EOFError, KeyboardInterrupt):
                self.p()
                break
            self.handle(line)
        if self.s.ending:
            self.finish()
        return 0

    def autoplay(self):
        self.intro()
        self.p(self.c(GREY, "\nSearching for a solution..."))
        path, st = self.eng.find_solution()
        if not path:
            self.p(self.c(RED, "No path to the true ending was found (%d states searched)." % st.get("expanded", 0)))
            return 1
        for ev in path:
            self.p(self.c(BOLD, "\n[%s] > %s" % (E.fmt_clock(self.s.clock), E.describe_event(self.case, ev))))
            self.apply(ev)
        ok = self.s.ending == self.case.true_ending
        self.p()
        self.p(self.c(GREEN if ok else RED, "%s in %d actions, %d game minutes (%s to %s)." % (
            "Solved" if ok else "Autoplay FAILED", self.s.actions, self.s.clock - self.case.start,
            E.fmt_clock(self.case.start), E.fmt_clock(self.s.clock))))
        return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Play a case pack in the terminal.")
    ap.add_argument("pack", help="pack folder (contains casepack.json and case-file.json)")
    ap.add_argument("--autoplay-solution", action="store_true", help="find and play a path to the true ending")
    ap.add_argument("--script", help="read commands from a file, one per line")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--log", help="append the JSON event log here (JSONL)")
    a = ap.parse_args(argv)
    try:
        case = E.load_pack(a.pack)
    except (E.PackError, OSError, ValueError) as ex:
        print("Can't load pack: %s" % ex, file=sys.stderr)
        return 2
    color = not a.no_color and sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    log = open(a.log, "a", encoding="utf-8") if a.log else None
    try:
        ui = UI(E.Engine(case, seed=a.seed), color=color, reader=Reader(a.script), log=log)
        return ui.autoplay() if a.autoplay_solution else ui.run()
    finally:
        if log:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
