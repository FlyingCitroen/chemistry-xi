import html
import json

import altair as alt
import pandas as pd
import streamlit as st

import agents
import chem_config as C
import chem_engine as engine
import i18n
import insight
import llm
import overlays
from generate_data import write_events
from personalize import Profile, relevance
from pipeline import MatchPipeline
from ui_text import U as _U

st.set_page_config(page_title="Chemistry XI", page_icon="⚽", layout="wide")
LANG = st.session_state.get("lang", "en")          # the language chosen on the previous run
LABELS = [f"{a} → {b}" for a, b in C.PAIRS]
ICON = {"goal": "⚽", "big_chance": "🎯", "fast_shot": "💥", "long_pass": "📐", "momentum": "🌊",
        "link": "🔗", "milestone": "🏅"}
GAME_ICON = {"WARMING_UP": "⏳", "CONTROL": "🎯", "HIGH_PRESS": "🔥", "CHAOS": "🌪️", "BALANCED": "⚖️"}


def U(key, **kw):
    return _U(st.session_state.get("lang", "en"), key, **kw)


# ---------- data & pipeline ----------
@st.cache_resource
def get_pipeline():
    def load():
        if not C.DATA_FILE.exists() or not C.META_FILE.exists():
            write_events()
        with C.DATA_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    events = load()
    if not any(e["event_type"] == "shot" for e in events):  # stale file from an older version
        write_events()
        events = load()
    return MatchPipeline(events)


PIPE = get_pipeline()
events, ALL, N = PIPE.events, PIPE.chem, len(PIPE.events)
by_id = {e["event_id"]: e for e in events}


@st.cache_data(show_spinner="…")
def cached_moment(idx, persona, lang, detail):
    return agents.narrate_moment(PIPE.moments[idx], persona, lang, detail)


@st.cache_data(show_spinner="…")
def cached_match_recap(k, pkey):
    p = Profile.from_key(pkey)
    return agents.recap_match(events, k, PIPE.personalize(k, p), p)


@st.cache_data(show_spinner="…")
def cached_narration(pair, k, persona, lang):
    states = ALL[pair]
    t = engine.transitions(states, events, k)[-1]
    f = agents.build_finding(f"{pair[0]} → {pair[1]}", t, states[k])
    return agents.narrate(f, persona, lang=lang)


def build_profile() -> Profile:
    ss = st.session_state
    club, player = ss.get("club", "(none)"), ss.get("player", "(none)")
    player = None if player == "(none)" else player
    return Profile(mode=ss.get("mode", "Casual fan"), lang=ss.get("lang", "en"),
                   club=None if club == "(none)" else club, player=player,
                   player_focus=bool(ss.get("player_focus")) and player is not None,
                   metric=ss.get("metric", "auto"), persona=ss.get("persona", "Fan"))


def current_pair():
    return C.PAIRS[LABELS.index(st.session_state.get("pair_choice", LABELS[0]))]


# ---------- callbacks ----------
def advance(n):
    st.session_state.k = min(st.session_state.k + n, N)


def reset():
    st.session_state.k = 0
    st.session_state.pop("recap_req", None)


def next_moment():
    k = st.session_state.k
    nxt = [m.k for m in PIPE.personalize(N, build_profile()) if m.k > k]
    st.session_state.k = nxt[0] if nxt else N


def next_link_change():
    states, k = ALL[current_pair()], st.session_state.k
    st.session_state.k = next((i for i in range(k + 1, len(states)) if states[i].buff != states[k].buff),
                              len(states) - 1)


def request_recap():
    st.session_state.recap_req = (st.session_state.k, build_profile().key())


def show_trace(result):
    st.caption(U("mode_caption", m=U("mode_" + {"llm": "llm", "template": "template", "fallback": "fallback"}[result.mode])))
    with st.expander(U("trace_title")):
        st.caption(U("trace_note"))
        for s in result.trace:
            st.markdown(f"{'✅' if s.ok else '❌'} **{s.agent}** · {s.action}")
            st.caption(s.detail)


