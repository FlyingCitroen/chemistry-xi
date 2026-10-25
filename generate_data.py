"""Synthetic, football-realistic match for two fictional clubs. Fixed seed, fully reproducible.

Event types: forward_pass, back_pass, shot, tackle, possession_change, pressure.
Chemistry pairs and the key storylines (a hot link, a goal it creates, a control spell, a chaotic
spell, a pressing spell) are scripted so the demo is controllable; everything else is random.
Pass codes: F=failed, S=success, P=progressive success, C=progressive success that created a chance.
Coordinates are in metres on a 105x68 pitch, always in the team's attacking direction."""
import json
import math
import random

import chem_config as C
import chem_engine as engine
import insight

SCRIPTS = {
    ("Alex", "Jamie"): "S F S F S S P S P C S P S S F F S F F S F F".split(),   # heats up, then cools
    ("Alex", "Morgan"): "S F S P F S F S P S F S P F S F S P".split(),           # ordinary pair
    ("Taylor", "Jamie"): "S S".split(),                                          # tiny sample
}
DECODE = {"F": (False, False, False), "S": (True, False, False),
          "P": (True, True, False), "C": (True, True, True)}
N_BG_PASSES = 240
# (outcome, x, y) - None means random. The hero goal (Alex -> Jamie) is added separately.
SHOTS = {
    C.TEAM: [("saved", None, None), ("off", 96, 30), ("goal", 92, 36), ("blocked", None, None),
             ("saved", None, None), ("off", None, None), ("goal", None, None),
             ("saved", None, None), ("off", None, None)],
    C.OPPONENT: [("saved", None, None), ("goal", 95, 33), ("off", None, None), ("off", None, None),
                 ("blocked", None, None), ("saved", None, None), ("off", None, None),
                 ("saved", None, None)],
}
ATTACKERS = {C.TEAM: ["Alex", "Jamie", "Taylor", "Morgan"], C.OPPONENT: ["Sam", "Quinn", "Blake", "Reese"]}
CHAOS_SPELL = (2400, 2700, 6)                 # seconds window, number of possession changes
PRESS_SPELL = (3300, 3600, C.OPPONENT, 7)     # window, pressing team, number of pressure events


def p_north(t):  # Northbridge dominate 20-35', Eastport dominate 55-65'
    return 0.8 if 1200 <= t < 2100 else 0.3 if 3300 <= t < 3900 else 0.5


def _base(t, team, etype, frm, to=None, **extra):
    e = {"minute": t // 60 + 1, "second": t % 60, "team": team, "player_from": frm, "player_to": to,
         "event_type": etype, "successful": False, "progressive": False, "chance_created": False,
         "data_source": "synthetic"}
    e.update(extra)
    return e


def _geometry(rng, forward, prog, chance):
    if forward:
        dx = rng.uniform(15, 35) if prog else rng.uniform(3, 14.9)
        x0 = rng.uniform(80 - dx, 104 - dx) if chance else rng.uniform(5, 100 - dx)
        x1 = x0 + dx
    else:
        dx = -rng.uniform(3, 25)
        x0 = rng.uniform(25, 100)
        x1 = x0 + dx
    y0 = rng.uniform(8, 60)
    y1 = min(68.0, max(0.0, y0 + rng.gauss(0, 8)))
    return x0, y0, x1, y1


def _pass(rng, t, team, frm, to, etype, ok, prog, chance):
    x0, y0, x1, y1 = _geometry(rng, etype == "forward_pass", prog, chance)
    dist = math.hypot(x1 - x0, y1 - y0)
    pressured = rng.random() < 0.3
    diff = min(1.0, 0.12 + dist / 70 + (0.2 if pressured else 0) + (0.12 if x1 > 80 else 0))
    speed = min(110, max(25, 28 + dist * 1.3 + rng.gauss(0, 6)))
    return _base(t, team, etype, frm, to, successful=bool(ok), progressive=bool(prog),
                 chance_created=bool(chance), x0=round(x0, 1), y0=round(y0, 1), x1=round(x1, 1),
                 y1=round(y1, 1), distance_m=round(dist, 1), ball_speed_kmh=round(speed),
                 difficulty=round(diff, 2), under_pressure=pressured)


def _shot(rng, t, team, shooter, outcome, x=None, y=None, speed=None, assist=None):
    x = rng.uniform(78, 100) if x is None else x
    y = min(68.0, max(0.0, rng.gauss(34, 10))) if y is None else y
    dist = math.hypot(105 - x, 34 - y)
    xg = round(min(0.8, 1.1 * math.exp(-dist / 9)), 2)
    return _base(t, team, "shot", shooter, None, successful=outcome in ("goal", "saved"),
                 x=round(x, 1), y=round(y, 1), distance_m=round(dist, 1), xg=xg, outcome=outcome,
                 goal=outcome == "goal", shot_speed_kmh=int(speed or rng.uniform(62, 118)),
                 assist_by=assist)


def _roster(team):
    return [n for n, v in C.ROSTER.items() if v[0] == team]


