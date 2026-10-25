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

st.set_page_config(page_title="Chemistry XI", page_icon="⚽", layout="wide")
LABELS = [f"{a} → {b}" for a, b in C.PAIRS]
ICON = {"goal": "⚽", "big_chance": "🎯", "fast_shot": "💥", "long_pass": "📐", "momentum": "🌊",
        "link": "🔗", "milestone": "🏅"}
GAME_ICON = {"WARMING_UP": "⏳", "CONTROL": "🎯", "HIGH_PRESS": "🔥", "CHAOS": "🌪️", "BALANCED": "⚖️"}


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


@st.cache_data(show_spinner="Narrator + Verifier working…")
def cached_moment(idx, persona, lang, detail):
    return agents.narrate_moment(PIPE.moments[idx], persona, lang, detail)


@st.cache_data(show_spinner="Recap agent working…")
def cached_match_recap(k, pkey):
    p = Profile.from_key(pkey)
    return agents.recap_match(events, k, PIPE.personalize(k, p), p)


@st.cache_data(show_spinner="Agents working…")
def cached_narration(pair, k, persona):
    states = ALL[pair]
    t = engine.transitions(states, events, k)[-1]
    f = agents.build_finding(f"{pair[0]} → {pair[1]}", t, states[k])
    return agents.narrate(f, persona)


@st.cache_data(show_spinner="Recap agent working…")
def cached_chem_recap(k, persona):
    return agents.recap(events, ALL, k, persona)


def build_profile() -> Profile:
    ss = st.session_state
    club = ss.get("club", "(none)")
    player = ss.get("player", "(none)")
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


def show_trace(result, label="Agent trace (Analyst → Narrator → Verifier)"):
    st.caption(f"Mode: **{result.mode}**")
    with st.expander(label):
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
    st.header("Viewer profile")
    st.radio("Viewing mode", ["Casual fan", "Analyst"], key="mode", horizontal=True)
    st.selectbox("Language", list(i18n.LANGS), format_func=lambda c: i18n.LANGS[c], key="lang")
    st.selectbox("Favourite club", ["(none)"] + C.TEAMS, key="club")
    st.selectbox("Favourite player", ["(none)"] + C.ALL_PLAYERS, key="player")
    st.toggle("Player focus mode (only this player's moments)", key="player_focus")
    st.selectbox("Metric focus", ["auto", "shot_speed", "pass_quality", "pressure", "chemistry"], key="metric")
    st.selectbox("Narration voice", list(agents.PERSONAS), key="persona")
    st.caption(llm.status())
    if llm.LAST_ERROR:
        st.caption(f"Last LLM error: {llm.LAST_ERROR[:160]}")
    with st.expander("Chemistry lens"):
        st.selectbox("Player pair (forward passes)", LABELS, key="pair_choice")
    with st.expander("Rules used (chem_config.py)"):
        st.json({"team_baseline": C.TEAM_BASELINE, **C.R.__dict__})
    with st.expander("Method"):
        st.markdown(
            "- **Pipeline:** ingest → interpret → explain → render → personalize.\n"
            "- Link score: Beta-smoothed success rate with ≈80% credible band.\n"
            "- Game state: last 5 match minutes (possession share, turnovers, pressure, tempo).\n"
            "- Every state uses only events played so far.\n"
            "- The LLM never decides: a Verifier rejects any number, label or player not in the engine output.")

profile = build_profile()
pair = current_pair()
pair_label = st.session_state.get("pair_choice", LABELS[0])
k = st.session_state.k
view = PIPE.interpret(k)
home, away = C.TEAMS
sc, tac = view["score"], view["tactical"]
detail = profile.mode

# ---------- header ----------
st.title("⚽ Chemistry XI")
st.caption("Explainable match intelligence · synthetic Northbridge FC v Eastport United")
c1, c2, c3, c4 = st.columns(4)
c1.button("▶ Next event", key="btn_next", on_click=advance, args=(1,), disabled=k >= N, width="stretch")
c2.button("⏩ Next 10", key="btn_next10", on_click=advance, args=(10,), disabled=k >= N, width="stretch")
c3.button("⏭ Next key moment", key="btn_moment", on_click=next_moment, disabled=k >= N, width="stretch")
c4.button("↺ Reset", key="btn_reset", on_click=reset, disabled=k == 0, width="stretch")

