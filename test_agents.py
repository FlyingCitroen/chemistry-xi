import chem_config as C
import chem_engine as engine
import agents
from generate_data import generate

EVENTS = generate()
ALL = engine.scan_all(EVENTS)
PAIR = ("Alex", "Jamie")


def all_findings():
    for pair, tl in ALL.items():
        for t in engine.transitions(tl, EVENTS, len(EVENTS)):
            yield agents.build_finding(f"{pair[0]} → {pair[1]}", t, tl[t["Event #"]])


def super_finding():
    tl = ALL[PAIR]
    i = next(i for i, s in enumerate(tl) if s.buff == C.SUPER)
    t = engine.transitions(tl, EVENTS, i)[-1]
    return agents.build_finding("Alex → Jamie", t, tl[i])


def test_every_template_passes_verifier():
    n = 0
    for f in all_findings():
        for p in agents.PERSONAS:
            assert agents.verify(agents.narration_template(f, p), f.facts()) == [], (f, p)
            n += 1
    assert n > 30  # the whole league of pairs was exercised


def test_verifier_rejects_invented_number():
    f = super_finding()
    assert agents.verify("Alex → Jamie hit 99.9% success!", f.facts())


def test_verifier_rejects_unknown_label_and_player():
    f = super_finding()
    assert agents.verify("The link became ULTRA_LINK.", f.facts())
    assert agents.verify("Morgan and Riley were brilliant.", f.facts())


def test_orchestrator_retries_then_accepts():
    f, calls = super_finding(), []
    good = agents.narration_template(f, "Fan")

    def stub(system, user):
        calls.append(user)
        return "Invented 91.7% stat." if len(calls) == 1 else good

    res = agents.narrate(f, "Fan", llm_fn=stub)
    assert res.mode == "llm" and res.text == good and len(calls) == 2
    assert "REJECTED" in calls[1]  # feedback reached the narrator


def test_orchestrator_falls_back_after_repeated_bad_drafts():
    f = super_finding()
    res = agents.narrate(f, "Coach", llm_fn=lambda s, u: "Totally made up 12345.")
    assert res.mode == "fallback"
    assert agents.verify(res.text, f.facts()) == []


def test_template_mode_without_llm():
    res = agents.narrate(super_finding(), "Commentator", llm_fn=lambda s, u: None)
    assert res.mode == "template"


def test_recap_is_grounded():
    res, moments, top = agents.recap(EVENTS, ALL, len(EVENTS), "Coach", llm_fn=lambda s, u: None)
    assert any(m["to"] == C.SUPER for m in moments)
    assert top and top[0]["Low"] >= top[-1]["Low"]
    assert any("Alex → Jamie" in line for line in [res.text])


def test_leaderboard_penalises_small_samples():
    board = {r["label"]: r for r in engine.leaderboard(ALL, len(EVENTS))}
    tj = board.get("Taylor → Jamie")
    assert tj is None or tj["Low"] < 0.6  # 2 perfect passes never look elite


def test_moment_narration_retries_and_falls_back():
    import i18n
    from pipeline import MatchPipeline
    P = MatchPipeline(EVENTS)
    m = next(x for x in P.moments if x.type == "goal")
    good = i18n.render(m, "zh", "Analyst")
    calls = []

    def stub(system, user):
        calls.append(system)
        return "Jamie 在第 99 分钟进球！" if len(calls) == 1 else good

    res = agents.narrate_moment(m, "Fan", "zh", "Analyst", llm_fn=stub)
    assert res.mode == "llm" and res.text == good and "中文" in calls[0]
    bad = agents.narrate_moment(m, "Fan", "es", "Casual fan", llm_fn=lambda s, u: "Marca Riley a los 99'.")
    assert bad.mode == "fallback" and agents.verify(bad.text, i18n.facts_text(m)) == []


def test_verifier_catches_unknown_player_inside_cjk_text():
    f = super_finding()
    assert agents.verify("进球的是Sam。", f.facts())


def test_match_recap_is_grounded_in_every_language():
    import i18n
    from personalize import Profile
    from pipeline import MatchPipeline
    P = MatchPipeline(EVENTS)
    for lang in i18n.LANGS:
        prof = Profile(mode="Analyst", lang=lang)
        res = agents.recap_match(EVENTS, len(EVENTS), P.personalize(len(EVENTS), prof), prof,
                                 llm_fn=lambda s, u: None)
        assert res.mode == "template" and "3-1" in res.text


def test_link_narration_in_every_language_is_verified():
    import i18n
    for f in all_findings():
        for lang in i18n.LANGS:
            for persona in agents.PERSONAS:
                assert agents.verify(agents.narration_template(f, persona, lang), f.facts()) == [], (lang, f)