def generate(seed: int = 42):
    rng = random.Random(seed)
    ev, hero_t = [], None
    for _ in range(N_BG_PASSES):
        t = rng.randrange(5400)
        team = C.TEAM if rng.random() < p_north(t) else C.OPPONENT
        while True:  # scripted pairs are excluded so their sample sizes stay controlled
            a, b = rng.sample(_roster(team), 2)
            if (a, b) not in SCRIPTS:
                break
        fwd = rng.random() < 0.7
        ok = rng.random() < (0.65 if fwd else 0.88)
        prog = fwd and ok and rng.random() < 0.4
        chance = prog and rng.random() < 0.2
        ev.append(_pass(rng, t, team, a, b, "forward_pass" if fwd else "back_pass", ok, prog, chance))
    for pair, script in SCRIPTS.items():
        times = sorted(rng.sample(range(5400), len(script)))
        for t, code in zip(times, script):
            ev.append(_pass(rng, t, C.ROSTER[pair[0]][0], *pair, "forward_pass", *DECODE[code]))
            if pair == ("Alex", "Jamie") and code == "C":
                hero_t = t
    ev.append(_shot(rng, min(5399, hero_t + 7), C.TEAM, "Jamie", "goal", 93, 35, 108, assist="Alex"))
    for team, shots in SHOTS.items():
        for (outcome, x, y), t in zip(shots, sorted(rng.sample(range(5400), len(shots)))):
            ev.append(_shot(rng, t, team, rng.choice(ATTACKERS[team]), outcome, x, y))
    for _ in range(36):
        team = rng.choice(C.TEAMS)
        ev.append(_base(rng.randrange(5400), team, "tackle", rng.choice(_roster(team)),
                        successful=rng.random() < 0.55, x=round(rng.uniform(10, 95), 1)))
    for _ in range(20):
        team = rng.choice(C.TEAMS)
        ev.append(_base(rng.randrange(5400), team, "possession_change", rng.choice(_roster(team)),
                        cause=rng.choice(["interception", "tackle", "loose_ball"])))
    lo, hi, n = CHAOS_SPELL
    for i in range(n):
        team = C.TEAMS[i % 2]
        ev.append(_base(rng.randrange(lo, hi), team, "possession_change", rng.choice(_roster(team)),
                        cause=rng.choice(["interception", "tackle", "loose_ball"])))
    for _ in range(30):
        team = rng.choice(C.TEAMS)
        ev.append(_base(rng.randrange(5400), team, "pressure", rng.choice(_roster(team)),
                        intensity=rng.randint(1, 3)))
    lo, hi, team, n = PRESS_SPELL
    for _ in range(n):
        ev.append(_base(rng.randrange(lo, hi), team, "pressure", rng.choice(_roster(team)),
                        intensity=rng.randint(2, 3)))
    ev.sort(key=lambda e: (e["minute"], e["second"]))
    for i, e in enumerate(ev, 1):
        e["event_id"] = i
    return ev


def meta(seed: int = 42):
    return {"competition": "Synthetic League (fictional)", "season": "2026/27 (synthetic)",
            "venue": "Synthetic Park", "home": C.TEAM, "away": C.OPPONENT, "duration_min": 90,
            "seed": seed, "data_source": "synthetic",
            "roster": {n: {"team": v[0], "number": v[1], "position": v[2]} for n, v in C.ROSTER.items()}}


def validate(events):
    """Fail loudly if the demo data does not tell the intended story."""
    seq = {p: [s.buff for s in engine.build_timeline(events, p)] for p in SCRIPTS}
    aj, am, tj = (seq[p] for p in [("Alex", "Jamie"), ("Alex", "Morgan"), ("Taylor", "Jamie")])
    assert C.SUPER in aj and C.COOLING in aj, "Alex→Jamie must reach SUPER_LINK and cool down"
    assert C.SUPER not in am, "Alex→Morgan must stay ordinary"
    assert set(tj) == {C.INSUFFICIENT}, "Taylor→Jamie must stay INSUFFICIENT_EVIDENCE"
    sc = insight.score(events)
    assert sc[C.TEAM] == 3 and sc[C.OPPONENT] == 1, f"unexpected score {sc}"
    assert any(e.get("assist_by") == "Alex" and e["goal"] for e in events), "hero goal missing"
    seen = {(s.label, s.team) for s in insight.tactical_timeline(events)}
    assert ("CONTROL", C.TEAM) in seen, "Northbridge control spell missing"
    assert ("HIGH_PRESS", C.OPPONENT) in seen, "Eastport pressing spell missing"
    assert any(l == "CHAOS" for l, _ in seen), "chaotic spell missing"


def write_events(path=C.DATA_FILE, seed: int = 42):
    events = generate(seed)
    validate(events)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    with open(C.META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta(seed), f, ensure_ascii=False, indent=2)
    return events


if __name__ == "__main__":
    from collections import Counter
    ev = write_events()
    print(f"Generated {len(ev)} synthetic events -> {C.DATA_FILE.name} (+ {C.META_FILE.name})")
    print("Event types:", dict(Counter(e["event_type"] for e in ev)))
    print("Final score:", insight.score(ev))
    for p in SCRIPTS:
        tl = engine.build_timeline(ev, p)
        path = [tl[0].buff] + [b.buff for a, b in zip(tl, tl[1:]) if a.buff != b.buff]
        print(f"{p[0]}→{p[1]}: {tl[-1].pair_n} passes | " + " > ".join(path[1:] or path))
