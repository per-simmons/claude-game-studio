#!/usr/bin/env python3
"""Case-pack linter: rules 1-9 of skills/studio/references/case-pack-format.md.

    python3 scripts/casepack/lint.py <pack-dir> [--json] [--stamp] [--node-cap N]

Exit 0 when every rule passes, 1 otherwise. --stamp writes lint.passed into casepack.json.
Standard library only; uses `jsonschema` for rule 1 when it is installed, otherwise a built-in
validator that covers the subset of JSON Schema the case-file schema uses.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E  # noqa: E402

LINTER_VERSION = "1"
SCHEMA_PATH = os.path.normpath(os.path.join(HERE, "..", "..", "skills", "studio", "references",
                                            "case-file.schema.json"))
ENDING_CONDS = ("TRUE_SOLUTION", "BLUFF", "RIGHT_WHO_WRONG_CASE", "TIMEOUT")
TRIGGERS = ("card_seen", "claim_heard", "claim_broken", "link_created", "storylet_done", "tell", "tell_fired",
            "latency_flag")


# ------------------------------------------------------------------ mini JSON Schema validator
def _type_ok(v, t):
    if isinstance(t, list):
        return any(_type_ok(v, x) for x in t)
    return {
        "object": lambda: isinstance(v, dict),
        "array": lambda: isinstance(v, list),
        "string": lambda: isinstance(v, str),
        "integer": lambda: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda: isinstance(v, bool),
        "null": lambda: v is None,
    }.get(t, lambda: True)()


def mini_validate(inst, schema, root, path="$", errors=None, limit=200):
    if errors is None:
        errors = []
    if len(errors) >= limit:
        return errors
    if "$ref" in schema:
        ref = schema["$ref"]
        node = root
        for part in ref.lstrip("#/").split("/"):
            node = node[part]
        return mini_validate(inst, node, root, path, errors, limit)
    if "anyOf" in schema:
        if not any(not mini_validate(inst, sub, root, path, [], limit) for sub in schema["anyOf"]):
            errors.append("%s: matches none of anyOf" % path)
        return errors
    if "type" in schema and not _type_ok(inst, schema["type"]):
        errors.append("%s: expected %s, got %s" % (path, schema["type"], type(inst).__name__))
        return errors
    if "enum" in schema and inst not in schema["enum"]:
        errors.append("%s: %r not one of %s" % (path, inst, schema["enum"]))
    if "const" in schema and inst != schema["const"]:
        errors.append("%s: must equal %r" % (path, schema["const"]))
    if isinstance(inst, str) and "pattern" in schema and not re.search(schema["pattern"], inst):
        errors.append("%s: %r does not match %s" % (path, inst, schema["pattern"]))
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            errors.append("%s: %s < minimum %s" % (path, inst, schema["minimum"]))
        if "maximum" in schema and inst > schema["maximum"]:
            errors.append("%s: %s > maximum %s" % (path, inst, schema["maximum"]))
    if isinstance(inst, dict):
        for r in schema.get("required", []):
            if r not in inst:
                errors.append("%s: missing required %r" % (path, r))
        props = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)
        for k, v in inst.items():
            if k in props:
                mini_validate(v, props[k], root, "%s.%s" % (path, k), errors, limit)
            elif addl is False:
                errors.append("%s: unexpected property %r" % (path, k))
            elif isinstance(addl, dict):
                mini_validate(v, addl, root, "%s.%s" % (path, k), errors, limit)
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errors.append("%s: fewer than %d items" % (path, schema["minItems"]))
        if "items" in schema:
            for i, v in enumerate(inst):
                mini_validate(v, schema["items"], root, "%s[%d]" % (path, i), errors, limit)
    return errors


# ------------------------------------------------------------------ relaxed reachability
def relaxed(case, allow_choices=True, card_ok=None):
    """Delete-relaxed fixpoint: what is obtainable if order never matters (flags_none, composure,
    trust and clock conditions assumed satisfiable). Returns dict of reachable sets."""
    c = case
    C, H, B, F, ST = set(), set(), set(), set(), set()
    locks = {}
    card_ok = card_ok or (lambda x: True)

    def ok(expr):
        if not expr:
            return True
        if any(x not in F for x in expr.get("flags_all") or []):
            return False
        fa = expr.get("flags_any")
        if fa and not any(x in F for x in fa):
            return False
        if any(x not in C for x in expr.get("cards_seen_all") or []):
            return False
        ca = expr.get("cards_seen_any")
        if ca and not any(x in C for x in ca):
            return False
        if any(x not in B for x in expr.get("claims_broken_all") or []):
            return False
        return True

    def see(x):
        if x and x not in C and card_ok(x) and x in c.card_by_id:
            C.add(x)
            return True
        return False

    def apply_st(st):
        ch = False
        if st.get("id") not in ST:
            ST.add(st.get("id"))
            ch = True
        for x in st.get("utters_claims") or []:
            if x not in H:
                H.add(x)
                ch = True
        for x in st.get("reveals") or []:
            ch = see(x) or ch
        for f in st.get("sets_flags") or []:
            if f not in F:
                F.add(f)
                ch = True
        return ch

    talk = set(E.TALK_INTENTS) - {"PRESENT", "CONFRONT"}
    changed = True
    while changed:
        changed = False
        for st in c.storylets:
            if st.get("id") in ST or not c.talkable(st.get("char")):
                continue
            intents = set(st.get("intents") or E.DEFAULT_STORYLET_INTENTS)
            t = st.get("topic")
            if "PRESENT" in intents and t in C:
                pass
            elif not (intents & talk):
                continue
            elif t != "*" and (t not in c.topic_by_id or not ok(c.topic_by_id[t].get("requires"))):
                continue
            if ok(st.get("requires")):
                changed = apply_st(st) or changed
        for key, (place, hs) in c.hotspots.items():
            if ok(hs.get("requires")) and ((hs.get("action") or "EXAMINE") not in E.SEARCH_ACTIONS
                                           or ok(place.get("search_requires"))):
                for x in hs.get("reveals") or []:
                    changed = see(x) or changed
        for con in c.contradictions:
            if con.get("claim") in B or con.get("claim") not in H or not ok(con.get("requires")):
                continue
            cands = set(C) | set(H) | {t for k in H for t in c.claim_testimony.get(k, [])}
            if any(x in cands for x in con.get("cards") or []):
                B.add(con.get("claim"))
                changed = True
                bt = c.storylet_by_id.get(con.get("result_beat"))
                if bt:
                    apply_st(bt)
                see(con.get("creates_card"))
                if con.get("opens_lock"):
                    sp = (c.claim_by_id.get(con.get("claim")) or {}).get("speaker")
                    locks.setdefault(sp, set()).add(con["opens_lock"])
        for lk in c.links:
            if (lk.get("a") in C or lk.get("a") in H) and (lk.get("b") in C or lk.get("b") in H):
                changed = see(lk.get("creates")) or changed
        for sc in c.scheduled:
            bt = c.storylet_by_id.get(sc.get("beat"))
            if bt and bt.get("id") not in ST and ok(sc.get("only_if")):
                changed = apply_st(bt) or changed
        if allow_choices:
            for ch in c.choices:
                if ok(ch.get("requires")):
                    for o in ch.get("options") or []:
                        for f in o.get("sets_flags") or []:
                            if f not in F:
                                F.add(f)
                                changed = True
                        bt = c.storylet_by_id.get(o.get("beat"))
                        if bt and bt.get("id") not in ST:
                            changed = apply_st(bt) or changed
        for ch in c.chars:
            cid = ch.get("id")
            lks = ch.get("locks") or []
            if not lks:
                continue
            got = locks.setdefault(cid, set())
            for lk in lks:
                if any((c.card_by_id.get(x) or {}).get("proof_category") == lk.get("category") for x in C):
                    got.add(lk.get("id"))
            if all(lk.get("id") in got or lk.get("category") in got for lk in lks):
                f = "%s_LOCKS_OPEN" % cid
                if f not in F:
                    F.add(f)
                    changed = True
    return {"cards": C, "claims": H, "broken": B, "flags": F, "storylets": ST, "ok": ok}


# ------------------------------------------------------------------ the linter
class Report:
    def __init__(self):
        self.rules = []
        self.warnings = []

    def rule(self, n, name, passed, details=None, info=None):
        self.rules.append({"rule": n, "name": name, "passed": bool(passed), "details": details or [],
                           "info": info or {}})

    @property
    def passed(self):
        return all(r["passed"] for r in self.rules)


def choice_flags(case):
    return {f for ch in case.choices for o in ch.get("options") or [] for f in o.get("sets_flags") or []}


def lint(pack_dir, node_cap=200000, time_budget=12.0):
    rep = Report()
    pack_dir = os.path.abspath(pack_dir)
    manifest = {}
    mpath = os.path.join(pack_dir, "casepack.json")
    if os.path.exists(mpath):
        try:
            manifest = E.load_json(mpath)
        except Exception as ex:  # noqa: BLE001
            rep.rule(1, "Structure", False, ["casepack.json is not valid JSON: %s" % ex])
            return rep, None
    else:
        rep.warnings.append("No casepack.json manifest (required for sharing).")
    case_path = os.path.join(pack_dir, manifest.get("case_file", "case-file.json"))
    try:
        data = E.load_json(case_path)
    except Exception as ex:  # noqa: BLE001
        rep.rule(1, "Structure", False, ["Cannot read %s: %s" % (case_path, ex)])
        return rep, None
    if not os.path.exists(os.path.join(pack_dir, "README.md")):
        rep.warnings.append("No README.md (required).")
    if manifest and manifest.get("format") != E.FORMAT:
        rep.warnings.append("casepack.json format is %r, expected %r." % (manifest.get("format"), E.FORMAT))

    # ---- rule 1: structure
    errs, validator = [], "built-in"
    schema = E.load_json(SCHEMA_PATH) if os.path.exists(SCHEMA_PATH) else None
    if schema is None:
        rep.warnings.append("Schema not found at %s; structural checks only." % SCHEMA_PATH)
        for k in ("meta", "clock", "places", "characters", "cards", "claims", "contradictions", "links",
                  "storylets", "solution", "endings", "timeline", "topics"):
            if k not in data:
                errs.append("$: missing required %r" % k)
    else:
        try:
            import jsonschema  # type: ignore
            validator = "jsonschema %s" % getattr(jsonschema, "__version__", "")
            v = jsonschema.Draft202012Validator(schema)
            errs = ["%s: %s" % ("$" + "".join("[%r]" % p for p in e.absolute_path), e.message)
                    for e in v.iter_errors(data)][:200]
        except ImportError:
            errs = mini_validate(data, schema, schema)
    rep.rule(1, "Structure (schema, %s)" % validator, not errs, errs[:40])
    if errs:
        # keep going only if the core arrays are usable
        core = all(isinstance(data.get(k), list) for k in ("characters", "cards", "claims", "storylets", "endings"))
        if not core:
            return rep, None

    case = E.Case(data, manifest=manifest, pack_dir=pack_dir)
    eng = E.Engine(case, seed=0)

    # ---- rule 2: IDs resolve
    rep.rule(2, "Every referenced ID exists", *_check_ids(case, rep))

    # ---- rule 4: herrings
    bad = ["%s is a herring with no herring_resolution" % c.get("id") for c in case.cards
           if c.get("role") == "herring" and not (c.get("herring_resolution") or "").strip()]
    rep.rule(4, "Every herring has a herring_resolution", not bad, bad)

    # ---- rule 3: three-clue rule (choices off)
    rx_all = relaxed(case, allow_choices=True)
    rx = relaxed(case, allow_choices=False)
    routes, details = {}, []
    for cat in E.CATEGORIES:
        r_core = _routes(case, cat, rx)
        r_all = _routes(case, cat, rx_all)
        routes[cat] = {"routes": len(r_core), "with_optional": len(r_all), "list": sorted(r_core)}
        if not case.proof_cards[cat]:
            details.append("%s: solution.proof.%s is empty" % (cat, cat))
        elif len(r_core) < 3:
            details.append("%s: only %d route(s) with optional branches off (%d with them): %s" % (
                cat, len(r_core), len(r_all), ", ".join(sorted(r_core)) or "none"))
    rep.rule(3, "Three Clue Rule (>=3 routes per proof category, optional branches off)", not details, details,
             {"routes": routes, "optional_flags": sorted(choice_flags(case))})

    # ---- rule 6: leak check
    proof_set = {p for cat in E.CATEGORIES for p in case.proof_cards[cat]}
    no_act = [c.get("id") for c in case.cards if "act" not in c]
    if no_act:
        rep.warnings.append("Cards without `act` are treated as Act 1 by the leak check: %s" % ", ".join(no_act[:12]))
    act1 = lambda x: (case.card_by_id.get(x) or {}).get("act", 1) == 1 or x in proof_set  # noqa: E731
    rx1 = relaxed(case, allow_choices=True, card_ok=act1)
    leaks = []
    for cat in E.CATEGORIES:
        hit = [p for p in case.proof_cards[cat] if p in rx1["cards"]]
        if hit:
            leaks.append("%s can be completed from Act-1 cards only (via %s)" % (cat, ", ".join(hit)))
    rep.rule(6, "Leak check (no proof category from Act-1 cards)", not leaks, leaks)

    # ---- rules 9 + 7: solve, then minimal path
    min_req = int(((manifest.get("lint") or {}).get("min_path_actions")) or 16)
    path, st = eng.find_solution(node_cap=min(node_cap, 50000))
    sol_info = {}
    if path:
        s_end, outs = eng.replay(path)
        sol_info = {"actions": len(path), "game_minutes": s_end.clock - case.start,
                    "path": [E.describe_event(case, ev) for ev in path]}
        rep.rule(9, "Offline player can finish the true ending", s_end.ending == case.true_ending,
                 [] if s_end.ending == case.true_ending else ["replay ended in %s" % s_end.ending], sol_info)
    else:
        rep.rule(9, "Offline player can finish the true ending", False,
                 ["no path to TRUE_SOLUTION found (%s, %d states expanded)" % (
                     "search space exhausted" if st.get("exhausted") else "node cap hit", st.get("expanded", 0))])
    if path:
        bpath, bst = eng.solve("bfs", node_cap=node_cap, time_budget=time_budget)
        if bpath:
            n, exact, lb = len(bpath), True, len(bpath)
        else:
            exact, lb = False, bst.get("depth", 0) + 1
            best = path
            for w in (1, 2, 3):  # depth-weighted best-first finds shorter paths than pure greedy
                wp, _ = eng.solve("best", node_cap=node_cap, weight=w, time_budget=max(2.0, time_budget / 3))
                if wp:
                    wp = eng.minimize(wp)
                    if len(wp) < len(best):
                        best = wp
            bpath, n = best, len(best)
        if exact:
            note = "exact BFS over productive actions"
        else:
            note = ("BFS budget ran out at depth %d; %d is a 1-minimal greedy path, an upper bound "
                    "(true minimum is between %d and %d)" % (lb - 1, n, lb, n))
        passed = n >= min_req
        if passed and not exact and lb < min_req:
            rep.warnings.append("rule 7 not proven: the shortest path found is %d actions, but a shorter one "
                                "can't be ruled out (raise --node-cap/--time-budget)" % n)
        rep.rule(7, "Minimal path >= %d actions" % min_req, passed,
                 [] if passed else ["a %d-action path reaches the true ending%s" % (n, "" if exact else " (found by search; so the minimum is at most %d)" % n)],
                 {"minimal_actions": n, "lower_bound": lb, "exact": exact, "note": note,
                  "path": [E.describe_event(case, ev) for ev in bpath]})
    else:
        rep.rule(7, "Minimal path >= %d actions" % min_req, False, ["no solution path to measure"])

    # ---- rule 5: endings reachable
    rep.rule(5, "Every ending is reachable", *_check_endings(case, eng, path))

    # ---- rule 8: facts_allowed gates
    rep.rule(8, "No solution fact in a writer storylet's facts_allowed before its gate (best effort)",
             *_check_facts(case, rx1))

    _warnings(case, eng, rx_all, rep)
    rep.rules.sort(key=lambda r: r["rule"])
    return rep, case


def _routes(case, cat, rx):
    """Distinct ways to obtain a card in solution.proof[cat] in the relaxed world `rx`."""
    ok = rx["ok"]
    C, H = rx["cards"], rx["claims"]
    out = set()
    for p in case.proof_cards[cat]:
        for key, (place, hs) in case.hotspots.items():
            if p in (hs.get("reveals") or []) and ok(hs.get("requires")) and (
                    (hs.get("action") or "EXAMINE") not in E.SEARCH_ACTIONS or ok(place.get("search_requires"))):
                out.add("examine %s -> %s" % (key, p))
        for st in case.storylets:
            if p in (st.get("reveals") or []) and st.get("id") in rx["storylets"] and \
                    not any(con.get("result_beat") == st.get("id") for con in case.contradictions):
                out.add("storylet %s -> %s" % (st.get("id"), p))
        for con in case.contradictions:
            if con.get("creates_card") != p and not (
                    p in ((case.storylet_by_id.get(con.get("result_beat")) or {}).get("reveals") or [])):
                continue
            if con.get("claim") not in H or not ok(con.get("requires")):
                continue
            tcards = {t for k in H for t in case.claim_testimony.get(k, [])}
            for x in con.get("cards") or []:
                if x in C or x in H or x in tcards:
                    out.add("%s: %s vs %s -> %s" % (con.get("id"), x, con.get("claim"), p))
        for lk in case.links:
            if lk.get("creates") == p and (lk.get("a") in C or lk.get("a") in H) and \
                    (lk.get("b") in C or lk.get("b") in H):
                out.add("link %s + %s -> %s" % (lk.get("a"), lk.get("b"), p))
    return out


def _check_ids(case, rep):
    c = case
    errs = []
    ids = {"characters": c.chars, "cards": c.cards, "claims": c.claims, "storylets": c.storylets,
           "contradictions": c.contradictions, "endings": c.endings, "places": c.places}
    for coll, items in ids.items():
        seen = set()
        for it in items:
            i = it.get("id")
            if i in seen:
                errs.append("duplicate id %s in %s" % (i, coll))
            seen.add(i)
    allids = {}
    for coll, items in ids.items():
        for it in items:
            allids.setdefault(it.get("id"), []).append(coll)
    for i, colls in allids.items():
        if len(colls) > 1:
            rep.warnings.append("id %s is used in %s" % (i, " and ".join(colls)))
    CH, CA, CL, ST = c.char_by_id, c.card_by_id, c.claim_by_id, c.storylet_by_id
    PL, TP = c.place_by_id, c.topic_by_id
    known_flags = set()
    for s in c.storylets:
        known_flags |= set(s.get("sets_flags") or [])
    known_flags |= choice_flags(c)
    known_flags |= {"%s_LOCKS_OPEN" % ch.get("id") for ch in c.chars if ch.get("locks")}
    known_flags |= {"%s_CONFESSES" % c.solution.get("who")}

    def need(kind, ref, where):
        table = {"char": CH, "card": CA, "claim": CL, "storylet": ST, "place": PL, "topic": TP}[kind]
        if ref not in table:
            errs.append("%s: unknown %s %r" % (where, kind, ref))

    def expr(e, where):
        if not e:
            return
        for x in (e.get("cards_seen_all") or []) + (e.get("cards_seen_any") or []):
            need("card", x, where)
        for x in e.get("claims_broken_all") or []:
            need("claim", x, where)
        for f in (e.get("flags_all") or []) + (e.get("flags_any") or []) + (e.get("flags_none") or []):
            if f not in known_flags:
                rep.warnings.append("%s: flag %r is never set by anything" % (where, f))

    for p in c.places:
        expr(p.get("search_requires"), "place %s" % p.get("id"))
        for h in p.get("hotspots") or []:
            for x in h.get("reveals") or []:
                need("card", x, "hotspot %s/%s" % (p.get("id"), h.get("id")))
            expr(h.get("requires"), "hotspot %s/%s" % (p.get("id"), h.get("id")))
    for s in c.storylets:
        w = "storylet %s" % s.get("id")
        need("char", s.get("char"), w)
        talk_sel = bool(set(s.get("intents") or E.DEFAULT_STORYLET_INTENTS) & (set(E.TALK_INTENTS) - {"PRESENT"}))
        if s.get("topic") != "*" and s.get("topic") not in TP and s.get("topic") not in CA:
            if talk_sel:
                errs.append("%s: unknown topic %r" % (w, s.get("topic")))
            else:  # beat-only storylets (SCHEDULED/ACCUSE/PRESENT...): topic is informational
                rep.warnings.append("%s: topic %r is not a topic id (fine for a beat-only storylet)" % (w, s.get("topic")))
        for x in s.get("utters_claims") or []:
            need("claim", x, w)
        for x in s.get("reveals") or []:
            need("card", x, w)
        for ln in s.get("lines") or []:
            if ln.get("speaker"):
                need("char", ln["speaker"], w + " line " + str(ln.get("id")))
        expr(s.get("requires"), w)
    for t in c.topics:
        expr(t.get("requires"), "topic %s" % t.get("id"))
    for cl in c.claims:
        need("char", cl.get("speaker"), "claim %s" % cl.get("id"))
        if cl.get("heard_via") and cl["heard_via"] not in ST and cl["heard_via"] not in c.line_owner:
            errs.append("claim %s: heard_via %r is not a storylet or line id" % (cl.get("id"), cl["heard_via"]))
    for cd in c.cards:
        if cd.get("source_line") and cd["source_line"] not in c.line_owner:
            errs.append("card %s: source_line %r is not a line id" % (cd.get("id"), cd["source_line"]))
    for con in c.contradictions:
        w = "contradiction %s" % con.get("id")
        need("claim", con.get("claim"), w)
        for x in con.get("cards") or []:
            if x not in CA and x not in CL:
                errs.append("%s: unknown card/claim %r" % (w, x))
        need("storylet", con.get("result_beat"), w)
        if con.get("creates_card"):
            need("card", con.get("creates_card"), w)
        if con.get("opens_lock"):
            sp = (CL.get(con.get("claim")) or {}).get("speaker")
            lks = (CH.get(sp) or {}).get("locks") or []
            if not any(con["opens_lock"] in (l.get("id"), l.get("category")) for l in lks):
                errs.append("%s: opens_lock %r is not a lock of %s" % (w, con["opens_lock"], sp))
        expr(con.get("requires"), w)
    for lk in c.links:
        for k in ("a", "b"):
            if lk.get(k) not in CA and lk.get(k) not in CL:
                errs.append("link %s+%s: unknown card/claim %r" % (lk.get("a"), lk.get("b"), lk.get(k)))
        need("card", lk.get("creates"), "link %s+%s" % (lk.get("a"), lk.get("b")))
    sol = c.solution
    need("char", sol.get("who"), "solution.who")
    for cat in E.CATEGORIES:
        for x in c.proof_cards[cat]:
            need("card", x, "solution.proof.%s" % cat)
            cd = CA.get(x)
            if cd and cd.get("kind") != "contradiction":
                errs.append("solution.proof.%s: %s is %s, but proof cards must be contradiction cards" % (
                    cat, x, cd.get("kind")))
    if sol.get("confession_beat"):
        need("storylet", sol["confession_beat"], "solution.confession_beat")
        conf = ST.get(sol["confession_beat"]) or {}
        fl = (conf.get("requires") or {}).get("flags_all") or []
        if not any(f.endswith("_CONFESSES") for f in fl):
            rep.warnings.append("confession_beat %s is not gated on flags_all [\"<KILLER>_CONFESSES\"]" % conf.get("id"))
    for e in c.endings:
        need("storylet", e.get("beat"), "ending %s" % e.get("id"))
        for cond in str(e.get("condition", "")).split("|"):
            cond = cond.strip()
            if cond.startswith("WHO:"):
                need("char", cond[4:], "ending %s" % e.get("id"))
            elif cond not in ENDING_CONDS:
                errs.append("ending %s: unknown condition %r" % (e.get("id"), cond))
        if "|" in str(e.get("condition", "")):
            rep.warnings.append("ending %s uses '|' (an extension of the terminal player)" % e.get("id"))
    for sc in c.scheduled:
        need("storylet", sc.get("beat"), "clock.scheduled at %s" % sc.get("at"))
        expr(sc.get("only_if"), "clock.scheduled at %s" % sc.get("at"))
    for h in c.hunch:
        kind, _, arg = (h.get("trigger") or "").partition(":")
        w = "hunch %s" % h.get("id")
        if kind not in TRIGGERS:
            errs.append("%s: unknown trigger %r" % (w, h.get("trigger")))
        elif kind in ("card_seen", "link_created"):
            need("card", arg, w)
        elif kind in ("claim_heard", "claim_broken"):
            need("claim", arg, w)
        elif kind == "storylet_done":
            need("storylet", arg, w)
        elif kind in ("tell", "tell_fired", "latency_flag"):
            need("char", arg.split(":")[0], w)
    for ch in c.chars:
        for w in ch.get("whereabouts") or []:
            need("place", w.get("place"), "character %s whereabouts" % ch.get("id"))
        for t in ch.get("tiers") or []:
            expr(t.get("requires"), "character %s tier %s" % (ch.get("id"), t.get("tier")))
    for t in c.timeline:
        for x in t.get("who") or []:
            need("char", x, "timeline t=%s" % t.get("t"))
        for x in t.get("traces") or []:
            if x not in CA:
                errs.append("timeline t=%s: unknown trace %r" % (t.get("t"), x))
    for owner in c.refusals:
        if owner != "*" and owner not in CH:
            errs.append("refusals: unknown character %r" % owner)
    for ch in c.choices:
        expr(ch.get("requires"), "choice %s" % ch.get("id"))
        for o in ch.get("options") or []:
            if o.get("beat"):
                need("storylet", o["beat"], "choice %s option %s" % (ch.get("id"), o.get("id")))
    return (not errs, errs[:60])


def _check_endings(case, eng, path):
    errs, info = [], {}
    if not case.endings:
        return False, ["no endings"], info
    reached = {}
    if path:
        reached[case.true_ending] = "autoplay"
    # rich states: saturate from the start, and from the solution's pre-accusation state
    states = [eng.saturate()]
    if path:
        s_pre, _ = eng.replay(path[:-1])
        states.append(eng.saturate(start=s_pre))
    # BLUFF needs three same-category contradiction cards in one run: search for each category
    if any(e.get("condition") == "BLUFF" for e in case.endings):
        for cat in E.CATEGORIES:
            cc = [x.get("id") for x in case.cards if x.get("kind") == "contradiction" and x.get("proof_category") == cat]
            if len(cc) < 3:
                continue
            bp, _ = eng.solve("best", node_cap=20000, goal=(cc, 3), time_budget=10)
            if bp:
                states.append(eng.replay(bp)[0])
                break
    sol = case.solution
    accusable = [ch.get("id") for ch in case.chars if case.accusable(ch.get("id"))]
    for s in states:
        ccards = [x for x in s.seen if (case.card_by_id.get(x) or {}).get("kind") == "contradiction"]
        triples = list(itertools.combinations(ccards, 3))[:400]
        answers = {slot: [(sol.get(slot) or [""])[0], "__wrong__"] for slot in ("how", "when", "why")}
        for who in accusable:
            for tri in triples:
                for how, when, why in itertools.product(answers["how"], answers["when"], answers["why"]):
                    th = {"who": who, "how": how, "when": when, "why": why, "proof": list(tri)}
                    end, cond = eng.evaluate(th)
                    if end.get("id") not in reached:
                        reached[end.get("id")] = "accuse %s with %s" % (case.short_name(who), "/".join(tri))
    # timeout: just let the clock run
    s = eng.start(record=False)[0]
    for _ in range(2000):
        if s.ending:
            break
        s, _ = eng.step(s, {"type": "WAIT", "minutes": 30}, record=False)
    if s.ending:
        reached.setdefault(s.ending, "let the clock run out")
    for e in case.endings:
        if e.get("id") not in reached:
            errs.append("ending %s (%s) is never reached" % (e.get("id"), e.get("condition")))
    if not any(e.get("condition") == "TIMEOUT" for e in case.endings):
        errs.append("no TIMEOUT ending: running out the clock has nowhere to go")
    for who in accusable:
        th = {"who": who, "how": "", "when": "", "why": "", "proof": []}
        if eng.evaluate(th)[0].get("id") == "END-UNRESOLVED":
            errs.append("accusing %s matches no ending" % who)
    info["reached"] = {k: v for k, v in reached.items() if k != "END-UNRESOLVED"}
    return not errs, errs, info


def _check_facts(case, rx1):
    sol = case.solution
    facts = set()
    for slot in ("how", "when", "why"):
        facts |= {E.norm(x) for x in sol.get(slot) or [] if x}
    facts |= {E.norm(x) for cat in E.CATEGORIES for x in case.proof_cards[cat]}
    killer = case.char_by_id.get(sol.get("who")) or {}
    secret = E.norm((killer.get("secret") or {}).get("summary", ""))
    errs, checked = [], 0
    for st in case.storylets:
        if st.get("mode") != "writer" or not st.get("facts_allowed"):
            continue
        checked += 1
        hits = []
        for f in st["facts_allowed"]:
            nf = E.norm(f)
            if not nf:
                continue
            if any(nf == x or (len(x) >= 6 and x in nf) or (len(nf) >= 12 and nf in x) for x in facts) or \
                    (len(nf) >= 12 and nf in secret):
                hits.append(f)
        if not hits:
            continue
        req = st.get("requires") or {}
        gated = bool(req) and not _act1_reachable(case, st, rx1)
        if not gated:
            errs.append("writer storylet %s may say %s before any gate" % (st.get("id"), hits))
    return not errs, errs, {"writer_storylets_checked": checked}


def _act1_reachable(case, st, rx1):
    return rx1["ok"](st.get("requires")) and st.get("id") in rx1["storylets"]


def _warnings(case, eng, rx, rep):
    for st in case.storylets:
        intents = set(st.get("intents") or E.DEFAULT_STORYLET_INTENTS)
        special = intents <= {"SCHEDULED", "ACCUSE", "FACEOFF", "PRESENT"}
        used = any(st.get("id") in (con.get("result_beat"),) for con in case.contradictions) or \
            any(st.get("id") == sc.get("beat") for sc in case.scheduled) or \
            any(st.get("id") == e.get("beat") for e in case.endings) or \
            st.get("id") == case.solution.get("confession_beat") or \
            any(st.get("id") == o.get("beat") for ch in case.choices for o in ch.get("options") or [])
        if not used and st.get("id") not in rx["storylets"]:
            rep.warnings.append("storylet %s looks unreachable" % st.get("id"))
    for cd in case.cards:
        if cd.get("id") not in rx["cards"]:
            rep.warnings.append("card %s can never be obtained" % cd.get("id"))
    for cl in case.claims:
        if cl.get("id") not in rx["claims"]:
            rep.warnings.append("claim %s is never uttered" % cl.get("id"))
    for sc in case.scheduled:
        if sc.get("at", 0) < case.start:
            rep.warnings.append("scheduled beat %s at %s is before clock.start; it plays at the opening" % (
                sc.get("beat"), sc.get("at")))
        if sc.get("at", 0) > case.deadline:
            rep.warnings.append("scheduled beat %s at %s is after the deadline and never fires" % (
                sc.get("beat"), sc.get("at")))


# ------------------------------------------------------------------ output
def render(rep, case, pack_dir, verbose=False):
    lines = []
    title = case.title if case else os.path.basename(pack_dir)
    lines.append("Linting %s  (%s)" % (title, pack_dir))
    for r in rep.rules:
        lines.append("  %s  %d. %s" % ("PASS" if r["passed"] else "FAIL", r["rule"], r["name"]))
        for d in r["details"]:
            lines.append("        - %s" % d)
        inf = r["info"]
        if r["rule"] == 3 and inf.get("routes"):
            lines.append("        routes: " + ", ".join("%s %d (+%d optional)" % (
                k, v["routes"], v["with_optional"] - v["routes"]) for k, v in inf["routes"].items()))
        if r["rule"] == 7 and "minimal_actions" in inf:
            lines.append("        minimal path: %d actions (%s)" % (inf["minimal_actions"], inf["note"]))
            if not r["passed"] or verbose:
                for i, step in enumerate(inf.get("path", []), 1):
                    lines.append("          %2d. %s" % (i, step))
        if r["rule"] == 9 and "actions" in inf:
            lines.append("        autoplay: %d actions, %d game minutes" % (inf["actions"], inf["game_minutes"]))
        if r["rule"] == 5 and inf.get("reached"):
            lines.append("        reached: " + ", ".join(sorted(inf["reached"])))
    if rep.warnings:
        lines.append("  Warnings (%d):" % len(rep.warnings))
        cap = len(rep.warnings) if verbose else 40
        for w in rep.warnings[:cap]:
            lines.append("    ~ %s" % w)
        if len(rep.warnings) > cap:
            lines.append("    ~ ... %d more" % (len(rep.warnings) - 40))
    lines.append("RESULT: %s" % ("PASS" if rep.passed else "FAIL"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint a case pack (rules 1-9).")
    ap.add_argument("pack")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the shortest path and all warnings")
    ap.add_argument("--stamp", action="store_true", help="write lint.passed/linter_version into casepack.json")
    ap.add_argument("--node-cap", type=int, default=200000, help="search node budget for rules 7 and 9")
    ap.add_argument("--time-budget", type=float, default=12.0, help="seconds per rule-7 search pass")
    a = ap.parse_args(argv)
    rep, case = lint(a.pack, node_cap=a.node_cap, time_budget=a.time_budget)
    if a.json:
        print(json.dumps({"pack": os.path.abspath(a.pack), "passed": rep.passed, "linter_version": LINTER_VERSION,
                          "rules": rep.rules, "warnings": rep.warnings}, indent=2, default=list))
    else:
        print(render(rep, case, os.path.abspath(a.pack), verbose=a.verbose))
    if a.stamp:
        mpath = os.path.join(a.pack, "casepack.json")
        if os.path.exists(mpath):
            m = E.load_json(mpath)
            m.setdefault("lint", {})
            m["lint"]["passed"] = rep.passed
            m["lint"]["linter_version"] = LINTER_VERSION
            with open(mpath, "w", encoding="utf-8") as f:
                json.dump(m, f, indent=2, ensure_ascii=False)
                f.write("\n")
    return 0 if rep.passed else 1


if __name__ == "__main__":
    sys.exit(main())