clock = insight.clock(events[k - 1]) if k else "00:00"
t1, t2, t3, t4 = st.columns(4)
t1.metric("MATCH CLOCK", clock)
t2.metric("EVENTS PLAYED", f"{k} / {N}")
t3.metric(f"{home} v {away}", f"{sc[home]} – {sc[away]}")
t4.metric("GAME STATE", f"{GAME_ICON[tac.label]} {tac.label}" + (f" · {tac.team}" if tac.team else ""))
st.progress(k / N if N else 0)

tab_mc, tab_player, tab_chem, tab_recap = st.tabs(
    ["📺 Match centre", "🧍 Player focus", "🔗 Chemistry", "📝 Recap"])

# ================= MATCH CENTRE =================
with tab_mc:
    left, right = st.columns([3, 2])
    with left:
        st.subheader("Your personalised feed")
        st.caption(f"{profile.mode} · {i18n.LANGS[profile.lang]}"
                   + (f" · ❤ {profile.club}" if profile.club else "")
                   + (f" · ⭐ {profile.player}" + (" (focus)" if profile.player_focus else "")
                      if profile.player else "")
                   + (f" · metric: {profile.metric}" if profile.metric != "auto" else ""))
        chosen = PIPE.personalize(k, profile)
        if chosen:
            for m in reversed(chosen[-6:]):
                res = cached_moment(m.idx, profile.persona, profile.lang, detail)
                with st.container(border=True):
                    st.markdown(f"{ICON[m.type]} {res.text}")
                    st.caption(f"{m.type} · relevance {relevance(m, profile):.2f} · {res.mode}")
            show_trace(cached_moment(chosen[-1].idx, profile.persona, profile.lang, detail))
        else:
            st.info("Nothing matches your profile yet. Click Next event or Next key moment.")

        st.subheader("On-screen overlay (stage d)")
        if chosen:
            latest = chosen[-1]
            res = cached_moment(latest.idx, profile.persona, profile.lang, detail)
            ov = overlays.overlay(latest, profile.lang, detail, res.text)
            overlay_card(ov)
            with st.expander("Machine-readable overlay JSON"):
                st.json(ov)
        feed = PIPE.render(k, profile)
        st.download_button("⬇ Download overlay timeline (JSON)", overlays.to_json(feed),
                           file_name="overlays.json", mime="application/json",
                           disabled=not feed, key="btn_download")
    with right:
        st.subheader("Why the game feels like this")
        st.markdown(f"**{GAME_ICON[tac.label]} {tac.label}**" + (f" · {tac.team}" if tac.team else ""))
        st.write(tac.reason)
        st.caption(f"Rhythm: {tac.rhythm} · window: last {tac.window_min} match minutes")
        poss = view["possession"]
        st.markdown(f"**Possession (share of passes)** — {home} {poss[home]}% · {away} {poss[away]}%")
        st.progress(poss[home] / 100)
        ts = view["teams"]
        rows = [("Passes", "passes"), ("Pass accuracy %", "accuracy"), ("Shots", "shots"),
                ("On target", "on_target"), ("xG", "xg"), ("Tackles won", "tackles_won"),
                ("Pressures", "pressures")]
        st.dataframe([{"Stat": lab, home: ts[home][key], away: ts[away][key]} for lab, key in rows],
                     width="stretch", hide_index=True)
        st.subheader("Recent events")
        if k:
            def describe(e):
                a = e["player_from"] + (f" → {e['player_to']}" if e.get("player_to") else "")
                return {"Time": insight.clock(e), "Team": e["team"], "Event": a, "Type": e["event_type"],
                        "Result": "✓" if e["successful"] else "✗"}
            st.dataframe([describe(e) for e in reversed(events[max(0, k - 8):k])],
                         width="stretch", hide_index=True)
        else:
            st.info("Click Next event to start the match.")

