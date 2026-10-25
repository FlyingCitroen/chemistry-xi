"""Stage (d) RENDER: timed, machine-readable overlay messages that a graphics engine can place over a live
feed. Schema: see README ('Overlay schema')."""
from __future__ import annotations

import json

import i18n

SCHEMA = "chemistry-xi.overlay/1"
DURATION = {"goal": 9, "big_chance": 6, "fast_shot": 5, "long_pass": 5, "momentum": 7, "link": 7, "milestone": 5}
STYLE = {"goal": "celebration", "big_chance": "alert", "fast_shot": "stat", "long_pass": "stat",
         "momentum": "tactical", "link": "insight", "milestone": "stat"}


def chips(m, lang):
    c, f = i18n.CHIP[lang], m.facts
    if m.type == "goal":
        return [(c["score"], f"{f['score_home']}-{f['score_away']}"), (c["xg"], f["xg"]),
                (c["speed"], f"{f['speed']} km/h")]
    if m.type == "big_chance":
        return [(c["xg"], f["xg"]), (c["speed"], f"{f['speed']} km/h")]
    if m.type == "fast_shot":
        return [(c["speed"], f"{f['speed']} km/h")]
    if m.type == "long_pass":
        return [(c["distance"], f"{f['distance']} m")]
    if m.type == "momentum":
        return [(c["possession"], f"{f['share_pct']}%"), (c["turnovers"], f["turnovers"]),
                (c["pressures"], f["pressures"])]
    if m.type == "link":
        return [(c["rate"], f"{f['smoothed_pct']}%"), (c["passes"], f["n"])]
    return [(c["passes"], f["count"])]


def overlay(m, lang: str, detail: str, text: str | None = None) -> dict:
    parts, sep = i18n.render_parts(m, lang, detail), i18n.T[lang]["sep"]
    return {
        "schema": SCHEMA, "id": m.id, "type": m.type, "style": STYLE[m.type], "lang": lang,
        "match_clock": m.time, "start_s": m.sec, "text": text or sep.join(parts), "duration_s": DURATION[m.type],
        "priority": round(m.significance, 2), "team": m.team or None, "players": list(m.players),
        "lower_third": {"headline": parts[0], "subline": sep.join(parts[1:])},
        "chips": [{"label": a, "value": b} for a, b in chips(m, lang)],
    }


def to_json(items: list[dict]) -> str:
    return json.dumps({"schema": SCHEMA, "overlays": items}, ensure_ascii=False, indent=2)
