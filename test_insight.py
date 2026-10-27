import chem_config as C
import chem_engine as engine
import i18n
import insight
import overlays
from generate_data import generate, validate, meta
from personalize import Profile, relevance, select
from pipeline import MatchPipeline

EVENTS = generate()
P = MatchPipeline(EVENTS)


def strip(m):  # compare moments ignoring their position in the list
    return (m.k, m.time, m.type, m.team, m.players, m.significance, m.facts, m.why_en, m.sec)


def test_dataset_is_rich_and_synthetic():
    types = {e["event_type"] for e in EVENTS}
    assert {"forward_pass", "back_pass", "shot", "tackle", "possession_change", "pressure"} <= types
    assert all(e["data_source"] == "synthetic" for e in EVENTS)
    assert all({"distance_m", "ball_speed_kmh", "difficulty"} <= e.keys()
               for e in EVENTS if e["event_type"] in insight.PASS_TYPES)
    assert meta()["home"] == C.TEAM and len(meta()["roster"]) == 16
    validate(EVENTS)


def test_score_and_hero_goal():
    assert insight.score(EVENTS) == {C.TEAM: 3, C.OPPONENT: 1}
    goal = next(m for m in P.moments if m.type == "goal" and m.facts.get("assist") == "Alex")
    assert goal.facts["link_buff"] == C.SUPER  # the goal came from the pair our engine flagged


def test_game_states_are_all_reachable():
    labels = {(s.label, s.team) for s in P.tactical}
    assert ("CONTROL", C.TEAM) in labels and ("HIGH_PRESS", C.OPPONENT) in labels
    assert any(l == "CHAOS" for l, _ in labels)


def test_no_future_peeking_in_moments_and_states():
    for k in (30, 120, 200, 301):
        sub = events_k = EVENTS[:k]
        tl = insight.tactical_timeline(sub)
        assert tl == P.tactical[:k + 1]
        moments = insight.detect_moments(sub, tl, engine.scan_all(sub))
        assert [strip(m) for m in moments] == [strip(m) for m in P.moments if m.k <= k]


def test_possession_sums_to_100_and_stats_consistent():
    p = insight.possession(EVENTS)
    assert sum(p.values()) == 100
    ps = insight.player_stats(EVENTS, "Jamie")
    assert ps["goals"] >= 1 and ps["completed"] <= ps["passes"]


def test_every_moment_renders_in_every_language_and_passes_verifier():
    import agents
    for m in P.moments:
        for lang in i18n.LANGS:
            for detail in ("Casual fan", "Analyst"):
                text = i18n.render(m, lang, detail)
                assert agents.verify(text, i18n.facts_text(m)) == [], (m.type, lang, detail)


def test_languages_actually_differ():
    goal = next(m for m in P.moments if m.type == "goal")
    texts = {l: i18n.render(goal, l) for l in i18n.LANGS}
    assert len(set(texts.values())) == 4
    assert "进球" in texts["zh"] and "ゴール" in texts["ja"] and "GOL" in texts["es"]


def test_analyst_gets_more_detail_than_casual_fan():
    goal = next(m for m in P.moments if m.type == "goal")
    assert len(i18n.render(goal, "en", "Analyst")) > len(i18n.render(goal, "en", "Casual fan"))


def test_overlay_schema_is_machine_readable():
    import json
    prof = Profile(mode="Analyst", lang="ja")
    feed = P.render(len(EVENTS), prof)
    assert feed
    data = json.loads(overlays.to_json(feed))
    for o in data["overlays"]:
        assert {"schema", "id", "type", "start_s", "duration_s", "lang", "lower_third", "chips"} <= o.keys()
        assert o["lang"] == "ja" and o["duration_s"] > 0
    starts = [o["start_s"] for o in data["overlays"]]
    assert starts == sorted(starts)


def test_personalisation_changes_what_each_viewer_sees():
    casual, analyst = Profile(mode="Casual fan"), Profile(mode="Analyst")
    assert len(select(P.moments, analyst)) > len(select(P.moments, casual))
    fav = Profile(mode="Casual fan", club=C.OPPONENT)
    assert len([m for m in select(P.moments, fav) if m.team == C.OPPONENT]) >= \
        len([m for m in select(P.moments, casual) if m.team == C.OPPONENT])
    focus = Profile(mode="Analyst", player="Jamie", player_focus=True)
    chosen = select(P.moments, focus)
    assert chosen and all("Jamie" in m.players for m in chosen)
    m = next(m for m in P.moments if m.type == "fast_shot")
    assert relevance(m, Profile(metric="shot_speed")) > relevance(m, Profile())


def test_pipeline_is_fast_enough_for_live_play():
    import time
    t = time.time()
    MatchPipeline(EVENTS)
    assert time.time() - t < 5  # whole match (all pairs, states, moments) in a few seconds, far less per event


def test_ui_has_the_same_keys_in_every_language():
    import ui_text
    base = set(ui_text.UI["en"])
    for lang, d in ui_text.UI.items():
        assert set(d) == base, (lang, base ^ set(d))
    assert set(i18n.LANGS) == set(ui_text.UI) == set(i18n.T) == set(i18n.CH) == set(i18n.CHIP)


def test_every_ui_key_used_by_the_app_exists():
    import re
    import ui_text
    used = set(re.findall(r'U\("([a-z_0-9]+)"', open("app.py", encoding="utf-8").read()))
    dynamic = {"mode_", "metric_", "voice_", "type_", "game_", "rhythm_"}
    missing = [k for k in used if k not in ui_text.UI["en"] and k not in dynamic]
    assert not missing, missing
    for prefix, vals in {"metric_": ["auto", "shot_speed", "pass_quality", "pressure", "chemistry"],
                         "voice_": ["Fan", "Commentator", "Coach", "Analyst"],
                         "type_": ["goal", "big_chance", "fast_shot", "long_pass", "momentum", "link", "milestone"],
                         "game_": ["WARMING_UP", "CONTROL", "HIGH_PRESS", "CHAOS", "BALANCED"],
                         "rhythm_": ["fast", "steady", "slow"]}.items():
        assert all(prefix + v in ui_text.UI["en"] for v in vals)


def test_chemistry_texts_are_localised_and_consistent():
    tl = P.chem[("Alex", "Jamie")]
    for lang in i18n.LANGS:
        reasons = {i18n.chem_reason(s, lang) for s in tl}
        assert len(reasons) > 3 and all(reasons)
    # the localised 'what is missing' list has the same length as the engine's own list
    for s in [s for s in tl if s.stats.attempts]:
        assert len(i18n.chem_unmet(s, "zh")) == len(s.unmet)
    # English re-derivation matches the engine's original reasons exactly
    played = [s for s in tl if s.stats.attempts]
    assert all(i18n.chem_reason(s, "en") == s.reason for s in played)


def test_tactical_text_localised():
    for lang in i18n.LANGS:
        assert all(i18n.tactical_text(t, lang) for t in P.tactical[::25])
