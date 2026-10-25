from streamlit.testing.v1 import AppTest


def test_app_smoke():
    at = AppTest.from_file("app.py", default_timeout=120).run()
    assert not at.exception
    for _ in range(6):
        at.button(key="btn_moment").click().run()
        assert not at.exception
    at.radio(key="mode").set_value("Analyst").run()
    at.selectbox(key="lang").select("zh").run()
    at.selectbox(key="club").select("Eastport United").run()
    at.selectbox(key="player").select("Jamie").run()
    at.toggle(key="player_focus").set_value(True).run()
    at.selectbox(key="metric").select("chemistry").run()
    at.selectbox(key="persona").select("Commentator").run()
    assert not at.exception
    at.button(key="btn_reset").click().run()
    at.selectbox(key="pair_choice").select("Taylor → Jamie").run()
    at.button(key="btn_link").click().run()
    at.button(key="btn_reset").click().run()
    at.button(key="btn_next10").click().run()
    at.button(key="btn_recap").click().run()
    assert not at.exception
    at.button(key="btn_reset").click().run()
    assert not at.exception
