from streamlit.testing.v1 import AppTest

CHOICES = {"mode": "Analyst", "club": "Eastport United", "player": "Jamie", "metric": "chemistry",
           "persona": "Commentator"}


def fresh():
    at = AppTest.from_file("app.py", default_timeout=120).run()
    assert not at.exception
    return at


def test_app_flow_in_english():
    at = fresh()
    for _ in range(4):
        at.button(key="btn_moment").click().run()
        assert not at.exception
    at.button(key="btn_reset").click().run()
    at.session_state["pair_choice"] = "Taylor → Jamie"
    at.run()
    at.button(key="btn_link").click().run()
    at.button(key="btn_reset").click().run()
    at.button(key="btn_next10").click().run()
    at.button(key="btn_recap").click().run()
    assert not at.exception
    at.button(key="btn_reset").click().run()
    assert not at.exception


def test_every_language_renders_every_screen():
    """One fresh session per language/mode: all tabs, recap included, at a late point in the match.
    (Fresh sessions because AppTest cannot re-run radios whose labels differ from their values.)"""
    from personalize import Profile
    for lang in ("en", "zh", "ja", "es"):
        for mode in ("Casual fan", "Analyst"):
            at = AppTest.from_file("app.py", default_timeout=120)
            at.session_state["lang"] = lang
            at.session_state["mode"] = mode
            at.session_state["k"] = 260
            for key, v in CHOICES.items():
                if key != "mode":
                    at.session_state[key] = v
            at.session_state["player_focus"] = mode == "Analyst"
            prof = Profile(mode=mode, lang=lang, club="Eastport United", player="Jamie",
                           player_focus=mode == "Analyst", metric="chemistry", persona="Commentator")
            at.session_state["recap_req"] = (260, prof.key())
            at.run()
            assert not at.exception, (lang, mode, at.exception)


def test_switching_language_keeps_the_viewer_profile():
    at = fresh()
    for k, v in CHOICES.items():
        at.session_state[k] = v
    at.run()
    at.session_state["lang"] = "zh"
    at.run()
    assert not at.exception
    for k, v in CHOICES.items():
        assert at.session_state[k] == v, k


def test_visible_text_is_localised():
    at = fresh()
    at.button(key="btn_moment").click().run()
    at.session_state["lang"] = "zh"
    at.run()
    labels = [b.label for b in at.button]
    assert any("下一个" in l for l in labels) and not any("Next event" in l for l in labels)
    assert any("比赛中心" in t.label for t in at.tabs)