# ================= PLAYER FOCUS =================
with tab_player:
    default = C.ALL_PLAYERS.index(profile.player) if profile.player else 1
    who = st.selectbox("Player", C.ALL_PLAYERS, index=default, key="focus_player")
    ps = insight.player_stats(events[:k], who)
    num, pos = C.ROSTER[who][1], C.ROSTER[who][2]
    st.subheader(f"#{num} {who} · {pos} · {C.ROSTER[who][0]}")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Passes completed", f"{ps['completed']}/{ps['passes']}")
    a2.metric("Accuracy", f"{ps['accuracy']}%" if ps["accuracy"] is not None else "—")
    a3.metric("Avg pass difficulty", ps["avg_difficulty"] if ps["avg_difficulty"] is not None else "—")
    a4.metric("Longest completed pass", f"{ps['longest_pass']} m" if ps["longest_pass"] else "—")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Top ball speed", f"{ps['top_ball_speed']} km/h" if ps["top_ball_speed"] else "—")
    b2.metric("Shots / goals / assists", f"{ps['shots']} / {ps['goals']} / {ps['assists']}")
    b3.metric("xG", ps["xg"])
    b4.metric("Tackles won", f"{ps['tackles_won']}/{ps['tackles']}")
    st.markdown("**Threshold indicators** (long pass ≥ "
                f"{C.LONG_PASS_M} m, shot ≥ {C.FAST_SHOT_KMH} km/h, ball ≥ {C.FAST_PASS_KMH} km/h)")
    ind = insight.indicators(events[:k], who)
    st.dataframe(ind, width="stretch", hide_index=True) if ind else st.caption("None triggered yet.")
    st.markdown("**Moments involving this player**")
    mine = [m for m in PIPE.explain(k) if who in m.players]
    if mine:
        for m in reversed(mine[-5:]):
            res = cached_moment(m.idx, profile.persona, profile.lang, detail)
            st.markdown(f"{ICON[m.type]} {res.text}")
    else:
        st.caption("No key moments for this player yet.")

