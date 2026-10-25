import chem_config as C
import chem_engine as engine
from generate_data import generate, validate

PAIRS = {"aj": ("Alex", "Jamie"), "am": ("Alex", "Morgan"), "tj": ("Taylor", "Jamie")}
EVENTS = generate()


def test_demo_story_holds():
    validate(EVENTS)


def test_no_future_peeking():
    for pair in PAIRS.values():
        full = engine.build_timeline(EVENTS, pair)
        for k in (0, 1, 37, 120, 200, len(EVENTS)):
            assert engine.build_timeline(EVENTS[:k], pair)[k] == full[k]


def test_small_sample_never_escalates():
    tl = engine.build_timeline(EVENTS, PAIRS["tj"])
    assert {s.buff for s in tl} == {C.INSUFFICIENT}


def test_cooldown_lasts_configured_length():
    tl = engine.build_timeline(EVENTS, PAIRS["aj"])
    cooling = sum(1 for a, b in zip(tl, tl[1:]) if b.buff == C.COOLING and b.pair_n != a.pair_n)
    assert cooling == C.R.cooldown_events


def test_smoothing_shrinks_toward_baseline():
    st = engine.window_stats([{"successful": True, "progressive": False,
                               "chance_created": False, "event_id": i} for i in range(3)])
    assert st.raw == 1.0 and C.TEAM_BASELINE < st.smoothed < 1.0
    assert st.hi - st.lo > 0.1  # wide interval on a tiny sample


def test_every_transition_is_recorded_when_jumping():
    tl = engine.build_timeline(EVENTS, PAIRS["aj"])
    seen = [s.buff for s in tl]
    t = engine.transitions(tl, EVENTS, len(EVENTS))
    assert len(t) == sum(1 for a, b in zip(seen, seen[1:]) if a != b)