def overlay_card(ov):
    chips = "".join(f"<span style='background:#1f3b6e;border-radius:12px;padding:2px 10px;margin-right:6px;"
                    f"font-size:0.85rem'>{html.escape(c['label'])} <b>{html.escape(str(c['value']))}</b></span>"
                    for c in ov["chips"])
    lt = ov["lower_third"]
    st.markdown(
        "<div style='background:#0b1d3a;color:#fff;border-left:6px solid #f2b134;border-radius:6px;"
        "padding:12px 16px'>"
        f"<div style='font-size:1.05rem;font-weight:700'>{html.escape(lt['headline'])}</div>"
        f"<div style='opacity:.85;margin:4px 0 8px'>{html.escape(lt['subline'])}</div>{chips}</div>",
        unsafe_allow_html=True)


st.session_state.setdefault("k", 0)

# ---------- sidebar: the viewer profile ----------
with st.sidebar:
    st.header(U("profile"))
    st.radio(U("mode_label"), ["Casual fan", "Analyst"], key="mode", horizontal=True,
             format_func=lambda v: U("mode_casual" if v == "Casual fan" else "mode_analyst"))
    st.selectbox("Language / 语言 / 言語 / Idioma", list(i18n.LANGS), format_func=lambda c: i18n.LANGS[c], key="lang")
    st.selectbox(U("club_label"), ["(none)"] + C.TEAMS, key="club",
                 format_func=lambda v: U("none") if v == "(none)" else v)
    st.selectbox(U("player_label"), ["(none)"] + C.ALL_PLAYERS, key="player",
                 format_func=lambda v: U("none") if v == "(none)" else v)
    st.toggle(U("focus_label"), key="player_focus")
    st.selectbox(U("metric_label"), ["auto", "shot_speed", "pass_quality", "pressure", "chemistry"], key="metric",
                 format_func=lambda v: U("metric_" + v))
    st.selectbox(U("voice_label"), list(agents.PERSONAS), key="persona", format_func=lambda v: U("voice_" + v))
    st.caption(llm.status())
    if llm.LAST_ERROR:
        st.caption(f"Last LLM error: {llm.LAST_ERROR[:160]}")
    with st.expander(U("chem_lens")):
        st.selectbox(U("pair_label"), LABELS, key="pair_choice")
    with st.expander(U("rules_title")):
        st.json({"team_baseline": C.TEAM_BASELINE, **C.R.__dict__})
    with st.expander(U("method_title")):
        st.markdown(U("method_body"))

profile = build_profile()
LANG = profile.lang
pair = current_pair()
pair_label = st.session_state.get("pair_choice", LABELS[0])
k = st.session_state.k
view = PIPE.interpret(k)
home, away = C.TEAMS
sc, tac = view["score"], view["tactical"]
detail = profile.mode

# ---------- header ----------
st.title("⚽ Chemistry XI")
st.caption(U("app_caption"))
c1, c2, c3, c4 = st.columns(4)
c1.button(U("btn_next"), key="btn_next", on_click=advance, args=(1,), disabled=k >= N, width="stretch")
c2.button(U("btn_next10"), key="btn_next10", on_click=advance, args=(10,), disabled=k >= N, width="stretch")
c3.button(U("btn_moment"), key="btn_moment", on_click=next_moment, disabled=k >= N, width="stretch")
c4.button(U("btn_reset"), key="btn_reset", on_click=reset, disabled=k == 0, width="stretch")

clock = insight.clock(events[k - 1]) if k else "00:00"
t1, t2, t3, t4 = st.columns(4)
t1.metric(U("m_clock"), clock)
t2.metric(U("m_events"), f"{k} / {N}")
t3.metric(f"{home} v {away}", f"{sc[home]} – {sc[away]}")
t4.metric(U("m_state"), f"{GAME_ICON[tac.label]} {U('game_' + tac.label)}" + (f" · {tac.team}" if tac.team else ""))
st.progress(k / N if N else 0)

tab_mc, tab_player, tab_chem, tab_recap = st.tabs([U("tab_mc"), U("tab_player"), U("tab_chem"), U("tab_recap")])

