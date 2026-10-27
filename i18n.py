"""Deterministic multi-language storytelling (en / zh / ja / es). Every template only uses values from
the moment's facts, so the result is always verifiable. The LLM path rewrites these under the same checks."""
from __future__ import annotations

LANGS = {"en": "English", "zh": "中文", "ja": "日本語", "es": "Español"}

T = {
    "en": {
        "sep": " ",
        "goal_head": "{t} GOAL! {scorer} scores for {team}.", "goal_assist": "Set up by {assist}.",
        "why_opened": "It opens the scoring.", "why_took_lead": "It puts {team} in front.",
        "why_equalised": "It levels the match.", "why_extended": "It extends the lead.",
        "why_pulled_back": "It pulls one back.",
        "goal_link": "The {assist} → {scorer} link was {link_buff} when it happened.",
        "goal_stat": "Score {score_home}-{score_away}; xG {xg}; shot speed {speed} km/h.",
        "big_head": "{t} Big chance for {shooter} ({team}): {outcome}.",
        "big_why": "A high-quality chance, with an xG of {xg}.", "big_stat": "Shot speed {speed} km/h.",
        "outcome_saved": "saved", "outcome_off": "off target", "outcome_blocked": "blocked",
        "fast_head": "{t} {shooter} ({team}) hits a {speed} km/h shot.",
        "fast_why": "That is above the {threshold} km/h speed threshold.",
        "long_head": "{t} {passer} finds {receiver} with a {distance} m pass.",
        "long_why": "A successful long pass, above the {threshold} m threshold.",
        "mom_CONTROL_head": "{t} {team} take control.",
        "mom_CONTROL_why": "They have {share_pct}% of the passes in the last {window_min} minutes with only {turnovers} turnover(s).",
        "mom_HIGH_PRESS_head": "{t} {team} press high.",
        "mom_HIGH_PRESS_why": "{pressures} pressure actions in the last {window_min} minutes.",
        "mom_CHAOS_head": "{t} The match turns chaotic.",
        "mom_CHAOS_why": "{turnovers} possession changes in the last {window_min} minutes, and the busiest side has only {share_pct}% of the passes.",
        "mom_BALANCED_head": "{t} The match settles down.",
        "mom_BALANCED_why": "Possession is shared: {share_pct}% of the passes for the leader and {turnovers} turnover(s) in the last {window_min} minutes.",
        "rhythm_fast": "fast", "rhythm_steady": "steady", "rhythm_slow": "slow", "tempo": "Tempo: {rhythm}.",
        "link_head": "{t} Link alert: {pair} is now {to}.",
        "link_SUPER_LINK_why": "Smoothed success rate of {smoothed_pct}% over the last {n} passes, above the baseline.",
        "link_COOLING_DOWN_why": "It no longer meets the Super Link criteria after {n} passes in the window.",
        "milestone_head": "{t} {player} completes pass number {count}.",
        "milestone_why": "It shows how involved {player} is in the build-up.",
        "recap_open": "Match recap at {clock}: {home} {hs}-{as_} {away}.", "recap_lead": "Key moments:",
        "recap_empty": "No key moments yet.",
        "recap_poss": "Possession by passes: {home} {home_pct}%, {away} {away_pct}%.",
    },
    "zh": {
        "sep": "",
        "goal_head": "{t} 进球！{team}的{scorer}破门。", "goal_assist": "由{assist}助攻。",
        "why_opened": "这是本场比赛的首个进球。", "why_took_lead": "{team}由此取得领先。",
        "why_equalised": "比分被扳平。", "why_extended": "领先优势被扩大。", "why_pulled_back": "球队追回一球。",
        "goal_link": "当时{assist} → {scorer}的连线状态为{link_buff}。",
        "goal_stat": "比分 {score_home}-{score_away}；xG {xg}；射门速度 {speed} 公里/小时。",
        "big_head": "{t} {team}的{shooter}获得绝佳机会：{outcome}。",
        "big_why": "这是一次高质量机会，xG为{xg}。", "big_stat": "射门速度 {speed} 公里/小时。",
        "outcome_saved": "被扑出", "outcome_off": "射偏", "outcome_blocked": "被封堵",
        "fast_head": "{t} {team}的{shooter}打出时速{speed}公里的射门。",
        "fast_why": "超过了{threshold}公里/小时的速度阈值。",
        "long_head": "{t} {passer}一脚{distance}米的传球找到了{receiver}。",
        "long_why": "这是一次成功的长传，超过{threshold}米的阈值。",
        "mom_CONTROL_head": "{t} {team}掌控了比赛。",
        "mom_CONTROL_why": "最近{window_min}分钟内他们占据{share_pct}%的传球，仅有{turnovers}次丢失球权。",
        "mom_HIGH_PRESS_head": "{t} {team}开始高位逼抢。",
        "mom_HIGH_PRESS_why": "最近{window_min}分钟内有{pressures}次施压。",
        "mom_CHAOS_head": "{t} 比赛变得混乱。",
        "mom_CHAOS_why": "最近{window_min}分钟发生{turnovers}次球权转换，传球最多的一方也只占{share_pct}%。",
        "mom_BALANCED_head": "{t} 比赛节奏趋于平稳。",
        "mom_BALANCED_why": "球权较为均衡：领先方占{share_pct}%的传球，最近{window_min}分钟有{turnovers}次球权转换。",
        "rhythm_fast": "快", "rhythm_steady": "平稳", "rhythm_slow": "慢", "tempo": "节奏：{rhythm}。",
        "link_head": "{t} 连线提示：{pair} 现为 {to}。",
        "link_SUPER_LINK_why": "最近{n}次传球的平滑成功率为{smoothed_pct}%，高于基线。",
        "link_COOLING_DOWN_why": "在窗口内{n}次传球后，已不再满足超级连线条件。",
        "milestone_head": "{t} {player}完成了第{count}次成功传球。",
        "milestone_why": "这显示出{player}在组织进攻中的参与度。",
        "recap_open": "比赛回顾（{clock}）：{home} {hs}-{as_} {away}。", "recap_lead": "关键时刻：",
        "recap_empty": "暂无关键时刻。",
        "recap_poss": "按传球计的控球：{home} {home_pct}%，{away} {away_pct}%。",
    },
    "ja": {
        "sep": "",
        "goal_head": "{t} ゴール！{team}の{scorer}が決めた。", "goal_assist": "アシストは{assist}。",
        "why_opened": "これが試合の先制点。", "why_took_lead": "{team}がリードを奪った。",
        "why_equalised": "試合は振り出しに戻った。", "why_extended": "リードを広げた。",
        "why_pulled_back": "1点を返した。",
        "goal_link": "その時点で{assist} → {scorer}のリンクは{link_buff}だった。",
        "goal_stat": "スコア {score_home}-{score_away}、xG {xg}、シュート速度 {speed} km/h。",
        "big_head": "{t} {team}の{shooter}に大チャンス：{outcome}。",
        "big_why": "質の高いチャンスで、xGは{xg}。", "big_stat": "シュート速度 {speed} km/h。",
        "outcome_saved": "セーブされた", "outcome_off": "枠外", "outcome_blocked": "ブロックされた",
        "fast_head": "{t} {team}の{shooter}が時速{speed} kmのシュートを放つ。",
        "fast_why": "{threshold} km/hのしきい値を上回った。",
        "long_head": "{t} {passer}が{distance} mのパスで{receiver}を見つけた。",
        "long_why": "成功したロングパスで、{threshold} mのしきい値を上回った。",
        "mom_CONTROL_head": "{t} {team}が主導権を握る。",
        "mom_CONTROL_why": "直近{window_min}分間でパスの{share_pct}%を占め、ターンオーバーは{turnovers}回だけ。",
        "mom_HIGH_PRESS_head": "{t} {team}が高い位置からプレス。",
        "mom_HIGH_PRESS_why": "直近{window_min}分間でプレッシャーが{pressures}回。",
        "mom_CHAOS_head": "{t} 試合が混沌としてきた。",
        "mom_CHAOS_why": "直近{window_min}分間でボール保持の入れ替わりが{turnovers}回、最多のチームでもパスの{share_pct}%。",
        "mom_BALANCED_head": "{t} 試合が落ち着いた。",
        "mom_BALANCED_why": "ボール保持は拮抗：優勢側のパスは{share_pct}%、直近{window_min}分間のターンオーバーは{turnovers}回。",
        "rhythm_fast": "速い", "rhythm_steady": "安定", "rhythm_slow": "遅い", "tempo": "テンポ：{rhythm}。",
        "link_head": "{t} リンク速報：{pair}が{to}に。",
        "link_SUPER_LINK_why": "直近{n}本のパスの平滑化成功率は{smoothed_pct}%で、基準を上回る。",
        "link_COOLING_DOWN_why": "ウィンドウ内の{n}本のパスの後、スーパーリンクの条件を満たさなくなった。",
        "milestone_head": "{t} {player}が{count}本目のパス成功。",
        "milestone_why": "{player}が組み立てに深く関わっていることを示す。",
        "recap_open": "試合ハイライト（{clock}）：{home} {hs}-{as_} {away}。", "recap_lead": "注目の場面：",
        "recap_empty": "まだ注目の場面はありません。",
        "recap_poss": "パス数ベースの支配率：{home} {home_pct}%、{away} {away_pct}%。",
    },
    "es": {
        "sep": " ",
        "goal_head": "{t} ¡GOL! {scorer} marca para {team}.", "goal_assist": "Asistencia de {assist}.",
        "why_opened": "Abre el marcador.", "why_took_lead": "Pone a {team} por delante.",
        "why_equalised": "Iguala el partido.", "why_extended": "Amplía la ventaja.",
        "why_pulled_back": "Acorta distancias.",
        "goal_link": "El vínculo {assist} → {scorer} estaba en {link_buff} en ese momento.",
        "goal_stat": "Marcador {score_home}-{score_away}; xG {xg}; velocidad del disparo {speed} km/h.",
        "big_head": "{t} Gran ocasión para {shooter} ({team}): {outcome}.",
        "big_why": "Una ocasión de gran calidad, con un xG de {xg}.", "big_stat": "Velocidad del disparo {speed} km/h.",
        "outcome_saved": "parada", "outcome_off": "fuera", "outcome_blocked": "bloqueado",
        "fast_head": "{t} {shooter} ({team}) dispara a {speed} km/h.",
        "fast_why": "Supera el umbral de {threshold} km/h.",
        "long_head": "{t} {passer} encuentra a {receiver} con un pase de {distance} m.",
        "long_why": "Un pase largo completado, por encima del umbral de {threshold} m.",
        "mom_CONTROL_head": "{t} {team} toma el control.",
        "mom_CONTROL_why": "Tiene el {share_pct}% de los pases en los últimos {window_min} minutos y solo {turnovers} pérdidas.",
        "mom_HIGH_PRESS_head": "{t} {team} presiona arriba.",
        "mom_HIGH_PRESS_why": "{pressures} acciones de presión en los últimos {window_min} minutos.",
        "mom_CHAOS_head": "{t} El partido se vuelve caótico.",
        "mom_CHAOS_why": "{turnovers} cambios de posesión en los últimos {window_min} minutos y el equipo con más pases solo tiene el {share_pct}%.",
        "mom_BALANCED_head": "{t} El partido se calma.",
        "mom_BALANCED_why": "La posesión está repartida: {share_pct}% de los pases para el líder y {turnovers} pérdidas en los últimos {window_min} minutos.",
        "rhythm_fast": "rápido", "rhythm_steady": "estable", "rhythm_slow": "lento", "tempo": "Ritmo: {rhythm}.",
        "link_head": "{t} Alerta de vínculo: {pair} pasa a {to}.",
        "link_SUPER_LINK_why": "Tasa de acierto suavizada del {smoothed_pct}% en los últimos {n} pases, por encima de la base.",
        "link_COOLING_DOWN_why": "Ya no cumple los criterios de Super Link tras {n} pases en la ventana.",
        "milestone_head": "{t} {player} completa el pase número {count}.",
        "milestone_why": "Muestra lo involucrado que está {player} en la construcción.",
        "recap_open": "Resumen del partido a los {clock}: {home} {hs}-{as_} {away}.", "recap_lead": "Momentos clave:",
        "recap_empty": "Aún no hay momentos clave.",
        "recap_poss": "Posesión según pases: {home} {home_pct}%, {away} {away_pct}%.",
    },
}

