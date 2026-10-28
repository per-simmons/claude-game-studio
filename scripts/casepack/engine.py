#!/usr/bin/env python3
"""Case-pack engine: a pure, deterministic reducer for case-file v1, plus the offline intent matcher
and a solver used by `play.py --autoplay-solution` and `lint.py`.

Contract: skills/studio/references/engine-semantics.md. Standard library only. No network.

    from engine import load_pack, Engine
    case = load_pack("examples/case-packs/the-locked-study")
    eng = Engine(case, seed=1)
    s = eng.initial_state()
    s, out = eng.step(s, {"type": "EXAMINE", "hotspot": "door"})

`step` never mutates its input state; it returns a new state and a list of output records
(lines, new cards, claims, info, errors, ending). Same pack + seed + events = same result.

Resolutions of points the contract leaves open are marked "RESOLVED:" below.
"""
from __future__ import annotations

import heapq
import itertools
import json
import os
import re
from collections import deque

FORMAT = "casepack/1"
CATEGORIES = ("alibi", "motive", "physical")
TALK_INTENTS = ("ASK", "FOLLOW_UP", "PRESS", "REASSURE", "THREATEN", "SMALL_TALK", "PRESENT",
                "CONFRONT", "META", "DEMAND_CONFESSION", "BARGAIN")
DEFAULT_STORYLET_INTENTS = ("ASK", "FOLLOW_UP")
SEARCH_ACTIONS = ("SEARCH", "SNOW_SEARCH")
# RESOLVED: the contract says only that META/DEMAND_CONFESSION/BARGAIN may touch trust. When no storylet
# answers, these trust deltas apply (before responds_to multipliers). Composure is never touched.
NO_STORYLET_TRUST = {"PRESS": -3, "THREATEN": -5, "DEMAND_CONFESSION": -2, "BARGAIN": -2}
MISS_TRUST = -5
# RESOLVED: composure/trust are clamped to 0..100 (GDD 5.1 ranges); keeps the state space finite.
CLAMP = (0, 100)
# RESOLVED: composure bands for refusals follow GDD 5.2 (Composed 70+, Strained 40-69, Cracking 15-39,
# Broken <15). Aliases high/mid/low are accepted as refusal keys too.
BANDS = ((70, "composed", "high"), (40, "strained", "mid"), (15, "cracking", "low"), (-10**9, "broken", "low"))
HUNCH_SPACING = 3
NON_ACTIONS = ("GO", "MEET", "EPILOGUE", "BEGIN")  # events that never count as player actions

STOP = set("""a an the and or but of to in on at by for with from is are was were be been being am i you he
she it we they me him her us them my your his its our their this that these those what when where who whom
why how do does did done have has had not no so if then than there here just about into out up down over
again any some all very can could would should will shall may might must tell know say said ask""".split())


# ----------------------------------------------------------------------------------------- loading
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class PackError(Exception):
    pass


def load_pack(pack_dir):
    """Load a pack folder (or a bare case-file.json path). Returns a Case."""
    pack_dir = os.path.abspath(pack_dir)
    manifest = {}
    if os.path.isfile(pack_dir):
        case_path = pack_dir
        pack_dir = os.path.dirname(pack_dir)
    else:
        mpath = os.path.join(pack_dir, "casepack.json")
        if os.path.exists(mpath):
            manifest = load_json(mpath)
        case_path = os.path.join(pack_dir, manifest.get("case_file", "case-file.json"))
    if not os.path.exists(case_path):
        raise PackError("no case file at %s" % case_path)
    return Case(load_json(case_path), manifest=manifest, pack_dir=pack_dir)


# ------------------------------------------------------------------------------------------ text
def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def stem(w):
    w = w.lower().strip("'")
    if w.endswith("'s"):
        w = w[:-2]
    for suf, minlen in (("ing", 6), ("ed", 5), ("es", 5), ("s", 4)):
        if w.endswith(suf) and len(w) >= minlen:
            return w[: -len(suf)]
    return w


def tokens(s):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9'\-:]*", str(s).lower())]


def content_stems(s):
    return {stem(t) for t in tokens(s) if t not in STOP and len(t) > 1}


def all_stems(s):
    """Every token (stopwords kept): author-chosen keywords like "where" must still match."""
    out = set()
    for t in tokens(s):
        out.add(t)
        out.add(stem(t))
    return out


def sanitize(text, cap=400):
    """Strip tags/brackets/control chars (player text is data, never direction)."""
    text = re.sub(r"<\|[^|]*\|>", " ", str(text))
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"<[^>]*>", " ", text)
    text = "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)
    return re.sub(r"\s+", " ", text).strip()[:cap]