# ================= MATCH CENTRE =================
with tab_mc:
    left, right = st.columns([3, 2])
    with left:
        st.subheader(U("feed_title"))
        st.caption(f"{U('mode_casual' if profile.mode == 'Casual fan' else 'mode_analyst')} · {i18n.LANGS[profile.lang]}"
                   + (f" · ❤ {profile.club}" if profile.club else "")
                   + (f" · ⭐ {profile.player}" if profile.player else "")
                   + (f" · {U('metric_' + profile.metric)}" if profile.metric != "auto" else ""))
        chosen = PIPE.personalize(k, profile)
        if chosen:
            for m in reversed(chosen[-6:]):
                res = cached_moment(m.idx, profile.persona, profile.lang, detail)
                with st.container(border=True):
                    st.markdown(f"{ICON[m.type]} {res.text}")
                    st.caption(f"{U('type_' + m.type)} · {U('relevance')} {relevance(m, profile):.2f}")
            show_trace(cached_moment(chosen[-1].idx, profile.persona, profile.lang, detail))
        else:
            st.info(U("feed_empty"))

        st.subheader(U("overlay_title"))
        if chosen:
            latest = chosen[-1]
            res = cached_moment(latest.idx, profile.persona, profile.lang, detail)
            ov = overlays.overlay(latest, profile.lang, detail, res.text)
            overlay_card(ov)
            with st.expander(U("overlay_json")):
                st.json(ov)
        feed = PIPE.render(k, profile)
        st.download_button(U("download"), overlays.to_json(feed), file_name="overlays.json",
                           mime="application/json", disabled=not feed, key="btn_download")
    with right:
        st.subheader(U("why_game"))
        st.markdown(f"**{GAME_ICON[tac.label]} {U('game_' + tac.label)}**" + (f" · {tac.team}" if tac.team else ""))
        st.write(i18n.tactical_text(tac, profile.lang))
        st.caption(U("rhythm_line", r=U("rhythm_" + tac.rhythm), w=tac.window_min))
        poss = view["possession"]
        st.markdown(f"**{U('possession_title')}** — {home} {poss[home]}% · {away} {poss[away]}%")
        st.progress(poss[home] / 100)
        ts = view["teams"]
        rows = [("st_passes", "passes"), ("st_accuracy", "accuracy"), ("st_shots", "shots"),
                ("st_on_target", "on_target"), ("st_xg", "xg"), ("st_tackles_won", "tackles_won"),
                ("st_pressures", "pressures")]
        st.dataframe([{U("stat_col"): U(lab), home: ts[home][key], away: ts[away][key]} for lab, key in rows],
                     width="stretch", hide_index=True)
        st.subheader(U("recent_title"))
        if k:
            def describe(e):
                a = e["player_from"] + (f" → {e['player_to']}" if e.get("player_to") else "")
                return {U("col_time"): insight.clock(e), U("col_team"): e["team"], U("col_event"): a,
                        U("col_type"): e["event_type"], "✓": "✓" if e["successful"] else "✗"}
            st.dataframe([describe(e) for e in reversed(events[max(0, k - 8):k])],
                         width="stretch", hide_index=True)
        else:
            st.info(U("recent_hint"))