CHIP = {
    "en": {"score": "Score", "xg": "xG", "speed": "Shot speed", "distance": "Distance", "possession": "Possession",
           "turnovers": "Turnovers", "pressures": "Pressures", "rate": "Smoothed rate", "passes": "Passes"},
    "zh": {"score": "比分", "xg": "xG", "speed": "射门速度", "distance": "距离", "possession": "控球",
           "turnovers": "球权转换", "pressures": "施压", "rate": "平滑成功率", "passes": "传球"},
    "ja": {"score": "スコア", "xg": "xG", "speed": "シュート速度", "distance": "距離", "possession": "支配率",
           "turnovers": "ターンオーバー", "pressures": "プレス", "rate": "平滑化成功率", "passes": "パス"},
    "es": {"score": "Marcador", "xg": "xG", "speed": "Velocidad", "distance": "Distancia", "possession": "Posesión",
           "turnovers": "Pérdidas", "pressures": "Presiones", "rate": "Tasa suavizada", "passes": "Pases"},
}


def facts_text(m) -> str:
    """Everything the narrator is allowed to say. The Verifier checks outputs against this text."""
    lines = [f"Type: {m.type}", f"Time: {m.time}", f"Team: {m.team or 'n/a'}"]
    if m.players:
        lines.append("Players: " + ", ".join(m.players))
    lines += [f"{k}: {v}" for k, v in m.facts.items()]
    lines.append(f"Engine reason: {m.why_en}")
    return "\n".join(lines)


