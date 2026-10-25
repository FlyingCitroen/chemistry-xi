"""Stages (b) INTERPRET and (c) EXPLAIN. Pure functions; every result at index k uses events[:k] only."""
from __future__ import annotations

from dataclasses import dataclass, replace

import chem_config as C

PASS_TYPES = ("forward_pass", "back_pass")


def secs(e) -> int:
    return (e["minute"] - 1) * 60 + e["second"]


def clock(e) -> str:
    return f"{e['minute']:02d}:{e['second']:02d}"


# ---------------- interpret: statistics ----------------
def score(played) -> dict:
    s = {t: 0 for t in C.TEAMS}
    for e in played:
        if e["event_type"] == "shot" and e.get("goal"):
            s[e["team"]] += 1
    return s


def possession(played) -> dict:
    """Possession proxy: share of passes. Returns whole percentages that sum to 100."""
    n = {t: 0 for t in C.TEAMS}
    for e in played:
        if e["event_type"] in PASS_TYPES:
            n[e["team"]] += 1
    tot = sum(n.values())
    home = round(100 * n[C.TEAMS[0]] / tot) if tot else 50
    return {C.TEAMS[0]: home, C.TEAMS[1]: 100 - home}


def team_stats(played, team) -> dict:
    ps = [e for e in played if e["team"] == team and e["event_type"] in PASS_TYPES]
    sh = [e for e in played if e["team"] == team and e["event_type"] == "shot"]
    tk = [e for e in played if e["team"] == team and e["event_type"] == "tackle"]
    done = sum(e["successful"] for e in ps)
    return {"passes": len(ps), "accuracy": round(100 * done / len(ps)) if ps else None,
            "shots": len(sh), "on_target": sum(e["successful"] for e in sh),
            "goals": sum(bool(e.get("goal")) for e in sh), "xg": round(sum(e["xg"] for e in sh), 2),
            "tackles_won": sum(e["successful"] for e in tk),
            "pressures": sum(1 for e in played if e["team"] == team and e["event_type"] == "pressure")}


def player_stats(played, name) -> dict:
    ps = [e for e in played if e["event_type"] in PASS_TYPES and e["player_from"] == name]
    done = [e for e in ps if e["successful"]]
    sh = [e for e in played if e["event_type"] == "shot" and e["player_from"] == name]
    tk = [e for e in played if e["event_type"] == "tackle" and e["player_from"] == name]
    return {
        "passes": len(ps), "completed": len(done),
        "accuracy": round(100 * len(done) / len(ps)) if ps else None,
        "avg_difficulty": round(sum(e["difficulty"] for e in ps) / len(ps), 2) if ps else None,
        "longest_pass": round(max((e["distance_m"] for e in done), default=0)) or None,
        "top_ball_speed": max((e["ball_speed_kmh"] for e in ps), default=None),
        "shots": len(sh), "goals": sum(bool(e.get("goal")) for e in sh),
        "assists": sum(1 for e in played if e["event_type"] == "shot" and e.get("goal")
                       and e.get("assist_by") == name),
        "xg": round(sum(e["xg"] for e in sh), 2),
        "top_shot_speed": max((e["shot_speed_kmh"] for e in sh), default=None),
        "tackles": len(tk), "tackles_won": sum(e["successful"] for e in tk),
        "pressures": sum(1 for e in played if e["event_type"] == "pressure" and e["player_from"] == name),
    }


def indicators(played, player=None) -> list[dict]:
    """Threshold-triggered indicators (the 'speed / distance indicators' of the brief)."""
    out = []
    for e in played:
        if player and e["player_from"] != player:
            continue
        et, who = e["event_type"], e["player_from"]
        if et == "shot" and e["shot_speed_kmh"] >= C.FAST_SHOT_KMH:
            out.append({"Time": clock(e), "Player": who, "Indicator": "Shot speed",
                        "Value": f"{e['shot_speed_kmh']} km/h"})
        elif et == "forward_pass" and e["successful"] and e["distance_m"] >= C.LONG_PASS_M:
            out.append({"Time": clock(e), "Player": who, "Indicator": "Long pass",
                        "Value": f"{round(e['distance_m'])} m"})
        elif et in PASS_TYPES and e["ball_speed_kmh"] >= C.FAST_PASS_KMH:
            out.append({"Time": clock(e), "Player": who, "Indicator": "Ball speed",
                        "Value": f"{e['ball_speed_kmh']} km/h"})
    return out


