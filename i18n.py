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