def render_parts(m, lang: str = "en", detail: str = "Casual fan") -> list:
    tr = T[lang]
    f = {"t": m.time, "team": m.team, **m.facts}
    if "outcome" in f:
        f["outcome"] = tr["outcome_" + f["outcome"]]
    if "rhythm" in f:
        f["rhythm"] = tr["rhythm_" + f["rhythm"]]
    ty, parts = m.type, []
    if ty == "goal":
        parts = [tr["goal_head"], tr["goal_assist"] if "assist" in f else "", tr["why_" + f["code"]],
                 tr["goal_link"] if "link_buff" in f else ""]
        stat = tr["goal_stat"]
    elif ty == "big_chance":
        parts, stat = [tr["big_head"], tr["big_why"]], tr["big_stat"]
    elif ty == "fast_shot":
        parts, stat = [tr["fast_head"], tr["fast_why"]], ""
    elif ty == "long_pass":
        parts, stat = [tr["long_head"], tr["long_why"]], ""
    elif ty == "momentum":
        parts, stat = [tr[f"mom_{m.facts['state']}_head"], tr[f"mom_{m.facts['state']}_why"]], tr["tempo"]
    elif ty == "link":
        parts, stat = [tr["link_head"], tr[f"link_{m.facts['to']}_why"]], ""
    else:  # milestone
        parts, stat = [tr["milestone_head"], tr["milestone_why"]], ""
    if detail == "Analyst" and stat:
        parts.append(stat)
    return [p.format(**f) for p in parts if p]