_ONES = ["twelve", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven"]
_MINS = {0: "o'clock", 5: "five past", 10: "ten past", 15: "a quarter past", 20: "twenty past", 25: "twenty-five past",
         30: "half past", 35: "twenty-five to", 40: "twenty to", 45: "a quarter to", 50: "ten to", 55: "five to"}


def clock_words(m):
    """Minutes after midnight -> spoken time to the nearest five minutes ('ten past three')."""
    m = int(round(m / 5.0)) * 5
    h, mm = (m // 60) % 24, m % 60
    if mm > 30:
        h, phrase = h + 1, _MINS[mm]
    else:
        phrase = _MINS[mm]
    hour = _ONES[h % 12]
    return hour + " o'clock" if mm == 0 else phrase + " " + hour


def fill_vars(text, clock):
    """Runtime line variables (VO-DIRECTION: written as words so timestamps match the script).
    {rail_time} = the game clock; {colonel_time} / {clock_plus_1} = one hour ahead."""
    if "{" not in (text or ""):
        return text
    return (text.replace("{rail_time}", clock_words(clock))
                .replace("{clock}", clock_words(clock))
                .replace("{colonel_time}", clock_words(clock + 60))
                .replace("{clock_plus_1}", clock_words(clock + 60)))


def fmt_clock(m):
    m = int(m) % 1440
    h, mm = divmod(m, 60)
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return "%d:%02d %s" % (h12, mm, ap)


def keyword_score(text_norm, text_stems, keywords):
    score = 0
    for kw in keywords or ():
        k = norm(kw)
        if not k:
            continue
        if " " in k:
            if (" " + k + " ") in (" " + text_norm + " "):
                score += 2
        elif stem(k) in text_stems or k in text_stems:
            score += 1
    return score


# ------------------------------------------------------------------------------------------ case
class Case:
    """Indexed, read-only view of a case file."""

    def __init__(self, data, manifest=None, pack_dir=None):
        self.data = data
        self.manifest = manifest or {}
        self.pack_dir = pack_dir
        g = data.get
        self.meta = g("meta", {}) or {}
        clock = g("clock", {}) or {}
        self.start = clock.get("start", 0)
        self.deadline = clock.get("deadline", 2879)
        self.costs = clock.get("costs", {}) or {}
        self.scheduled = clock.get("scheduled", []) or []
        self.withdraw_after = clock.get("withdraw_after_misses", 3) or 3
        self.withdraw_minutes = clock.get("withdraw_minutes", 20)
        self.places = g("places", []) or []
        self.place_by_id = {p.get("id"): p for p in self.places}
        self.hotspots = {}          # "PLACE/hs" -> (place, hotspot)
        self.hotspots_by_id = {}    # hs id -> [keys]
        for p in self.places:
            for h in p.get("hotspots", []) or []:
                key = "%s/%s" % (p.get("id"), h.get("id"))
                self.hotspots[key] = (p, h)
                self.hotspots_by_id.setdefault(h.get("id"), []).append(key)
        self.chars = g("characters", []) or []
        self.char_by_id = {c.get("id"): c for c in self.chars}
        self.cards = g("cards", []) or []
        self.card_by_id = {c.get("id"): c for c in self.cards}
        self.claims = g("claims", []) or []
        self.claim_by_id = {c.get("id"): c for c in self.claims}
        self.contradictions = g("contradictions", []) or []
        self.contra_by_claim = {}
        for c in self.contradictions:
            self.contra_by_claim.setdefault(c.get("claim"), []).append(c)
        self.links = g("links", []) or []
        self.storylets = g("storylets", []) or []
        self.storylet_by_id = {}
        self.storylets_by_char = {}
        for i, s in enumerate(self.storylets):
            self.storylet_by_id.setdefault(s.get("id"), s)
            self.storylets_by_char.setdefault(s.get("char"), []).append(s)
        self.topics = g("topics", []) or []
        self.topic_by_id = {t.get("id"): t for t in self.topics}
        self.solution = g("solution", {}) or {}
        self.endings = g("endings", []) or []
        self.timeline = g("timeline", []) or []
        self.hunch = g("hunch", []) or []
        self.refusals = g("refusals", {}) or {}
        self.choices = g("choices", []) or []
        self.choice_by_id = {c.get("id"): c for c in self.choices}
        # line id -> storylet id, claim -> testimony cards
        self.line_owner = {}
        for s in self.storylets:
            for ln in s.get("lines", []) or []:
                self.line_owner.setdefault(ln.get("id"), s.get("id"))
        self.claim_testimony = {}
        for cl in self.claims:
            via = cl.get("heard_via")
            srcs = {via}
            st = self.storylet_by_id.get(via)
            if st:
                srcs |= {ln.get("id") for ln in st.get("lines", []) or []}
            self.claim_testimony[cl.get("id")] = [
                c.get("id") for c in self.cards
                if c.get("kind") == "testimony" and c.get("source_line") and c.get("source_line") in srcs]
        self.proof_cards = {cat: list((self.solution.get("proof", {}) or {}).get(cat, []) or [])
                            for cat in CATEGORIES}
        self._talkable = {}
        self.true_ending = next((e.get("id") for e in self.endings if e.get("condition") == "TRUE_SOLUTION"), None)

    # names --------------------------------------------------------------------------------
    @property
    def title(self):
        return self.manifest.get("title") or self.meta.get("title") or self.meta.get("id") or "Untitled case"

    def name_of(self, cid):
        c = self.char_by_id.get(cid)
        if c:
            return c.get("name", cid)
        return {"HUNCH": "HUNCH", "AGENT": "YOU", "NARRATOR": "NARRATOR"}.get(cid, cid or "")

    def short_name(self, cid):
        c = self.char_by_id.get(cid) or {}
        for a in c.get("aliases") or []:
            a = re.sub(r"^(the|a)\s+", "", a.strip(), flags=re.I)
            if a and len(a.split()) == 1 and a.lower() not in ("you", "me"):
                return a[0].upper() + a[1:]
        n = self.name_of(cid)
        parts = [p for p in n.replace(".", ". ").split() if p.lower().rstrip(".") not in
                 ("mr", "mrs", "miss", "ms", "dr", "sir", "lady", "lord", "the", "colonel", "constable",
                  "inspector", "professor", "agent", "detective", "sergeant", "col", "conductor", "capt",
                  "captain", "major", "rev", "father", "officer")]
        return parts[0] if parts else n

    def accusable(self, cid):
        c = self.char_by_id.get(cid)
        if not c:
            return False
        if "accusable" in c:
            return bool(c["accusable"])
        return c.get("role") in ("killer", "suspect")

    def talkable(self, cid):
        # RESOLVED: you can talk to anyone who isn't the victim and has at least one storylet that
        # answers a talk intent (so narrator/player pseudo-characters like a Hunch aren't listed).
        if cid in self._talkable:
            return self._talkable[cid]
        c = self.char_by_id.get(cid)
        ok = bool(c) and c.get("role") != "victim"
        if ok:
            talk = set(TALK_INTENTS) - {"PRESENT", "CONFRONT"}
            ok = any(set(st.get("intents") or DEFAULT_STORYLET_INTENTS) & talk
                     for st in self.storylets_by_char.get(cid, ()))
        self._talkable[cid] = ok
        return ok

    def cost(self, key):
        return int(self.costs.get(key, 0) or 0)


# ----------------------------------------------------------------------------------------- state
class State:
    __slots__ = ("clock", "location", "interviewing", "last_topic", "seen", "heard", "broken", "flags",
                 "done", "chars", "links_made", "chosen", "sched_fired", "hunch_fired", "last_hunch",
                 "tells", "actions", "rng", "transcript", "ending", "theory", "epilogue")

    def copy(self):
        n = State.__new__(State)
        n.clock = self.clock
        n.location = self.location
        n.interviewing = self.interviewing
        n.last_topic = dict(self.last_topic)
        n.seen = dict(self.seen)
        n.heard = dict(self.heard)
        n.broken = dict(self.broken)
        n.flags = dict(self.flags)
        n.done = dict(self.done)
        n.chars = {k: {"composure": v["composure"], "trust": v["trust"], "miss": v["miss"],
                       "withdrawn_until": v["withdrawn_until"], "locks": dict(v["locks"])}
                   for k, v in self.chars.items()}
        n.links_made = dict(self.links_made)
        n.chosen = dict(self.chosen)
        n.sched_fired = set(self.sched_fired)
        n.hunch_fired = set(self.hunch_fired)
        n.last_hunch = self.last_hunch
        n.tells = set(self.tells)
        n.actions = self.actions
        n.rng = self.rng
        n.transcript = list(self.transcript)
        n.ending = self.ending
        n.theory = self.theory
        n.epilogue = self.epilogue
        return n

    def key(self):
        """Progress key (no clock): used by the solver to deduplicate states."""
        return (frozenset(self.seen), frozenset(self.heard), frozenset(self.broken), frozenset(self.flags),
                frozenset(self.done),
                tuple(sorted((k, v["composure"], v["trust"], tuple(sorted(v["locks"].items())))
                             for k, v in self.chars.items())),
                frozenset(self.chosen.items()), frozenset(self.sched_fired), self.ending)

    def to_json(self):
        return {
            "clock": self.clock, "location": self.location, "interviewing": self.interviewing,
            "seen": list(self.seen), "heard": list(self.heard), "broken": list(self.broken),
            "flags": list(self.flags), "done": list(self.done),
            "chars": self.chars, "links_made": list(self.links_made), "chosen": self.chosen,
            "actions": self.actions, "ending": self.ending, "theory": self.theory,
            "transcript": self.transcript,
        }


class Out(list):
    def emit(self, kind, **kw):
        kw["kind"] = kind
        self.append(kw)
        return kw


# ---------------------------------------------------------------------------------------- engine
class Engine:
    def __init__(self, case, seed=0):
        self.case = case
        self.seed = int(seed)
        self._relevance = None
        self._order = {id(st): i for i, st in enumerate(case.storylets)}

    # -- setup -------------------------------------------------------------------------------
    def initial_state(self):
        c = self.case
        s = State.__new__(State)
        s.clock = c.start
        s.location = c.places[0].get("id") if c.places else None
        s.interviewing = None
        s.last_topic = {}
        s.seen, s.heard, s.broken, s.flags, s.done = {}, {}, {}, {}, {}
        s.chars = {}
        for ch in c.chars:
            b = ch.get("baseline", {}) or {}
            s.chars[ch.get("id")] = {
                "composure": _clamp(b.get("composure", 50)), "trust": _clamp(b.get("trust", 50)),
                "miss": 0, "withdrawn_until": None,
                "locks": {lk.get("id"): False for lk in ch.get("locks", []) or []}}
        s.links_made, s.chosen = {}, {}
        s.sched_fired, s.hunch_fired, s.tells = set(), set(), set()
        s.last_hunch = None
        s.actions = 0
        s.rng = (self.seed * 2654435761 + 1) & 0x7FFFFFFF
        s.transcript = []
        s.ending = None
        s.theory = None
        s.epilogue = None
        return s

    # -- quality expressions -----------------------------------------------------------------
    def holds(self, expr, s, cid=None):
        if not expr:
            return True
        f = s.flags
        if any(x not in f for x in expr.get("flags_all", ()) or ()):
            return False
        fa = expr.get("flags_any")
        if fa and not any(x in f for x in fa):
            return False
        if any(x in f for x in expr.get("flags_none", ()) or ()):
            return False
        if any(x not in s.seen for x in expr.get("cards_seen_all", ()) or ()):
            return False
        ca = expr.get("cards_seen_any")
        if ca and not any(x in s.seen for x in ca):
            return False
        if any(x not in s.broken for x in expr.get("claims_broken_all", ()) or ()):
            return False
        st = s.chars.get(cid)
        if "composure_lte" in expr and (st is None or st["composure"] > expr["composure_lte"]):
            return False
        if "composure_gte" in expr and (st is None or st["composure"] < expr["composure_gte"]):
            return False
        if "trust_gte" in expr and (st is None or st["trust"] < expr["trust_gte"]):
            return False
        if "clock_gte" in expr and s.clock < expr["clock_gte"]:
            return False
        if "clock_lte" in expr and s.clock > expr["clock_lte"]:
            return False
        return True

    def topic_open(self, s, topic):
        if topic in (None, "*"):
            return True
        t = self.case.topic_by_id.get(topic)
        return t is not None and self.holds(t.get("requires"), s)

    def open_topics(self, s):
        return [t.get("id") for t in self.case.topics if self.holds(t.get("requires"), s)]

    # -- storylet selection ------------------------------------------------------------------
    def select(self, s, cid, topic, intent, pool=None):
        """Highest priority eligible storylet; ties go to file order. topic None matches only '*'."""
        best, bestp = None, None
        for st in (pool if pool is not None else self.case.storylets_by_char.get(cid, ())):
            t = st.get("topic")
            if t != "*" and (topic is None or t != topic):
                continue
            if intent not in (st.get("intents") or DEFAULT_STORYLET_INTENTS):
                continue
            if pool is None:
                if st.get("once") and st.get("id") in s.done:
                    continue
                if not self.holds(st.get("requires"), s, cid):
                    continue
            p = st.get("priority", 0) or 0
            if best is None or p > bestp:
                best, bestp = st, p
        return best

    def eligible_storylets(self, s, cid):
        return [st for st in self.case.storylets_by_char.get(cid, ())
                if not (st.get("once") and st.get("id") in s.done) and self.holds(st.get("requires"), s, cid)]

    # -- helpers -----------------------------------------------------------------------------
    def _rand(self, s, n):
        s.rng = (s.rng * 1103515245 + 12345) & 0x7FFFFFFF
        return (s.rng >> 8) % max(1, n)

    def _lines(self, s, lines, default_speaker, out, record, source=None):
        for ln in lines or ():
            spk = ln.get("speaker") or default_speaker
            item = out.emit("line", speaker=spk, name=self.case.name_of(spk), text=fill_vars(ln.get("text", ""), s.clock),
                            direction=ln.get("direction"), line_id=ln.get("id"), source=source)
            if record:
                s.transcript.append({"t": s.clock, "speaker": spk, "name": item["name"],
                                     "text": item["text"], "direction": item["direction"],
                                     "line_id": item["line_id"]})

    def _see(self, s, cid, out, via=None):
        if cid and cid not in s.seen and cid in self.case.card_by_id:
            s.seen[cid] = True
            card = self.case.card_by_id[cid]
            out.emit("card", id=cid, title=card.get("title"), card_kind=card.get("kind"),
                     description=card.get("description"), via=via)

    def _hear(self, s, clid, out):
        if clid and clid not in s.heard and clid in self.case.claim_by_id:
            s.heard[clid] = True
            cl = self.case.claim_by_id[clid]
            out.emit("claim", id=clid, speaker=cl.get("speaker"), text=cl.get("text"))

    def _flag(self, s, f, out):
        if f and f not in s.flags:
            s.flags[f] = True
            out.emit("flag", flag=f)

    def _delta(self, s, cid, comp=0, trust=0):
        st = s.chars.get(cid)
        if not st:
            return
        if comp:
            st["composure"] = _clamp(st["composure"] + comp)
            if comp < 0:
                s.tells.add(cid)
        if trust:
            st["trust"] = _clamp(st["trust"] + trust)

    def play(self, s, st, out, record=True, intent=None):
        """Apply a storylet (engine-semantics: Talking step 3)."""
        cid = st.get("char")
        self._lines(s, st.get("lines"), cid, out, record, source=st.get("id"))
        for cl in st.get("utters_claims", ()) or ():
            self._hear(s, cl, out)
        for c in st.get("reveals", ()) or ():
            self._see(s, c, out, via=st.get("id"))
        for f in st.get("sets_flags", ()) or ():
            self._flag(s, f, out)
        mult = 1.0
        ch = self.case.char_by_id.get(cid) or {}
        if intent in ("REASSURE", "PRESS", "THREATEN"):
            mult = float((ch.get("responds_to") or {}).get(intent, 1.0))
        self._delta(s, cid, int(round((st.get("composure_delta", 0) or 0) * mult)),
                    int(round((st.get("trust_delta", 0) or 0) * mult)))
        s.done[st.get("id")] = True

    def play_beat(self, s, beat_id, out, record=True):
        st = self.case.storylet_by_id.get(beat_id)
        if st:
            self.play(s, st, out, record)
            return True
        return False

    def band(self, composure):
        for lo, name, _alias in BANDS:
            if composure >= lo:
                return name
        return "broken"

    def _refuse(self, s, cid, intent, out, record):
        r = self.case.refusals
        comp = s.chars.get(cid, {}).get("composure", 50)
        band = self.band(comp)
        alias = next(a for lo, n, a in BANDS if n == band)
        # RESOLVED: lookup order: the character's line for this intent+band, then for the intent,
        # then refusals["*"] for the intent, then the character's band line, then "*" fallbacks.
        ib = ["%s:%s" % (intent, band), "%s:%s" % (intent, alias), intent]
        order = [(cid, ib), ("*", ib), (cid, [band, alias, "*"]), ("*", [band, alias, "*"])]
        lines = None
        for owner, keys in order:
            table = r.get(owner) or {}
            low = {k.lower(): v for k, v in table.items()}
            for k in keys:
                v = table.get(k) or low.get(k.lower())
                if v:
                    lines = v
                    break
            if lines:
                break
        if lines:
            ln = lines[self._rand(s, len(lines))]
            self._lines(s, [ln], cid, out, record, source="refusal")
        else:
            self._lines(s, [{"id": "GENERIC-DEFLECT", "text": "I've nothing to say about that.",
                             "direction": "guarded"}], cid, out, record, source="refusal")

    def _open_lock(self, s, cid, lock, out):
        st = s.chars.get(cid)
        if not st or lock not in st["locks"] or st["locks"][lock]:
            return False
        st["locks"][lock] = True
        out.emit("lock", char=cid, lock=lock, name=self.case.name_of(cid))
        if st["locks"] and all(st["locks"].values()):
            self._flag(s, "%s_LOCKS_OPEN" % cid, out)
        return True

    def _lock_by_ref(self, cid, ref):
        ch = self.case.char_by_id.get(cid) or {}
        locks = ch.get("locks", []) or []
        for lk in locks:
            if lk.get("id") == ref:
                return lk.get("id")
        for lk in locks:  # RESOLVED: opens_lock may name a category instead of a lock id
            if lk.get("category") == ref:
                return lk.get("id")
        return None

    def _lock_check(self, s, target, card_id, out):
        card = self.case.card_by_id.get(card_id)
        if not card or card_id not in s.seen or not card.get("proof_category"):
            return False
        ch = self.case.char_by_id.get(target) or {}
        opened = False
        for lk in ch.get("locks", []) or []:
            if lk.get("category") == card["proof_category"] and not s.chars[target]["locks"].get(lk.get("id")):
                opened = self._open_lock(s, target, lk.get("id"), out) or opened
        return opened

    def withdrawn(self, s, cid):
        st = s.chars.get(cid)
        return bool(st and st["withdrawn_until"] is not None and s.clock < st["withdrawn_until"])

    def _fetch_cost(self, s, cid):
        return self.case.cost("FETCH") if (cid and s.interviewing and s.interviewing != cid) else 0

    # -- clock -------------------------------------------------------------------------------
    def _advance(self, s, minutes, out, record):
        old = s.clock
        s.clock = old + max(0, int(minutes))
        if s.clock != old:
            out.emit("clock", clock=s.clock, minutes=s.clock - old)
        # RESOLVED: a scheduled beat is evaluated once, at the moment the clock passes `at`
        # (old < at <= new). If only_if fails then, it never fires.
        for i, sc in enumerate(self.case.scheduled):
            if i in s.sched_fired:
                continue
            at = sc.get("at", 0)
            if old < at <= s.clock:
                s.sched_fired.add(i)
                beat = self.case.storylet_by_id.get(sc.get("beat"))
                if beat and self.holds(sc.get("only_if"), s, beat.get("char")):
                    out.emit("scheduled", beat=sc.get("beat"), at=at)
                    self.play(s, beat, out, record)
        if s.clock >= self.case.deadline and not s.ending:
            self._timeout(s, out, record)

    def _timeout(self, s, out, record):
        end = next((e for e in self.case.endings if e.get("condition") == "TIMEOUT"), None)
        if end is None:
            end = {"id": "END-TIMEOUT", "title": "Out of time", "beat": None}
        s.ending = end.get("id")
        out.emit("ending", id=end.get("id"), title=end.get("title"), condition="TIMEOUT",
                 epilogue_choices=end.get("epilogue_choices", []) or [])
        self.play_beat(s, end.get("beat"), out, record)

    # -- hunch -------------------------------------------------------------------------------
    def trigger_holds(self, s, trig):
        kind, _, arg = (trig or "").partition(":")
        if kind == "card_seen":
            return arg in s.seen
        if kind == "claim_heard":
            return arg in s.heard
        if kind == "claim_broken":
            return arg in s.broken
        if kind == "link_created":
            return arg in s.links_made
        if kind == "storylet_done":
            return arg in s.done
        if kind in ("tell", "tell_fired"):
            return arg.split(":")[0] in s.tells
        return False  # e.g. latency_flag: only meaningful in the voice engine

    def _hunch(self, s, out, record):
        if s.ending or not self.case.hunch:
            return
        if s.last_hunch is not None and s.actions - s.last_hunch < HUNCH_SPACING:
            return
        for h in self.case.hunch:
            hid = h.get("id")
            if hid in s.hunch_fired or not self.trigger_holds(s, h.get("trigger")):
                continue
            s.hunch_fired.add(hid)
            s.last_hunch = s.actions
            ln = dict(h.get("line") or {})
            ln.setdefault("speaker", "HUNCH")
            out.emit("hunch", id=hid)
            self._lines(s, [ln], "HUNCH", out, record, source=hid)
            return

    # -- the reducer -------------------------------------------------------------------------
    def step(self, state, ev, record=True):
        """Pure reducer: returns (new_state, outputs). Invalid events return the input state unchanged."""
        s = state.copy()
        out = Out()
        t = (ev.get("type") or "").upper()
        if s.ending and t != "EPILOGUE":
            out.emit("error", text="The case is closed.")
            return state, out
        h = getattr(self, "_ev_" + t.lower(), None)
        if h is None:
            out.emit("error", text="Unknown event type %r." % t)
            return state, out
        counted = h(s, ev, out, record)
        if counted is None:
            return state, out
        if counted and t not in NON_ACTIONS:
            s.actions += 1
            self._hunch(s, out, record)
        return s, out

    def replay(self, events, record=False):
        s, _ = self.start(record)
        outs = []
        for ev in events:
            s, out = self.step(s, ev, record)
            outs.append(out)
        return s, outs

    # events ---------------------------------------------------------------------------------
    def _err(self, out, msg):
        out.emit("error", text=msg)
        return None

    def start(self, record=True):
        """Initial state after BEGIN (fires scheduled beats at or before clock.start). Returns (state, out)."""
        return self.step(self.initial_state(), {"type": "BEGIN"}, record)

    def _ev_begin(self, s, ev, out, record):
        # RESOLVED: scheduled beats with at <= clock.start fire once, on BEGIN (the opening beat).
        for i, sc in enumerate(self.case.scheduled):
            if i in s.sched_fired or sc.get("at", 0) > s.clock:
                continue
            s.sched_fired.add(i)
            beat = self.case.storylet_by_id.get(sc.get("beat"))
            if beat and self.holds(sc.get("only_if"), s, beat.get("char")):
                out.emit("scheduled", beat=sc.get("beat"), at=sc.get("at"))
                self.play(s, beat, out, record)
        return False

    def _ev_go(self, s, ev, out, record):
        p = ev.get("place")
        if p not in self.case.place_by_id:
            return self._err(out, "No such place.")
        if s.location == p:
            out.emit("info", text="You're already in %s." % self.case.place_by_id[p].get("name"))
            return False
        s.location = p
        s.interviewing = None
        out.emit("moved", place=p, name=self.case.place_by_id[p].get("name"))
        self._advance(s, self.case.cost("MOVE"), out, record)
        return False

    def _ev_meet(self, s, ev, out, record):
        cid = ev.get("char")
        if not self.case.talkable(cid):
            return self._err(out, "You can't talk to them.")
        if self.withdrawn(s, cid):
            out.emit("info", text="%s won't speak to you until %s." % (
                self.case.name_of(cid), fmt_clock(s.chars[cid]["withdrawn_until"])))
            return False
        if s.interviewing == cid:
            return False
        cost = self.case.cost("FETCH") if s.interviewing else 0
        s.interviewing = cid
        self._advance(s, cost, out, record)
        return False

    def _ev_say(self, s, ev, out, record):
        """Free text: run the offline matcher, then reduce the resolved event."""
        cid = ev.get("char") or s.interviewing
        if not cid:
            return self._err(out, "Talk to someone first.")
        resolved = self.interpret(s, cid, ev.get("text", ""))
        out.emit("intent", event=resolved)
        h = getattr(self, "_ev_" + resolved["type"].lower())
        return h(s, resolved, out, record)

    def _ev_talk(self, s, ev, out, record):
        cid = ev.get("char") or s.interviewing
        if not self.case.talkable(cid):
            return self._err(out, "You can't talk to them.")
        intent = (ev.get("intent") or "ASK").upper()
        if intent not in TALK_INTENTS:
            return self._err(out, "Unknown intent %s." % intent)
        if intent in ("PRESENT", "CONFRONT"):
            return self._err(out, "Use a PRESENT or CONFRONT event.")
        if self.withdrawn(s, cid):
            out.emit("info", text="%s won't speak to you until %s." % (
                self.case.name_of(cid), fmt_clock(s.chars[cid]["withdrawn_until"])))
            return False
        topic = ev.get("topic")
        if intent in ("FOLLOW_UP", "PRESS", "REASSURE") and not topic:
            topic = s.last_topic.get(cid)
        if topic and not self.topic_open(s, topic):
            topic = None
        if intent == "ASK" and topic is None:
            intent = "SMALL_TALK"
        cost = self._fetch_cost(s, cid) + self.case.cost(intent)
        st = self.select(s, cid, topic, intent)
        out.emit("talk", char=cid, intent=intent, topic=topic, storylet=st.get("id") if st else None)
        if st:
            self.play(s, st, out, record, intent=intent)
        else:
            self._refuse(s, cid, intent, out, record)
            td = NO_STORYLET_TRUST.get(intent, 0)
            if td:
                mult = float(((self.case.char_by_id.get(cid) or {}).get("responds_to") or {}).get(intent, 1.0))
                self._delta(s, cid, 0, int(round(td * mult)))
        if topic:
            s.last_topic[cid] = topic
        s.interviewing = cid
        self._advance(s, cost, out, record)
        return True

    def _contradiction_hit(self, s, claim_id, cands, target, out, record):
        claim = self.case.claim_by_id[claim_id]
        speaker = claim.get("speaker")
        for c in self.case.contra_by_claim.get(claim_id, ()):
            if any(x in (c.get("cards") or ()) for x in cands) and self.holds(c.get("requires"), s, speaker):
                s.broken[claim_id] = True
                out.emit("broken", claim=claim_id, contradiction=c.get("id"), speaker=speaker,
                         text=claim.get("text"))
                self.play_beat(s, c.get("result_beat"), out, record)
                self._see(s, c.get("creates_card"), out, via=c.get("id"))
                self._delta(s, speaker, c.get("composure_delta", 0) or 0, 0)
                if c.get("opens_lock"):
                    lk = self._lock_by_ref(speaker, c["opens_lock"])
                    if lk:
                        self._open_lock(s, speaker, lk, out)
                for who in {speaker, target}:
                    if who in s.chars:
                        s.chars[who]["miss"] = 0
                return True
        return False

    def _miss(self, s, target, out, record):
        st = s.chars.get(target)
        if not st:
            return
        st["trust"] = _clamp(st["trust"] + MISS_TRUST)
        st["miss"] += 1
        out.emit("miss", char=target, streak=st["miss"])
        if st["miss"] >= self.case.withdraw_after:
            st["miss"] = 0
            st["withdrawn_until"] = s.clock + self.case.cost("PRESENT") + int(self.case.withdraw_minutes or 0)
            out.emit("withdrawn", char=target, until=st["withdrawn_until"], name=self.case.name_of(target))
            if s.interviewing == target:
                s.interviewing = None

    def _ev_present(self, s, ev, out, record):
        c = self.case
        card, claim, target = ev.get("card"), ev.get("claim"), ev.get("char")
        if card not in c.card_by_id:
            return self._err(out, "No such card.")
        if card not in s.seen:
            return self._err(out, "You haven't found that yet.")
        if claim:
            if claim not in c.claim_by_id:
                return self._err(out, "No such claim.")
            if claim not in s.heard:
                return self._err(out, "Nobody has said that to you yet.")
            target = target or c.claim_by_id[claim].get("speaker")
            if claim in s.broken:
                out.emit("info", text="You've already caught them out on that.")
                return False
        target = target or s.interviewing
        if not c.talkable(target):
            return self._err(out, "Present it to whom?")
        if self.withdrawn(s, target):
            out.emit("info", text="%s won't speak to you until %s." % (
                c.name_of(target), fmt_clock(s.chars[target]["withdrawn_until"])))
            return False
        cost = self._fetch_cost(s, target) + c.cost("PRESENT")
        out.emit("present", char=target, card=card, claim=claim)
        hit = False
        if claim:
            hit = self._contradiction_hit(s, claim, [card], target, out, record)
            if not hit:
                self._refuse_present(s, target, out, record)
                self._miss(s, target, out, record)
        opened = self._lock_check(s, target, card, out)
        if not claim:
            # RESOLVED: presenting a card with no claim is a "show". A PRESENT storylet whose topic is
            # the card id (or "*") answers it; otherwise nothing happens. It is never a miss.
            st = self.select(s, target, card, "PRESENT")
            if st:
                self.play(s, st, out, record, intent="PRESENT")
            elif not opened:
                out.emit("info", text="%s looks at it and says nothing." % c.name_of(target))
        s.interviewing = target if not self.withdrawn(s, target) else None
        self._advance(s, cost, out, record)
        return True

    def _refuse_present(self, s, target, out, record):
        self._refuse(s, target, "PRESENT", out, record)

    def _ev_confront(self, s, ev, out, record):
        c = self.case
        a, b = ev.get("a"), ev.get("b")
        for x in (a, b):
            if x not in c.claim_by_id:
                return self._err(out, "No such claim.")
            if x not in s.heard:
                return self._err(out, "Nobody has said that to you yet.")
        target = ev.get("char") or c.claim_by_id[a].get("speaker")
        if self.withdrawn(s, target):
            out.emit("info", text="%s won't speak to you until %s." % (
                c.name_of(target), fmt_clock(s.chars[target]["withdrawn_until"])))
            return False
        cost = self._fetch_cost(s, target) + c.cost("CONFRONT" if "CONFRONT" in c.costs else "PRESENT")
        out.emit("confront", char=target, a=a, b=b)
        # RESOLVED: CONFRONT a b tries b's testimony (the claim id itself, or a testimony card whose
        # source_line is the line that uttered b) against a; if that misses it tries the reverse.
        hit = False
        for x, y in ((a, b), (b, a)):
            if x in s.broken:
                continue
            cands = [y] + c.claim_testimony.get(y, [])
            if self._contradiction_hit(s, x, cands, target, out, record):
                hit = True
                break
        if not hit:
            self._refuse_present(s, target, out, record)
            self._miss(s, target, out, record)
        s.interviewing = target if not self.withdrawn(s, target) else None
        self._advance(s, cost, out, record)
        return True

    def resolve_hotspot(self, s, ref):
        c = self.case
        if ref in c.hotspots:
            return ref
        keys = c.hotspots_by_id.get(ref, [])
        if len(keys) == 1:
            return keys[0]
        for k in keys:
            if c.hotspots[k][0].get("id") == s.location:
                return k
        return keys[0] if keys else None

    def hotspot_ok(self, s, place, hs):
        action = hs.get("action") or "EXAMINE"
        if not self.holds(hs.get("requires"), s):
            return False
        if action in SEARCH_ACTIONS and not self.holds(place.get("search_requires"), s):
            return False
        return True

    def _ev_examine(self, s, ev, out, record):
        key = self.resolve_hotspot(s, ev.get("hotspot"))
        if not key:
            return self._err(out, "There's nothing like that to examine.")
        place, hs = self.case.hotspots[key]
        label = hs.get("label") or hs.get("id")
        s.location = place.get("id")
        if not self.hotspot_ok(s, place, hs):
            out.emit("info", text="%s (not now)" % label)
            return False
        new = [x for x in hs.get("reveals", []) or [] if x not in s.seen]
        if not new:
            out.emit("info", text="%s: nothing new." % label)
            return False
        out.emit("examine", hotspot=key, label=label)
        for x in new:
            self._see(s, x, out, via=key)
        self._advance(s, self.case.cost(hs.get("action") or "EXAMINE"), out, record)
        return True

    def _ev_search(self, s, ev, out, record):
        pid = ev.get("place") or s.location
        place = self.case.place_by_id.get(pid)
        if not place:
            return self._err(out, "Search where?")
        s.location = pid
        spots = [h for h in place.get("hotspots", []) or [] if (h.get("action") or "EXAMINE") in SEARCH_ACTIONS]
        if not spots:
            labels = [h.get("label") or h.get("id") for h in place.get("hotspots", []) or []]
            out.emit("info", text="Nothing to search here." + (
                " Try examining: %s." % ", ".join(labels) if labels else ""))
            return False
        found, cost, blocked = [], 0, []
        for h in spots:
            if not self.hotspot_ok(s, place, h):
                blocked.append(h.get("label") or h.get("id"))
                continue
            new = [x for x in h.get("reveals", []) or [] if x not in s.seen and x not in found]
            if new:
                found += new
                cost = max(cost, self.case.cost(h.get("action")))
        if not found:
            out.emit("info", text="You search %s and find nothing new.%s" % (
                place.get("name"), (" (%s: not now)" % ", ".join(blocked)) if blocked else ""))
            return False
        out.emit("search", place=pid)
        for x in found:
            self._see(s, x, out, via=pid)
        self._advance(s, cost, out, record)
        return True

    def _ev_link(self, s, ev, out, record):
        # RESOLVED: like contradiction `cards`, a link endpoint may be a claim id (it must be heard).
        a, b = ev.get("a"), ev.get("b")
        for x in (a, b):
            if x not in s.seen and x not in s.heard:
                return self._err(out, "You can only link cards you have.")
        for lk in self.case.links:
            if {lk.get("a"), lk.get("b")} == {a, b}:
                cr = lk.get("creates")
                if cr in s.seen:
                    out.emit("info", text="You've already made that connection.")
                    return False
                s.links_made[cr] = True
                if lk.get("hunch_line"):
                    self._lines(s, [{"id": "LINK-" + str(cr), "text": lk["hunch_line"]}], "HUNCH", out,
                                record, source="link")
                self._see(s, cr, out, via="link")
                return True
        out.emit("info", text="No connection comes to mind.")
        return False

    def available_choices(self, s):
        return [ch for ch in self.case.choices
                if ch.get("id") not in s.chosen and self.holds(ch.get("requires"), s)]

    def _ev_choose(self, s, ev, out, record):
        ch = self.case.choice_by_id.get(ev.get("choice"))
        if not ch or ch not in self.available_choices(s):
            return self._err(out, "That choice isn't open.")
        opt = next((o for o in ch.get("options", []) or [] if o.get("id") == ev.get("option")), None)
        if not opt:
            return self._err(out, "No such option.")
        s.chosen[ch.get("id")] = opt.get("id")
        out.emit("chose", choice=ch.get("id"), option=opt.get("id"), label=opt.get("label"))
        for f in opt.get("sets_flags", []) or []:
            self._flag(s, f, out)
        if opt.get("beat"):
            self.play_beat(s, opt["beat"], out, record)
        self._advance(s, self.case.cost("CHOOSE"), out, record)
        return True

    def _ev_wait(self, s, ev, out, record):
        # RESOLVED (extension): WAIT advances the clock (default 10 min); lets clock-gated beats happen.
        self._advance(s, int(ev.get("minutes", 10) or 10), out, record)
        return True

    # accusation -----------------------------------------------------------------------------
    def ok_proof(self, proof):
        lists = [set(self.case.proof_cards[c]) for c in CATEGORIES]
        if len(proof) != 3:
            return False
        return any(all(p in l for p, l in zip(perm, lists)) for perm in itertools.permutations(proof))

    def _match_answer(self, given, accepted):
        if not accepted:
            return True
        g = norm(given)
        return any(g == norm(a) for a in accepted)

    def evaluate(self, theory):
        """Return (ending dict, condition) for a theory; endings in file order, first match wins."""
        sol = self.case.solution
        who_ok = theory.get("who") == sol.get("who")
        rest_ok = (self._match_answer(theory.get("how", ""), sol.get("how")) and
                   self._match_answer(theory.get("when", ""), sol.get("when")) and
                   self._match_answer(theory.get("why", ""), sol.get("why")))
        proof = list(theory.get("proof", []))
        okp = self.ok_proof(proof)
        cats = {(self.case.card_by_id.get(p) or {}).get("proof_category") for p in proof}
        for e in self.case.endings:
            for cond in str(e.get("condition", "")).split("|"):
                cond = cond.strip()
                m = False
                if cond == "TRUE_SOLUTION":
                    m = who_ok and rest_ok and okp
                elif cond == "BLUFF":
                    m = who_ok and len(proof) == 3 and len(cats) == 1 and None not in cats
                elif cond == "RIGHT_WHO_WRONG_CASE":
                    m = who_ok
                elif cond.startswith("WHO:"):
                    m = theory.get("who") == cond[4:]
                if m:
                    return e, cond
        return {"id": "END-UNRESOLVED", "title": "Case unresolved", "beat": None}, None

    def validate_theory(self, s, theory):
        c = self.case
        who = theory.get("who")
        if not c.accusable(who):
            return "You can't accuse %s." % (c.name_of(who) if who else "nobody")
        proof = list(theory.get("proof", []) or [])
        if len(proof) != 3 or len(set(proof)) != 3:
            return "Pick exactly three different proof cards."
        for p in proof:
            card = c.card_by_id.get(p)
            if not card or p not in s.seen:
                return "You haven't found %s." % p
            if card.get("kind") != "contradiction":
                return "%s isn't a contradiction card." % card.get("title", p)
        return None

    def _ev_accuse(self, s, ev, out, record):
        theory = {k: ev.get(k) for k in ("who", "how", "when", "why")}
        theory["proof"] = list(ev.get("proof", []) or [])
        err = self.validate_theory(s, theory)
        if err:
            return self._err(out, err)
        s.theory = theory
        end, cond = self.evaluate(theory)
        s.ending = end.get("id")
        out.emit("accused", theory=theory)
        if cond == "TRUE_SOLUTION":
            sol = self.case.solution
            # A confession may come only from the accusation or a <KILLER>_CONFESSES-gated storylet.
            conf = self.case.storylet_by_id.get(sol.get("confession_beat"))
            flags = {"%s_CONFESSES" % sol.get("who")}
            if conf:
                flags |= {f for f in ((conf.get("requires") or {}).get("flags_all") or []) if f.endswith("_CONFESSES")}
            for f in sorted(flags):
                self._flag(s, f, out)
            if conf and conf.get("id") != end.get("beat") and conf.get("id") not in s.done:
                self.play(s, conf, out, record)
        out.emit("ending", id=end.get("id"), title=end.get("title"), condition=cond,
                 epilogue_choices=end.get("epilogue_choices", []) or [])
        self.play_beat(s, end.get("beat"), out, record)
        self._advance(s, self.case.cost("ACCUSE"), out, record)
        return True

    def _ev_epilogue(self, s, ev, out, record):
        if not s.ending:
            return self._err(out, "No ending yet.")
        s.epilogue = ev.get("choice")
        out.emit("epilogue", choice=s.epilogue)
        # RESOLVED: epilogue_choices are strings; the ending's epilogue_beats maps a choice label to
        # a storylet id, and a choice that is itself a storylet id plays that beat.
        end = next((e for e in self.case.endings if e.get("id") == s.ending), {})
        beat = (end.get("epilogue_beats") or {}).get(s.epilogue, s.epilogue)
        if beat in self.case.storylet_by_id:
            self.play_beat(s, beat, out, record)
        return False

    # -- accusation option lists (for the guided form) --------------------------------------
    def accusation_options(self, slot, s=None):
        """Answers for how/when/why: solution answers plus decoys, shuffled deterministically."""
        c = self.case
        sol = c.solution
        opts = list(sol.get(slot, []) or [])
        decoys = list(((sol.get("decoys") or {}).get(slot)) or [])
        if not decoys:
            # RESOLVED: without solution.decoys, decoys are drawn from other cards / the timeline.
            if slot == "when":
                decoys = [fmt_clock(e.get("t")) for e in c.timeline if e.get("t") is not None]
            else:
                cat = {"how": "physical", "why": "motive"}[slot]
                decoys = [cd.get("title") for cd in c.cards
                          if cd.get("kind") != "contradiction" and
                          (cd.get("proof_category") == cat or cd.get("role") == "herring")]
        seen, res = set(), []
        for o in opts[:1] + decoys:
            if o and norm(o) not in seen and (norm(o) not in {norm(x) for x in opts[1:]}):
                seen.add(norm(o))
                res.append(o)
        res = res[:6]
        rng = (self.seed * 7919 + len(slot) * 104729) & 0x7FFFFFFF
        for i in range(len(res) - 1, 0, -1):  # deterministic Fisher-Yates
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            j = (rng >> 8) % (i + 1)
            res[i], res[j] = res[j], res[i]
        return res

    # -- offline intent matcher --------------------------------------------------------------
    def match_topic(self, s, text):
        tn = norm(text)
        ts = content_stems(text)
        ks = all_stems(text)
        best, bs = None, 0
        for t in self.case.topics:
            if not self.holds(t.get("requires"), s):
                continue
            sc = keyword_score(tn, ks, t.get("keywords")) * 2
            sc += len(content_stems(t.get("label", "")) & ts)
            if norm(t.get("id", "")) and norm(t.get("id", "")).replace(" ", "_") in tn.replace(" ", "_").split():
                sc += 2
            if sc > bs:
                best, bs = t.get("id"), sc
        return best

    def match_card(self, s, text, pool=None):
        tn = norm(text)
        ts = content_stems(text)
        ks = all_stems(text)
        raw = text.lower()
        best, bs = None, 0
        for cid in (pool if pool is not None else list(s.seen)):
            cd = self.case.card_by_id.get(cid)
            if not cd:
                continue
            sc = keyword_score(tn, ks, cd.get("keywords")) * 2
            sc += len(content_stems(cd.get("title", "")) & ts)
            if cid.lower() in raw:
                sc += 5
            if sc > bs:
                best, bs = cid, sc
        return best

    def match_claim(self, s, text, speaker=None, unbroken=True):
        ts = content_stems(text)
        raw = text.lower()
        best, bs = None, 0
        for clid in s.heard:
            cl = self.case.claim_by_id.get(clid)
            if not cl or (speaker and cl.get("speaker") != speaker) or (unbroken and clid in s.broken):
                continue
            sc = 2 * len(content_stems(cl.get("text", "")) & ts)
            via = self.case.storylet_by_id.get(cl.get("heard_via"))
            if via:  # the words actually spoken count too
                sc += len(content_stems(" ".join(ln.get("text", "") for ln in via.get("lines", []))) & ts)
            if clid.lower() in raw:
                sc += 5
            if sc > bs:
                best, bs = clid, sc
        return best

    def interpret(self, s, cid, text):
        """Offline matcher: free text -> structured event (TALK / PRESENT).

        RESOLVED: verb families are tested in this order: META, DEMAND_CONFESSION, THREATEN, BARGAIN,
        PRESENT (only if a seen card is named), PRESS, REASSURE, then topic overlap (ASK), follow-up
        cues (FOLLOW_UP), else SMALL_TALK. Safety intents first, so "confess and I'll help you" is a
        confession demand, never a reassurance.
        """
        raw = sanitize(text)
        t = " " + raw.lower() + " "
        topic = self.match_topic(s, raw)
        base = {"type": "TALK", "char": cid}
        if re.search(r"\b(ai|a\.i\.|prompt|instructions?|model|system|chatbot|language model|jailbreak)\b", t):
            return dict(base, intent="META")
        if re.search(r"\bconfess|\badmit (that )?you (killed|murdered|did it)|\byou killed (him|her)\b", t):
            return dict(base, intent="DEMAND_CONFESSION")
        if re.search(r"\bhang\b|\bhanged\b|\bjail\b|\bor else\b|\bnoose\b|\bprison\b", t):
            return dict(base, intent="THREATEN", topic=topic)
        if re.search(r"\bdeal\b|\bmoney\b|\blet you go\b|\bbribe\b|\bpay you\b|\bcut me in\b", t):
            return dict(base, intent="BARGAIN")
        if re.search(r"\b(present|show|explain this|explain that|look at this|what about this|how do you explain)\b", t):
            card = self.match_card(s, raw)
            if card:
                claim = self.match_claim(s, raw, speaker=cid)
                ev = {"type": "PRESENT", "char": cid, "card": card}
                if claim:
                    ev["claim"] = claim
                return ev
        if re.search(r"don'?t believe|\blying\b|\bliar\b|\blie\b|\blies\b|come off it|\bnonsense\b|\brubbish\b|\btruth\b", t):
            return dict(base, intent="PRESS", topic=topic or s.last_topic.get(cid))
        if re.search(r"\btrust\b|help me|nobody'?s accusing|no one'?s accusing|\bsafe\b|not in trouble|it'?s all right|it'?s alright|take your time", t):
            return dict(base, intent="REASSURE", topic=topic or s.last_topic.get(cid))
        follow = re.search(r"\b(and then|what then|then what|what else|go on|tell me more|what happened next|why|after that|and\?)\b", t)
        if topic:
            if follow and topic == s.last_topic.get(cid):
                return dict(base, intent="FOLLOW_UP", topic=topic)
            return dict(base, intent="ASK", topic=topic)
        if follow and s.last_topic.get(cid):
            return dict(base, intent="FOLLOW_UP", topic=s.last_topic.get(cid))
        return dict(base, intent="SMALL_TALK")

    # ======================================================================== solver ===========
    def accuse_event(self, s):
        """If one seen contradiction card per proof category exists, return the TRUE accusation."""
        pick = []
        for cat in CATEGORIES:
            p = next((x for x in self.case.proof_cards[cat] if x in s.seen and x not in pick
                      and (self.case.card_by_id.get(x) or {}).get("kind") == "contradiction"), None)
            if not p:
                return None
            pick.append(p)
        sol = self.case.solution
        return {"type": "ACCUSE", "who": sol.get("who"), "how": (sol.get("how") or [""])[0],
                "when": (sol.get("when") or [""])[0], "why": (sol.get("why") or [""])[0], "proof": pick}

    SOLVER_INTENTS = ("ASK", "PRESS", "REASSURE", "FOLLOW_UP", "THREATEN", "SMALL_TALK", "META",
                      "DEMAND_CONFESSION", "BARGAIN")

    def candidates(self, s, allow_choices=True, allow_wait=False):
        """Events that might change progress (storylets that would play, open hotspots, hittable
        contradictions, lock presentations, creatable links, choices)."""
        c = self.case
        evs = []
        open_t = self.open_topics(s)
        open_set = set(open_t)
        order = self._order
        for ch in c.chars:
            cid = ch.get("id")
            if not c.talkable(cid) or self.withdrawn(s, cid):
                continue
            pool = self.eligible_storylets(s, cid)
            if pool:
                # winners per (topic, intent) computed in one pass (same rule as select()).
                explicit, star = {}, {}
                for st in pool:
                    t = st.get("topic")
                    p = (st.get("priority", 0) or 0, -order[id(st)])
                    for intent in (st.get("intents") or DEFAULT_STORYLET_INTENTS):
                        if intent not in self.SOLVER_INTENTS:
                            continue
                        if t == "*":
                            if intent not in star or p > star[intent][0]:
                                star[intent] = (p, st)
                        elif t in open_set:
                            k = (t, intent)
                            if k not in explicit or p > explicit[k][0]:
                                explicit[k] = (p, st)
                got = {}
                for (t, intent), (p, st) in explicit.items():
                    sb = star.get(intent)
                    if sb and sb[0] > p:
                        continue
                    got.setdefault(st.get("id"), (intent, t))
                for intent, (p, st) in star.items():
                    if st.get("id") in got:
                        continue
                    if intent == "ASK":
                        t = next((t for t in open_t if (t, "ASK") not in explicit or explicit[(t, "ASK")][0] < p), None)
                        if t is None:
                            continue
                        got[st.get("id")] = ("ASK", t)
                    else:
                        t = next((t for t in [None] + open_t if t is None or (t, intent) not in explicit
                                  or explicit[(t, intent)][0] < p), None)
                        got[st.get("id")] = (intent, t)
                for sid, (intent, t) in got.items():
                    ev = {"type": "TALK", "char": cid, "intent": intent}
                    if t:
                        ev["topic"] = t
                    evs.append(ev)
                # PRESENT storylets keyed on a card id
                for st in pool:
                    if "PRESENT" in (st.get("intents") or ()) and st.get("topic") in s.seen:
                        evs.append({"type": "PRESENT", "char": cid, "card": st.get("topic")})
            # lock presentations
            locks = s.chars.get(cid, {}).get("locks", {})
            closed = {lk.get("category") for lk in ch.get("locks", []) or [] if not locks.get(lk.get("id"))}
            if closed:
                for card in s.seen:
                    if (c.card_by_id.get(card) or {}).get("proof_category") in closed:
                        evs.append({"type": "PRESENT", "char": cid, "card": card})
        for con in c.contradictions:
            cl = con.get("claim")
            if cl not in s.heard or cl in s.broken:
                continue
            sp = (c.claim_by_id.get(cl) or {}).get("speaker")
            if self.withdrawn(s, sp) or not self.holds(con.get("requires"), s, sp):
                continue
            for card in con.get("cards", []) or []:
                if card in s.seen:
                    evs.append({"type": "PRESENT", "char": sp, "card": card, "claim": cl})
                    break
            else:
                for card in con.get("cards", []) or []:
                    if card in s.heard and card in c.claim_by_id:
                        evs.append({"type": "CONFRONT", "char": sp, "a": cl, "b": card})
                        break
                    other = next((k for k, v in c.claim_testimony.items() if card in v and k in s.heard), None)
                    if other:
                        evs.append({"type": "CONFRONT", "char": sp, "a": cl, "b": other})
                        break
        for key, (place, hs) in c.hotspots.items():
            if any(x not in s.seen for x in hs.get("reveals", []) or []) and self.hotspot_ok(s, place, hs):
                evs.append({"type": "EXAMINE", "hotspot": key})
        for lk in c.links:
            if (lk.get("a") in s.seen or lk.get("a") in s.heard) and \
                    (lk.get("b") in s.seen or lk.get("b") in s.heard) and lk.get("creates") not in s.seen:
                evs.append({"type": "LINK", "a": lk.get("a"), "b": lk.get("b")})
        if allow_choices:
            for ch in self.available_choices(s):
                for o in ch.get("options", []) or []:
                    evs.append({"type": "CHOOSE", "choice": ch.get("id"), "option": o.get("id")})
        if allow_wait:
            evs.append({"type": "WAIT", "minutes": 10})
        return evs

    # relevance (backward regression from the proof cards) ---------------------------------
    def relevance(self, targets=None):
        key = tuple(sorted(targets)) if targets else None
        if self._relevance is not None and key in self._relevance:
            return self._relevance[key]
        c = self.case
        R = set()
        stack = [("card", p) for p in targets] if targets else \
            [("card", p) for cat in CATEGORIES for p in c.proof_cards[cat]]

        def need_expr(expr, cid=None):
            if not expr:
                return
            for f in (expr.get("flags_all") or []) + (expr.get("flags_any") or []):
                stack.append(("flag", f))
            for x in (expr.get("cards_seen_all") or []) + (expr.get("cards_seen_any") or []):
                stack.append(("card", x))
            for x in expr.get("claims_broken_all") or []:
                stack.append(("broken", x))
            if "composure_lte" in expr and cid:
                stack.append(("comp_down", cid))
            if "composure_gte" in expr and cid:
                stack.append(("comp_up", cid))
            if "trust_gte" in expr and cid:
                stack.append(("trust_up", cid))
            if "clock_gte" in expr:
                stack.append(("clock", None))

        def need_contra(con):
            stack.append(("claim", con.get("claim")))
            for x in con.get("cards", []) or []:
                stack.append(("claim", x) if x in c.claim_by_id else ("card", x))
            need_expr(con.get("requires"), (c.claim_by_id.get(con.get("claim")) or {}).get("speaker"))

        def need_story(st):
            stack.append(("story", st.get("id")))

        while stack:
            fact = stack.pop()
            if fact in R:
                continue
            R.add(fact)
            kind, x = fact
            if kind == "card":
                for key, (place, hs) in c.hotspots.items():
                    if x in (hs.get("reveals") or []):
                        need_expr(hs.get("requires"))
                        if (hs.get("action") or "EXAMINE") in SEARCH_ACTIONS:
                            need_expr(place.get("search_requires"))
                for st in c.storylets:
                    if x in (st.get("reveals") or []):
                        need_story(st)
                for con in c.contradictions:
                    if con.get("creates_card") == x:
                        stack.append(("broken", con.get("claim")))
                for lk in c.links:
                    if lk.get("creates") == x:
                        stack += [("card", lk.get("a")), ("card", lk.get("b"))]
                for cid, cards in c.claim_testimony.items():
                    if x in cards:
                        stack.append(("claim", cid))
            elif kind == "claim":
                for st in c.storylets:
                    if x in (st.get("utters_claims") or []):
                        need_story(st)
            elif kind == "broken":
                for con in c.contra_by_claim.get(x, []):
                    need_contra(con)
            elif kind == "flag":
                for st in c.storylets:
                    if x in (st.get("sets_flags") or []):
                        need_story(st)
                for ch in c.choices:
                    for o in ch.get("options", []) or []:
                        if x in (o.get("sets_flags") or []):
                            need_expr(ch.get("requires"))
                            stack.append(("choice", ch.get("id")))
                if x.endswith("_LOCKS_OPEN"):
                    cid = x[: -len("_LOCKS_OPEN")]
                    for lk in (c.char_by_id.get(cid) or {}).get("locks", []) or []:
                        stack.append(("lock", (cid, lk.get("id"))))
            elif kind == "lock":
                cid, lid = x
                lk = next((l for l in (c.char_by_id.get(cid) or {}).get("locks", []) if l.get("id") == lid), {})
                for con in c.contradictions:
                    if con.get("opens_lock") in (lid, lk.get("category")):
                        stack.append(("broken", con.get("claim")))
                for cd in c.cards:
                    if cd.get("proof_category") == lk.get("category"):
                        stack.append(("card", cd.get("id")))
            elif kind == "story":
                st = c.storylet_by_id.get(x) or {}
                need_expr(st.get("requires"), st.get("char"))
                t = c.topic_by_id.get(st.get("topic"))
                if t:
                    need_expr(t.get("requires"))
                for con in c.contradictions:
                    if con.get("result_beat") == x:
                        stack.append(("broken", con.get("claim")))
                for sc in c.scheduled:
                    if sc.get("beat") == x:
                        need_expr(sc.get("only_if"), st.get("char"))
                        stack.append(("clock", None))
                for ch in c.choices:
                    for o in ch.get("options", []) or []:
                        if o.get("beat") == x:
                            need_expr(ch.get("requires"))
            elif kind in ("comp_down", "comp_up", "trust_up"):
                sign = -1 if kind == "comp_down" else 1
                field = "trust_delta" if kind == "trust_up" else "composure_delta"
                for st in c.storylets_by_char.get(x, []):
                    if (st.get(field, 0) or 0) * sign > 0:
                        need_story(st)
                if kind == "comp_down":
                    for con in c.contradictions:
                        if (c.claim_by_id.get(con.get("claim")) or {}).get("speaker") == x and \
                                (con.get("composure_delta", 0) or 0) < 0:
                            stack.append(("broken", con.get("claim")))
        if self._relevance is None:
            self._relevance = {}
        self._relevance[key] = R
        return R

    def _gain(self, s, s2, R):
        """True if s -> s2 gained a relevant fact."""
        for kind, a, b in (("card", s.seen, s2.seen), ("claim", s.heard, s2.heard),
                           ("broken", s.broken, s2.broken), ("flag", s.flags, s2.flags)):
            if len(b) != len(a):
                for x in b:
                    if x not in a and (kind, x) in R:
                        return True
        for cid, v2 in s2.chars.items():
            v = s.chars[cid]
            if v2["composure"] < v["composure"] and ("comp_down", cid) in R:
                return True
            if v2["composure"] > v["composure"] and ("comp_up", cid) in R:
                return True
            if v2["trust"] > v["trust"] and ("trust_up", cid) in R:
                return True
            if v2["locks"] != v["locks"]:
                return True
        if len(s2.done) != len(s.done):
            for x in s2.done:
                if x not in s.done and ("story", x) in R:
                    return True
        if s2.sched_fired != s.sched_fired:
            return True
        return False

    def _h(self, s, R, goal=None):
        if goal:
            targets, need = goal
            missing_cats = max(0, need - sum(1 for t in targets if t in s.seen))
        else:
            missing_cats = sum(1 for cat in CATEGORIES if not any(p in s.seen for p in self.case.proof_cards[cat]))
        miss = 0
        for kind, x in R:
            if kind == "card" and x not in s.seen:
                miss += 1
            elif kind == "claim" and x not in s.heard:
                miss += 1
            elif kind == "broken" and x not in s.broken:
                miss += 1
            elif kind == "flag" and x not in s.flags:
                miss += 1
        return missing_cats * 1000 + miss

    def _needs_wait(self):
        if self.case.scheduled:
            return True
        return any("clock_gte" in (st.get("requires") or {}) for st in self.case.storylets)

    def solve(self, mode="best", node_cap=20000, allow_choices=True, relevant_only=True, start=None,
              time_budget=None, goal=None, weight=0):
        """Find events reaching TRUE_SOLUTION. mode 'bfs' = fewest actions (within the productive-action
        graph); 'best' = greedy best-first. goal=(cards, k) instead stops once k of `cards` are seen
        (no accusation appended). Returns (path or None, stats dict)."""
        R = self.relevance(goal[0] if goal else None)
        s0 = start or self.start(record=False)[0]
        wait = self._needs_wait()
        stats = {"expanded": 0, "exhausted": False, "capped": False}
        counter = itertools.count()
        visited = {s0.key()}
        if mode == "bfs":
            frontier = deque([(s0, [])])
            pop = frontier.popleft
            push = lambda h, d, st, p: frontier.append((st, p))  # noqa: E731
        else:
            frontier = [(self._h(s0, R, goal), 0, next(counter), s0, [])]
            pop = lambda: heapq.heappop(frontier)[3:]  # noqa: E731
            push = lambda h, d, st, p: heapq.heappush(frontier, (h, d, next(counter), st, p))  # noqa: E731
        import time as _time
        t0 = _time.time()
        while frontier:
            if stats["expanded"] >= node_cap or (time_budget and _time.time() - t0 > time_budget):
                stats["capped"] = True
                return None, stats
            s, path = pop()
            stats["expanded"] += 1
            stats["depth"] = len(path)
            if goal:
                if sum(1 for t in goal[0] if t in s.seen) >= goal[1]:
                    return path, stats
                acc = None
            else:
                acc = self.accuse_event(s)
            if acc:
                s2, _ = self.step(s, acc, record=False)
                if s2.ending and s2.ending == self.case.true_ending:
                    return path + [acc], stats
            for ev in self.candidates(s, allow_choices=allow_choices, allow_wait=wait):
                s2, out = self.step(s, ev, record=False)
                if s2 is s or s2.ending:
                    continue
                k = s2.key()
                if k in visited:
                    continue
                if relevant_only and not self._gain(s, s2, R):
                    continue
                visited.add(k)
                push(self._h(s2, R, goal) + weight * (len(path) + 1), len(path) + 1, s2, path + [ev])
        stats["exhausted"] = True
        return None, stats

    def replay_reaches_true(self, events):
        s = self.start(record=False)[0]
        for ev in events:
            s2, out = self.step(s, ev, record=False)
            if s2 is s and any(o["kind"] == "error" for o in out):
                return False
            s = s2
            if s.ending and s.ending != self.case.true_ending:
                return False
        return s.ending is not None and s.ending == self.case.true_ending

    def minimize(self, path):
        """Drop actions one at a time while the replay still reaches TRUE_SOLUTION (1-minimal)."""
        path = list(path)
        changed = True
        while changed:
            changed = False
            for i in range(len(path) - 2, -1, -1):
                trial = path[:i] + path[i + 1:]
                if self.replay_reaches_true(trial):
                    path = trial
                    changed = True
        return path

    def find_solution(self, node_cap=20000):
        """Autoplay path: best-first on relevant actions, falling back to an unpruned search."""
        for relevant in (True, False):
            path, st = self.solve("best", node_cap=node_cap, relevant_only=relevant)
            if path:
                return self.minimize(path), st
        return None, st

    def saturate(self, start=None, allow_choices=True, max_steps=3000):
        """Greedy 'do everything' playthrough that never triggers an ending. Returns the final state."""
        s = start or self.start(record=False)[0]
        visited = {s.key()}
        for _ in range(max_steps):
            moved = False
            for ev in self.candidates(s, allow_choices=allow_choices):
                s2, _ = self.step(s, ev, record=False)
                if s2 is s or s2.ending:
                    continue
                k = s2.key()
                if k in visited:
                    continue
                visited.add(k)
                s = s2
                moved = True
                break
            if not moved:
                break
        return s


def _clamp(v):
    return max(CLAMP[0], min(CLAMP[1], int(v)))


def describe_event(case, ev):
    """Human command for an event (used by autoplay output)."""
    t = ev.get("type")
    n = lambda cid: case.short_name(cid)  # noqa: E731
    if t == "TALK":
        tl = (case.topic_by_id.get(ev.get("topic")) or {}).get("label") or ev.get("topic")
        verb = {"ASK": "ask", "FOLLOW_UP": "follow up with", "PRESS": "press", "REASSURE": "reassure",
                "THREATEN": "threaten", "SMALL_TALK": "chat with", "META": "meta-question",
                "DEMAND_CONFESSION": "demand a confession from", "BARGAIN": "bargain with"}.get(ev["intent"], ev["intent"])
        return "%s %s%s" % (verb, n(ev["char"]), (" about %s" % tl) if tl else "")
    if t == "PRESENT":
        card = (case.card_by_id.get(ev["card"]) or {}).get("title", ev["card"])
        if ev.get("claim"):
            return "present %s (%s) to %s's claim %s" % (card, ev["card"], n(ev.get("char")), ev["claim"])
        return "present %s (%s) to %s" % (card, ev["card"], n(ev.get("char")))
    if t == "CONFRONT":
        return "confront %s: %s vs %s" % (n(ev.get("char")), ev["a"], ev["b"])
    if t == "EXAMINE":
        place, hs = case.hotspots.get(ev["hotspot"], ({}, {}))
        return "examine %s (%s)" % (hs.get("label") or hs.get("id"), place.get("name"))
    if t == "SEARCH":
        return "search %s" % ((case.place_by_id.get(ev.get("place")) or {}).get("name") or "here")
    if t == "LINK":
        return "link %s %s" % (ev["a"], ev["b"])
    if t == "CHOOSE":
        ch = case.choice_by_id.get(ev["choice"]) or {}
        o = next((o for o in ch.get("options", []) if o.get("id") == ev["option"]), {})
        return "choose: %s" % (o.get("label") or ev["option"])
    if t == "WAIT":
        return "wait %d" % ev.get("minutes", 10)
    if t == "ACCUSE":
        return "accuse %s (how: %s; when: %s; why: %s; proof: %s)" % (
            n(ev["who"]), ev["how"], ev["when"], ev["why"], ", ".join(ev["proof"]))
    return json.dumps(ev)