# ================= PLAYER FOCUS =================
with tab_player:
    default = C.ALL_PLAYERS.index(profile.player) if profile.player else 1
    who = st.selectbox(U("p_select"), C.ALL_PLAYERS, index=default, key="focus_player")
    ps = insight.player_stats(events[:k], who)
    st.subheader(f"#{C.ROSTER[who][1]} {who} · {C.ROSTER[who][2]} · {C.ROSTER[who][0]}")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric(U("p_completed"), f"{ps['completed']}/{ps['passes']}")
    a2.metric(U("p_accuracy"), f"{ps['accuracy']}%" if ps["accuracy"] is not None else "—")
    a3.metric(U("p_difficulty"), ps["avg_difficulty"] if ps["avg_difficulty"] is not None else "—")
    a4.metric(U("p_longest"), f"{ps['longest_pass']} m" if ps["longest_pass"] else "—")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric(U("p_ballspeed"), f"{ps['top_ball_speed']} km/h" if ps["top_ball_speed"] else "—")
    b2.metric(U("p_sga"), f"{ps['shots']} / {ps['goals']} / {ps['assists']}")
    b3.metric(U("p_xg"), ps["xg"])
    b4.metric(U("p_tackles"), f"{ps['tackles_won']}/{ps['tackles']}")
    st.markdown(U("ind_title", a=C.LONG_PASS_M, b=C.FAST_SHOT_KMH, c=C.FAST_PASS_KMH))
    names = {"Shot speed": "ind_shot", "Long pass": "ind_long", "Ball speed": "ind_ball"}
    ind = insight.indicators(events[:k], who)
    if ind:
        st.dataframe([{U("col_time"): r["Time"], U("col_player"): r["Player"],
                       U("col_indicator"): U(names[r["Indicator"]]), U("col_value"): r["Value"]} for r in ind],
                     width="stretch", hide_index=True)
    else:
        st.caption(U("ind_none"))
    st.markdown(U("p_moments"))
    mine = [m for m in PIPE.explain(k) if who in m.players]
    if mine:
        for m in reversed(mine[-5:]):
            st.markdown(f"{ICON[m.type]} {cached_moment(m.idx, profile.persona, profile.lang, detail).text}")
    else:
        st.caption(U("p_none"))