def render(m, lang: str = "en", detail: str = "Casual fan", opener: str = "") -> str:
    text = T[lang]["sep"].join(render_parts(m, lang, detail))
    return f"{opener} {text}".strip() if opener else text


# ---------------- chemistry (link engine) texts ----------------
CH = {
 "en": {"insuff": "Only {n} pair pass(es) so far; at least {min} are needed before any judgment.",
        "super": "Smoothed rate {sm} ≥ {thr} over the last {n} passes, with {p} progressive passes and {c} chance(s) created.",
        "cool_enter": "No longer meets Super Link criteria. Holding for {cd} pair passes before downgrading.",
        "cool_left": "Cooling down: {left} pair pass(es) left in the hold period.",
        "potential": "Smoothed rate {sm} is above the {b} baseline, but not all Super Link criteria are met.",
        "normal": "Smoothed rate {sm} is not clearly above the {b} team baseline.",
        "u_att": "Needs {need} passes in the window (has {has}).", "u_rate": "Smoothed rate must be ≥ {thr} (now {cur}).",
        "u_prog": "Needs {need} progressive passes (has {has}).", "u_chance": "Needs {need} chance created (has {has}).",
        "tag_SUPER_LINK": "The link is clicking.", "tag_COOLING_DOWN": "The connection is cooling off.",
        "tag_POTENTIAL_LINK": "Early signs of a link.", "tag_NORMAL": "Back to ordinary levels.",
        "tag_INSUFFICIENT_EVIDENCE": "Too early to say.",
        "detail": "Over the last {a} forward passes, {s} succeeded ({sm} smoothed vs a {b} baseline), with {p} progressive and {c} chance(s) created."},
 "zh": {"insuff": "目前仅有{n}次该配对传球；至少需要{min}次才能做出判断。",
        "super": "最近{n}次传球的平滑成功率为{sm}，不低于{thr}，并有{p}次推进传球和{c}次创造机会。",
        "cool_enter": "已不再满足超级连线条件，将在{cd}次配对传球后再降级。",
        "cool_left": "冷却中：保持期内还剩{left}次配对传球。",
        "potential": "平滑成功率{sm}高于{b}的基线，但尚未满足全部超级连线条件。",
        "normal": "平滑成功率{sm}没有明显高于{b}的球队基线。",
        "u_att": "窗口内需要{need}次传球（目前{has}次）。", "u_rate": "平滑成功率需不低于{thr}（目前{cur}）。",
        "u_prog": "需要{need}次推进传球（目前{has}次）。", "u_chance": "需要创造{need}次机会（目前{has}次）。",
        "tag_SUPER_LINK": "连线状态火热。", "tag_COOLING_DOWN": "这对搭档正在降温。",
        "tag_POTENTIAL_LINK": "出现了连线的早期迹象。", "tag_NORMAL": "回到普通水平。",
        "tag_INSUFFICIENT_EVIDENCE": "为时尚早，无法判断。",
        "detail": "最近{a}次前插传球中成功{s}次（平滑成功率{sm}，基线{b}），其中推进传球{p}次，创造机会{c}次。"},
 "ja": {"insuff": "このペアのパスはまだ{n}本。判断には少なくとも{min}本必要。",
        "super": "直近{n}本のパスの平滑化成功率は{sm}で{thr}以上、前進パス{p}本、チャンス創出{c}回。",
        "cool_enter": "スーパーリンクの条件を満たさなくなった。{cd}本のペアパスの間は様子を見る。",
        "cool_left": "クールダウン中：保持期間はあと{left}本。",
        "potential": "平滑化成功率{sm}は基準{b}を上回るが、スーパーリンクの全条件は未達。",
        "normal": "平滑化成功率{sm}はチーム基準{b}を明確には上回っていない。",
        "u_att": "ウィンドウ内に{need}本のパスが必要（現在{has}本）。", "u_rate": "平滑化成功率が{thr}以上必要（現在{cur}）。",
        "u_prog": "前進パスが{need}本必要（現在{has}本）。", "u_chance": "チャンス創出が{need}回必要（現在{has}回）。",
        "tag_SUPER_LINK": "リンクが噛み合っている。", "tag_COOLING_DOWN": "つながりが冷めてきた。",
        "tag_POTENTIAL_LINK": "リンクの兆しが見える。", "tag_NORMAL": "通常レベルに戻った。",
        "tag_INSUFFICIENT_EVIDENCE": "判断するには早すぎる。",
        "detail": "直近{a}本の前方パスのうち{s}本が成功（平滑化{sm}、基準{b}）、前進パス{p}本、チャンス創出{c}回。"},
 "es": {"insuff": "Solo {n} pase(s) de esta pareja; hacen falta al menos {min} para juzgar.",
        "super": "Tasa suavizada {sm} ≥ {thr} en los últimos {n} pases, con {p} pases progresivos y {c} ocasión(es) creada(s).",
        "cool_enter": "Ya no cumple los criterios de Super Link. Se mantiene durante {cd} pases de la pareja antes de bajar.",
        "cool_left": "Enfriándose: quedan {left} pase(s) de la pareja en el periodo de espera.",
        "potential": "La tasa suavizada {sm} supera la base de {b}, pero no se cumplen todos los criterios de Super Link.",
        "normal": "La tasa suavizada {sm} no supera con claridad la base del equipo ({b}).",
        "u_att": "Necesita {need} pases en la ventana (tiene {has}).", "u_rate": "La tasa suavizada debe ser ≥ {thr} (ahora {cur}).",
        "u_prog": "Necesita {need} pases progresivos (tiene {has}).", "u_chance": "Necesita {need} ocasión creada (tiene {has}).",
        "tag_SUPER_LINK": "El vínculo funciona.", "tag_COOLING_DOWN": "La conexión se está enfriando.",
        "tag_POTENTIAL_LINK": "Primeras señales de vínculo.", "tag_NORMAL": "Vuelve a niveles normales.",
        "tag_INSUFFICIENT_EVIDENCE": "Demasiado pronto para opinar.",
        "detail": "En los últimos {a} pases hacia delante, {s} fueron exitosos ({sm} suavizado frente a una base de {b}), con {p} progresivos y {c} ocasión(es) creada(s)."},
}