# ---------------- explain: game state (control vs chaos, pressure, rhythm) ----------------
@dataclass(frozen=True)
class Tactical:
    label: str       # WARMING_UP | CONTROL | HIGH_PRESS | CHAOS | BALANCED
    team: str
    share_pct: int
    turnovers: int
    pressures: int
    rhythm: str      # fast | steady | slow
    window_min: int
    reason: str


_WARM = Tactical("WARMING_UP", "", 50, 0, 0, "steady", C.TACTICAL_WINDOW_S // 60,
                 "Not enough events yet to read the game.")


def _read(win, k, now) -> Tactical:
    W = C.TACTICAL_WINDOW_S
    if len(win) < C.WARMUP_EVENTS:
        return _WARM
    passes = {t: 0 for t in C.TEAMS}
    press = {t: 0 for t in C.TEAMS}
    turn = 0
    for e in win:
        if e["event_type"] in PASS_TYPES:
            passes[e["team"]] += 1
        elif e["event_type"] == "pressure":
            press[e["team"]] += 1
        elif e["event_type"] == "possession_change":
            turn += 1
    total = sum(passes.values())
    leader = max(passes, key=passes.get) if passes[C.TEAMS[0]] != passes[C.TEAMS[1]] else ""
    share = round(100 * passes[leader] / total) if total and leader else 50
    presser = max(press, key=press.get)
    tempo = len(win) / (max(60, min(now, W)) / 60)
    avg = k / (max(60, now) / 60)
    rhythm = "fast" if tempo >= 1.25 * avg else "slow" if tempo <= 0.75 * avg else "steady"
    wm = W // 60
    if press[presser] >= C.PRESS_MIN:
        return Tactical("HIGH_PRESS", presser, share, turn, press[presser], rhythm, wm,
                        f"{presser} made {press[presser]} pressure actions in the last {wm} minutes.")
    if total >= 6 and leader and share >= round(C.CONTROL_SHARE * 100) and turn <= C.CONTROL_MAX_TURNOVERS:
        return Tactical("CONTROL", leader, share, turn, press[presser], rhythm, wm,
                        f"{leader} had {share}% of the passes in the last {wm} minutes with only "
                        f"{turn} turnovers.")
    if turn >= C.CHAOS_MIN_TURNOVERS:
        return Tactical("CHAOS", "", share, turn, press[presser], rhythm, wm,
                        f"{turn} possession changes in the last {wm} minutes; nobody is settling.")
    return Tactical("BALANCED", "", share, turn, press[presser], rhythm, wm,
                    f"Possession is shared: {share}% of passes for the leader, {turn} turnovers.")


def tactical_timeline(events) -> list[Tactical]:
    out, lo = [_WARM], 0
    for k in range(1, len(events) + 1):
        now = secs(events[k - 1])
        while secs(events[lo]) < now - C.TACTICAL_WINDOW_S:
            lo += 1
        out.append(_read(events[lo:k], k, now))
    return out


# ---------------- explain: key moments ----------------
@dataclass(frozen=True)
class Moment:
    k: int
    time: str
    type: str          # goal | big_chance | fast_shot | long_pass | momentum | link | milestone
    team: str
    players: tuple
    significance: float
    facts: dict
    why_en: str        # the engine's own reason (English); localized text is rendered in i18n
    sec: int
    idx: int = -1

    @property
    def id(self) -> str:
        return f"m{self.k}-{self.type}"


WHY_GOAL = {"opened": "It opens the scoring.", "took_lead": "It puts the scoring team in front.",
            "equalised": "It levels the match.", "extended": "It extends the lead.",
            "pulled_back": "It pulls one back."}