# ================= CHEMISTRY =================
with tab_chem:
    states = ALL[pair]
    state = states[k]
    stats = state.stats
    sub_live, sub_scan = st.tabs([U("sub_live"), U("sub_scan")])
    with sub_live:
        st.button(U("btn_link"), key="btn_link", on_click=next_link_change, disabled=k >= N)
        left, right = st.columns([3, 2])
        with left:
            st.subheader(pair_label)
            st.metric(U("buff_label"), f"{C.BUFF_STYLE[state.buff][0]} {state.buff}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(U("c_passes", n=C.R.window), stats.attempts)
            m2.metric(U("c_ok"), stats.successes)
            m3.metric(U("c_prog"), stats.progressive)
            m4.metric(U("c_chances"), stats.chances)
            m5, m6 = st.columns(2)
            m5.metric(U("c_observed"), f"{stats.raw:.1%}" if stats.raw is not None else "—")
            m6.metric(U("c_smoothed"), f"{stats.smoothed:.1%}" if stats.smoothed is not None else "—",
                      delta=U("c_vs_base", d=f"{(stats.smoothed - C.TEAM_BASELINE) * 100:+.1f}")
                      if stats.smoothed is not None else None)
            st.subheader(U("unc_title"))
            rows = [{"n": s.pair_n, "Smoothed": s.stats.smoothed, "Low": s.stats.lo, "High": s.stats.hi,
                     "Buff": s.buff} for prev, s in zip(states[:k], states[1:k + 1]) if s.pair_n != prev.pair_n]
            if rows:
                df = pd.DataFrame(rows)
                total = max(states[-1].pair_n, 2)
                x = alt.X("n:Q", title=U("axis_pass"), scale=alt.Scale(domain=[1, total]),
                          axis=alt.Axis(tickMinStep=1))
                ys = alt.Scale(domain=[0, 1])
                band = alt.Chart(df).mark_area(opacity=0.18).encode(
                    x=x, y=alt.Y("Low:Q", scale=ys, axis=alt.Axis(format="%", title=U("axis_rate"))), y2="High:Q")
                line = alt.Chart(df).mark_line(color="#555").encode(x=x, y=alt.Y("Smoothed:Q", scale=ys))
                pts = alt.Chart(df).mark_circle(size=90).encode(
                    x=x, y=alt.Y("Smoothed:Q", scale=ys),
                    color=alt.Color("Buff:N", legend=None, scale=alt.Scale(
                        domain=list(C.BUFF_STYLE), range=[v[1] for v in C.BUFF_STYLE.values()])),
                    tooltip=["n", alt.Tooltip("Smoothed:Q", format=".1%"), "Buff"])
                rule = lambda v, dash: alt.Chart(pd.DataFrame({"y": [v]})).mark_rule(
                    strokeDash=dash, color="#888").encode(y=alt.Y("y:Q", scale=ys))
                st.altair_chart(alt.layer(band, line, pts, rule(C.TEAM_BASELINE, [4, 4]),
                                          rule(engine.super_threshold(), [1, 3])).properties(height=260),
                                width="stretch")
                st.caption(U("chart_caption", base=f"{C.TEAM_BASELINE:.0%}", thr=f"{engine.super_threshold():.1%}"))
            else:
                st.info(U("no_pairs"))
            st.subheader(U("why_buff"))
            st.write(i18n.chem_reason(state, profile.lang))
            if state.buff != C.SUPER and stats.attempts:
                st.markdown(U("why_not"))
                for u in i18n.chem_unmet(state, profile.lang):
                    st.markdown(f"- {u}")
            st.subheader(U("evidence_title"))
            if stats.evidence:
                st.dataframe([{U("col_time"): insight.clock(by_id[i]),
                               U("col_result"): U("ev_ok") if by_id[i]["successful"] else U("ev_fail"),
                               U("ev_prog"): U("yes") if by_id[i]["progressive"] else "",
                               U("ev_chance"): U("yes") if by_id[i]["chance_created"] else "",
                               U("ev_dist"): by_id[i]["distance_m"], U("ev_diff"): by_id[i]["difficulty"]}
                              for i in reversed(stats.evidence)], width="stretch", hide_index=True)
        with right:
            st.subheader(U("link_narr"))
            trans = engine.transitions(states, events, k)
            if trans:
                res = cached_narration(pair, k, profile.persona, profile.lang)
                st.write(res.text)
                show_trace(res)
                st.dataframe([{U("col_time"): t["Time"], U("col_from"): t["From"], U("col_to"): t["To"],
                               U("col_smoothed"): t["Smoothed"],
                               U("col_reason"): i18n.chem_reason(states[t["Event #"]], profile.lang)}
                              for t in reversed(trans)], width="stretch", hide_index=True)
            else:
                st.caption(U("link_wait"))
    with sub_scan:
        st.caption(U("scan_caption"))
        fmt = {U(c): st.column_config.NumberColumn(format="percent") for c in ("sc_smoothed", "sc_low", "sc_high")}
        rows_of = lambda rs: [{U("sc_pair"): r["Pair"], U("sc_buff"): f"{C.BUFF_STYLE[r['Buff']][0]} {r['Buff']}",
                               U("sc_total"): r["Passes"], U("sc_window"): r["Window"],
                               U("sc_smoothed"): r["Smoothed"], U("sc_low"): r["Low"], U("sc_high"): r["High"]}
                              for r in rs]
        ranked = engine.leaderboard(ALL, k, C.R.super_min_attempts)
        watch = [r for r in engine.leaderboard(ALL, k) if r["Pair"] not in {x["Pair"] for x in ranked}]
        st.markdown(U("ranked_title", n=C.R.super_min_attempts))
        if ranked:
            st.dataframe(rows_of(ranked), width="stretch", hide_index=True, column_config=fmt)
        else:
            st.info(U("ranked_none", n=C.R.super_min_attempts))
        if watch:
            st.markdown(U("watch_title"))
            st.dataframe(rows_of(watch), width="stretch", hide_index=True, column_config=fmt)

# ================= RECAP =================
with tab_recap:
    st.subheader(U("recap_title"))
    st.caption(U("recap_caption"))
    st.button(U("btn_recap"), key="btn_recap", on_click=request_recap, disabled=k == 0)
    req = st.session_state.get("recap_req")
    if req:
        rk, pkey = req
        res = cached_match_recap(rk, pkey)
        st.markdown(f"**{U('recap_header', clock=insight.clock(events[rk - 1]), language=i18n.LANGS[Profile.from_key(pkey).lang])}**")
        st.write(res.text)
        show_trace(res)

st.divider()
st.caption(U("footer"))