def chem_reason(state, lang: str = "en") -> str:
    """Localised version of the link engine's reason, rebuilt from the numbers in the state."""
    import chem_config as C
    import chem_engine as engine
    tr, st = CH[lang], state.stats
    sm = f"{st.smoothed:.1%}" if st.smoothed is not None else "n/a"
    b = f"{C.TEAM_BASELINE:.0%}"
    if state.buff == C.INSUFFICIENT:
        return tr["insuff"].format(n=st.attempts, min=C.R.min_attempts)
    if state.buff == C.SUPER:
        return tr["super"].format(sm=sm, thr=f"{engine.super_threshold():.1%}", n=st.attempts,
                                  p=st.progressive, c=st.chances)
    if state.buff == C.COOLING:
        return (tr["cool_enter"].format(cd=C.R.cooldown_events) if state.cooldown_left == C.R.cooldown_events
                else tr["cool_left"].format(left=state.cooldown_left))
    return tr["potential" if state.buff == C.POTENTIAL else "normal"].format(sm=sm, b=b)


def chem_unmet(state, lang: str = "en") -> list:
    import chem_config as C
    import chem_engine as engine
    tr, st, R = CH[lang], state.stats, C.R
    thr, out = engine.super_threshold(), []
    if st.attempts < R.super_min_attempts:
        out.append(tr["u_att"].format(need=R.super_min_attempts, has=st.attempts))
    if st.smoothed is None or st.smoothed < thr:
        out.append(tr["u_rate"].format(thr=f"{thr:.1%}", cur="n/a" if st.smoothed is None else f"{st.smoothed:.1%}"))
    if st.progressive < R.super_min_progressive:
        out.append(tr["u_prog"].format(need=R.super_min_progressive, has=st.progressive))
    if st.chances < R.super_min_chances:
        out.append(tr["u_chance"].format(need=R.super_min_chances, has=st.chances))
    return out


def tactical_text(tac, lang: str = "en") -> str:
    from ui_text import U
    if tac.label == "WARMING_UP":
        return U(lang, "warm_reason")
    return T[lang][f"mom_{tac.label}_why"].format(share_pct=tac.share_pct, turnovers=tac.turnovers,
                                                    pressures=tac.pressures, window_min=tac.window_min)