def detect_moments(events, tactical, chem_all=None) -> list[Moment]:
    out, sc, done = [], {t: 0 for t in C.TEAMS}, {}
    last_emit, last_state, seen_state = -10**9, ("WARMING_UP", ""), {}
    for k, e in enumerate(events, 1):
        et, t, now = e["event_type"], clock(e), secs(e)
        if et == "shot":
            team = e["team"]
            opp = C.OPPONENT if team == C.TEAM else C.TEAM
            if e.get("goal"):
                a, b = sc[team], sc[opp]
                code = ("opened" if a + b == 0 else "took_lead" if a == b else "equalised" if a + 1 == b
                        else "extended" if a > b else "pulled_back")
                sc[team] += 1
                f = {"scorer": e["player_from"], "score_home": sc[C.TEAM], "score_away": sc[C.OPPONENT],
                     "code": code, "xg": e["xg"], "speed": e["shot_speed_kmh"]}
                players = (e["player_from"],)
                if e.get("assist_by"):
                    f["assist"] = e["assist_by"]
                    players += (e["assist_by"],)
                    tl = (chem_all or {}).get((e["assist_by"], e["player_from"]))
                    if tl and tl[k].buff in (C.SUPER, C.POTENTIAL):
                        f["link_buff"] = tl[k].buff
                out.append(Moment(k, t, "goal", team, players,
                                  1.0 + (0.2 if code in ("took_lead", "equalised") else 0.0), f,
                                  WHY_GOAL[code], now))
            elif e["xg"] >= C.BIG_CHANCE_XG:
                out.append(Moment(k, t, "big_chance", team, (e["player_from"],), 0.6 + e["xg"],
                                  {"shooter": e["player_from"], "outcome": e["outcome"], "xg": e["xg"],
                                   "speed": e["shot_speed_kmh"]},
                                  f"A high-quality chance (xG {e['xg']}).", now))
            elif e["shot_speed_kmh"] >= C.FAST_SHOT_KMH:
                out.append(Moment(k, t, "fast_shot", team, (e["player_from"],), 0.35,
                                  {"shooter": e["player_from"], "speed": e["shot_speed_kmh"],
                                   "threshold": C.FAST_SHOT_KMH},
                                  "A hard strike above the speed threshold.", now))
        if et == "forward_pass" and e["successful"] and e["distance_m"] >= C.LONG_PASS_M:
            out.append(Moment(k, t, "long_pass", e["team"], (e["player_from"], e["player_to"]),
                              0.3 + (0.1 if e["chance_created"] else 0.0),
                              {"passer": e["player_from"], "receiver": e["player_to"],
                               "distance": round(e["distance_m"]), "threshold": C.LONG_PASS_M},
                              "A successful long pass above the distance threshold.", now))
        if et in ("forward_pass", "back_pass") and e["successful"]:
            who = e["player_from"]
            done[who] = done.get(who, 0) + 1
            if done[who] == C.MILESTONE_PASSES:
                out.append(Moment(k, t, "milestone", e["team"], (who,), 0.25,
                                  {"player": who, "count": done[who]},
                                  f"{who} reached {done[who]} completed passes.", now))
        cur = tactical[k]
        state = (cur.label, cur.team)
        if cur.label == "BALANCED":
            last_state = ("BALANCED", "")          # remember it silently so a later CONTROL re-emits
        elif (cur.label != "WARMING_UP" and state != last_state and now - last_emit >= 90
              and now - seen_state.get(state, -10**9) >= 600):
            out.append(Moment(k, t, "momentum", cur.team, (), 0.5,
                              {"state": cur.label, "share_pct": cur.share_pct, "turnovers": cur.turnovers,
                               "pressures": cur.pressures, "window_min": cur.window_min,
                               "rhythm": cur.rhythm}, cur.reason, now))
            last_emit, last_state, seen_state[state] = now, state, now
    for (a, b), tl in (chem_all or {}).items():
        for i in range(1, len(tl)):
            if tl[i].buff != tl[i - 1].buff and tl[i].buff in (C.SUPER, C.COOLING):
                ev = events[i - 1]
                out.append(Moment(i, clock(ev), "link", C.ROSTER[a][0], (a, b),
                                  0.8 if tl[i].buff == C.SUPER else 0.5,
                                  {"pair": f"{a} → {b}", "to": tl[i].buff,
                                   "smoothed_pct": round(100 * tl[i].stats.smoothed, 1),
                                   "n": tl[i].stats.attempts}, tl[i].reason, secs(ev)))
    out.sort(key=lambda m: m.k)
    return [replace(m, idx=i) for i, m in enumerate(out)]