# ================= CHEMISTRY =================
with tab_chem:
    state = ALL[pair][k]
    stats, states = state.stats, ALL[pair]
    sub_live, sub_scan = st.tabs(["Live link analysis", "Team scan"])
    with sub_live:
        st.button("⏭ Next link change", key="btn_link", on_click=next_link_change, disabled=k >= N)
        left, right = st.columns([3, 2])
        with left:
            st.subheader(pair_label)
            st.metric("Buff", f"{C.BUFF_STYLE[state.buff][0]} {state.buff}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"Passes (last {C.R.window})", stats.attempts)
            m2.metric("Successful", stats.successes)
            m3.metric("Progressive", stats.progressive)
            m4.metric("Chances", stats.chances)
            m5, m6 = st.columns(2)
            m5.metric("Observed rate", f"{stats.raw:.1%}" if stats.raw is not None else "—")
            m6.metric("Smoothed rate", f"{stats.smoothed:.1%}" if stats.smoothed is not None else "—",
                      delta=f"{(stats.smoothed - C.TEAM_BASELINE) * 100:+.1f} pp vs baseline"
                      if stats.smoothed is not None else None)
            st.subheader("Uncertainty over time")
            rows = [{"Pass #": s.pair_n, "Smoothed": s.stats.smoothed, "Low": s.stats.lo,
                     "High": s.stats.hi, "Buff": s.buff}
                    for prev, s in zip(states[:k], states[1:k + 1]) if s.pair_n != prev.pair_n]
            if rows:
                df = pd.DataFrame(rows)
                total = max(states[-1].pair_n, 2)
                x = alt.X("Pass #:Q", scale=alt.Scale(domain=[1, total]), axis=alt.Axis(tickMinStep=1))
                ys = alt.Scale(domain=[0, 1])
                band = alt.Chart(df).mark_area(opacity=0.18).encode(
                    x=x, y=alt.Y("Low:Q", scale=ys, axis=alt.Axis(format="%", title="Success rate")), y2="High:Q")
                line = alt.Chart(df).mark_line(color="#555").encode(x=x, y=alt.Y("Smoothed:Q", scale=ys))
                pts = alt.Chart(df).mark_circle(size=90).encode(
                    x=x, y=alt.Y("Smoothed:Q", scale=ys),
                    color=alt.Color("Buff:N", scale=alt.Scale(
                        domain=list(C.BUFF_STYLE), range=[v[1] for v in C.BUFF_STYLE.values()])),
                    tooltip=["Pass #", alt.Tooltip("Smoothed:Q", format=".1%"), "Buff"])
                rule = lambda v, dash: alt.Chart(pd.DataFrame({"y": [v]})).mark_rule(
                    strokeDash=dash, color="#888").encode(y=alt.Y("y:Q", scale=ys))
                st.altair_chart(alt.layer(band, line, pts, rule(C.TEAM_BASELINE, [4, 4]),
                                          rule(engine.super_threshold(), [1, 3])).properties(height=260),
                                width="stretch")
                st.caption(f"Dashed = baseline {C.TEAM_BASELINE:.0%}; dotted = Super Link threshold "
                           f"{engine.super_threshold():.1%}; band = ≈80% credible interval.")
            else:
                st.info("No pair passes yet.")
            st.subheader("Why this Buff?")
            st.write(state.reason)
            if state.buff != C.SUPER and state.unmet and stats.attempts:
                st.markdown("**Why not SUPER_LINK yet?**")
                for u in state.unmet:
                    st.markdown(f"- {u}")
            st.subheader("Evidence")
            if stats.evidence:
                st.dataframe([{"Time": insight.clock(by_id[i]),
                               "Result": "✅ Success" if by_id[i]["successful"] else "❌ Failed",
                               "Progressive": "Yes" if by_id[i]["progressive"] else "",
                               "Chance created": "Yes" if by_id[i]["chance_created"] else "",
                               "Distance (m)": by_id[i]["distance_m"],
                               "Difficulty": by_id[i]["difficulty"]}
                              for i in reversed(stats.evidence)], width="stretch", hide_index=True)
        with right:
            st.subheader("🎙 Link narration")
            trans = engine.transitions(states, events, k)
            if trans:
                res = cached_narration(pair, k, profile.persona)
                st.write(res.text)
                show_trace(res)
                st.dataframe(list(reversed(trans)), width="stretch", hide_index=True)
            else:
                st.caption("The narrator speaks when a Buff changes.")
    with sub_scan:
        st.caption("Every directed pair is scanned with the same rules, ranked by the **lower** credible "
                   "bound. Pairs with too few passes sit on a watchlist, however good they look.")
        fmt = {c: st.column_config.NumberColumn(format="percent") for c in ("Smoothed", "Low (80%)", "High (80%)")}
        rows_of = lambda rs: [{"Pair": r["Pair"], "Buff": f"{C.BUFF_STYLE[r['Buff']][0]} {r['Buff']}",
                               "Passes so far": r["Passes"], "In window": r["Window"],
                               "Smoothed": r["Smoothed"], "Low (80%)": r["Low"], "High (80%)": r["High"]}
                              for r in rs]
        ranked = engine.leaderboard(ALL, k, C.R.super_min_attempts)
        watch = [r for r in engine.leaderboard(ALL, k) if r["Pair"] not in {x["Pair"] for x in ranked}]
        st.markdown(f"**Ranked** (≥ {C.R.super_min_attempts} passes in window)")
        if ranked:
            st.dataframe(rows_of(ranked), width="stretch", hide_index=True, column_config=fmt)
        else:
            st.info(f"No pair has {C.R.super_min_attempts} passes in the window yet.")
        if watch:
            st.markdown("**Watchlist** — too little data to rank")
            st.dataframe(rows_of(watch), width="stretch", hide_index=True, column_config=fmt)

# ================= RECAP =================
with tab_recap:
    st.subheader("Automated match recap")
    st.caption("Built only from verified key moments and engine statistics, tailored to your profile "
               "(mode, language, club, player, metric).")
    st.button("Generate recap at current minute", key="btn_recap", on_click=request_recap, disabled=k == 0)
    req = st.session_state.get("recap_req")
    if req:
        rk, pkey = req
        res = cached_match_recap(rk, pkey)
        st.markdown(f"**Recap · {insight.clock(events[rk - 1])} · {i18n.LANGS[Profile.from_key(pkey).lang]}**")
        st.write(res.text)
        show_trace(res, "Agent trace (Analyst → Narrator → Verifier)")
        with st.expander("Chemistry recap (link moments across all pairs)"):
            cres, moments, top = cached_chem_recap(rk, Profile.from_key(pkey).persona)
            st.write(cres.text)

st.divider()
st.caption("Synthetic data and illustrative rules. Possession is a pass-share proxy. Buffs are analytical "
           "states, not real player abilities; a high pass-success rate does not prove chemistry.")
