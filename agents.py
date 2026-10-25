"""Multi-agent layer. The rule engine is the single source of truth.

Analyst   - deterministic tools (chem_engine) produce a Finding. No LLM, no judgment calls by AI.
Narrator  - writes the story in a persona's voice (Azure OpenAI, or a template when unavailable).
Verifier  - rejects any draft containing numbers, buff labels or players that are not in the facts.
Orchestrator - Narrator <-> Verifier loop with feedback, max N attempts, then a verified template.
Recap     - the same loop applied to the whole match.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import chem_config as C
import chem_engine as engine
import i18n
import insight
import llm

PERSONAS = {
    "Fan": "an enthusiastic supporter talking to friends: warm, simple, a little emotive, no jargon",
    "Commentator": "a live TV commentator: punchy, present tense, dramatic but precise",
    "Coach": "a performance analyst briefing a head coach: concise, measured, mentions uncertainty",
    "Analyst": "a data analyst: precise, quantitative, neutral, mentions the metric behind each claim",
}
OPENERS = {"Fan": "Look at this!", "Commentator": "And there it is!", "Coach": "Analyst note:",
           "Analyst": "Data point:"}
TAGS = {
    C.SUPER: "The link is clicking.",
    C.COOLING: "The connection is cooling off.",
    C.POTENTIAL: "Early signs of a link.",
    C.NORMAL: "Back to ordinary levels.",
    C.INSUFFICIENT: "Too early to say.",
}

SYSTEM = ("You write football match commentary from a rule engine's output. Use ONLY the facts "
          "given. Never invent numbers, players, causes or predictions. Copy numbers and buff "
          "labels exactly as written. The data is synthetic. Voice: {voice}. {length}")


# ---------------- data containers ----------------
@dataclass(frozen=True)
class Step:
    agent: str
    action: str
    detail: str
    ok: bool = True


@dataclass(frozen=True)
class Result:
    text: str
    mode: str          # "llm" | "template" | "fallback"
    trace: tuple


@dataclass(frozen=True)
class Finding:
    label: str
    time: str
    frm: str
    to: str
    attempts: int
    successes: int
    progressive: int
    chances: int
    smoothed: float
    lo: float
    hi: float
    reason: str
    unmet: tuple

    def facts(self) -> str:
        lines = [
            f"Pair: {self.label}",
            f"Time: {self.time}",
            f"Buff change: {self.frm} -> {self.to}",
            f"Window: last {self.attempts} forward passes, {self.successes} successful, "
            f"{self.progressive} progressive, {self.chances} chances created",
            f"Smoothed success rate: {self.smoothed:.1%} (approx. 80% interval "
            f"{self.lo:.1%} to {self.hi:.1%}); team baseline {C.TEAM_BASELINE:.0%}",
            f"Engine reason: {self.reason}",
        ]
        if self.unmet:
            lines.append("Still missing for SUPER_LINK: " + " ".join(self.unmet))
        return "\n".join(lines)


# ---------------- Analyst (deterministic tool use) ----------------
def build_finding(label: str, transition: dict, state) -> Finding:
    s = state.stats
    return Finding(label, transition["Time"], transition["From"], transition["To"],
                   s.attempts, s.successes, s.progressive, s.chances,
                   s.smoothed, s.lo, s.hi, transition["Reason"], tuple(state.unmet))


# ---------------- Verifier ----------------
NUM = re.compile(r"\d+:\d+|\d+(?:\.\d+)?")
BUFF = re.compile(r"\b[A-Z]{2,}(?:_[A-Z]+)+\b")


def _allowed_numbers(facts: str) -> set:
    allowed = set()
    for tok in NUM.findall(facts):
        if ":" in tok:
            allowed.add(tok)
            allowed.update(float(p) for p in tok.split(":"))
        else:
            v = float(tok)
            allowed.add(v)
            if "." in tok:
                allowed.add(float(int(v + 0.5)))  # "72.5%" may be written as "73%"
    return allowed


def verify(text: str, facts: str) -> list[str]:
    """Return a list of problems; an empty list means the text is grounded in the facts."""
    issues = []
    if not text.strip():
        return ["Empty text."]
    if len(text) > 700:
        issues.append("Too long.")
    allowed = _allowed_numbers(facts)
    for tok in NUM.findall(text):
        key = tok if ":" in tok else float(tok)
        if key not in allowed:
            issues.append(f"Number '{tok}' is not in the facts.")
    for name in set(BUFF.findall(text)):
        if name not in facts:
            issues.append(f"Buff label '{name}' is not in the facts.")
    for player in C.ALL_PLAYERS:  # lookarounds instead of \b so names inside CJK text are caught too
        if re.search(rf"(?<![A-Za-z]){player}(?![A-Za-z])", text) and player not in facts:
            issues.append(f"Player '{player}' is not in the facts.")
    return issues


# ---------------- Narrator + orchestrator ----------------
def _run(facts: str, template: str, persona: str, length: str, trace: list,
         llm_fn, max_attempts: int) -> Result:
    system = SYSTEM.format(voice=PERSONAS[persona], length=length)
    feedback, text, mode = "", None, "template"
    for attempt in range(1, max_attempts + 1):
        draft = llm_fn(system, f"Facts:\n{facts}{feedback}")
        if draft is None:
            trace.append(Step("Narrator", "template mode",
                              "Azure OpenAI not configured or unavailable; using deterministic template."))
            break
        trace.append(Step("Narrator", f"draft #{attempt}", draft))
        issues = verify(draft, facts)
        trace.append(Step("Verifier", f"check #{attempt}", "PASS" if not issues else "; ".join(issues),
                          not issues))
        if not issues:
            text, mode = draft, "llm"
            break
        feedback = ("\n\nYour previous draft was REJECTED by the verifier: " + "; ".join(issues)
                    + ". Rewrite it using only the facts above.")
    else:
        mode = "fallback"
        trace.append(Step("Orchestrator", "fallback",
                          f"No draft passed in {max_attempts} attempts; using verified template."))
    if text is None:
        text = template
        issues = verify(text, facts)
        trace.append(Step("Verifier", "check template", "PASS" if not issues else "; ".join(issues),
                          not issues))
    return Result(text, mode, tuple(trace))


def narration_template(f: Finding, persona: str) -> str:
    return (f"{OPENERS[persona]} {f.time} — {f.label}: {f.frm} → {f.to}. {TAGS[f.to]} "
            f"Over the last {f.attempts} forward passes, {f.successes} succeeded "
            f"({f.smoothed:.1%} smoothed vs a {C.TEAM_BASELINE:.0%} baseline), with "
            f"{f.progressive} progressive and {f.chances} chance(s) created.")


def narrate(f: Finding, persona: str, llm_fn=None, max_attempts: int = 3) -> Result:
    llm_fn = llm_fn or llm.chat
    trace = [Step("Analyst", "tool: build_finding",
                  f"{f.label}: {f.frm} → {f.to} at {f.time} (deterministic engine output)")]
    return _run(f.facts(), narration_template(f, persona), persona,
                "Write at most 2 sentences.", trace, llm_fn, max_attempts)


# ---------------- Recap agent ----------------
def recap(events, timelines, k: int, persona: str, llm_fn=None, max_attempts: int = 3):
    llm_fn = llm_fn or llm.chat
    moments = []
    for pair, tl in timelines.items():
        for i in range(1, min(k, len(tl) - 1) + 1):
            if tl[i].buff != tl[i - 1].buff and tl[i].buff in (C.SUPER, C.COOLING):
                e = events[i - 1]
                moments.append({"i": i, "time": f"{e['minute']:02d}:{e['second']:02d}",
                                "label": f"{pair[0]} → {pair[1]}", "to": tl[i].buff,
                                "smoothed": tl[i].stats.smoothed, "n": tl[i].stats.attempts})
    moments.sort(key=lambda m: m["i"])
    moments = moments[-6:]
    top = engine.leaderboard(timelines, k, C.R.super_min_attempts)[:3]
    clock = f"{events[k-1]['minute']:02d}:{events[k-1]['second']:02d}" if k else "00:00"

    facts = [f"Match clock: {clock}; events played: {k}"]
    facts += [f"Moment: {m['time']} {m['label']} became {m['to']} "
              f"(smoothed {m['smoothed']:.1%} over {m['n']} passes)" for m in moments]
    facts += [f"Rank {r}: {t['label']} lower bound {t['Low']:.1%}, {t['Passes']} passes, "
              f"status {t['Buff']}" for r, t in enumerate(top, 1)]

    parts = [f"{OPENERS[persona]} Match recap at {clock}."]
    parts.append("Key link moments: " + "; ".join(
        f"{m['time']} {m['label']} became {m['to']} ({m['smoothed']:.1%} smoothed over {m['n']} passes)"
        for m in moments) + "." if moments else "No Super Link moments yet.")
    if top:
        parts.append("Most reliable links by conservative lower bound: " + "; ".join(
            f"{t['label']} ({t['Low']:.1%}, {t['Passes']} passes)" for t in top) + ".")
    trace = [Step("Analyst", "tool: scan_all_pairs + leaderboard",
                  f"{len(timelines)} pairs scanned; {len(moments)} key moments; top {len(top)} ranked")]
    result = _run("\n".join(facts), " ".join(parts), persona,
                  "Write 3 to 4 sentences as a short match recap.", trace, llm_fn, max_attempts)
    return result, moments, top


# ---------------- Moment narration & match recap (multi-language, personalised) ----------------
def narrate_moment(m, persona: str, lang: str, detail: str, llm_fn=None, max_attempts: int = 3) -> Result:
    llm_fn = llm_fn or llm.chat
    opener = OPENERS.get(persona, "") if lang == "en" else ""
    trace = [Step("Analyst", "tool: detect_moment",
                  f"{m.type} at {m.time} (significance {m.significance:.2f}) — deterministic engine output")]
    return _run(i18n.facts_text(m), i18n.render(m, lang, detail, opener), persona,
                f"Write at most 2 sentences in {i18n.LANGS[lang]}. Keep names, numbers and labels exactly.",
                trace, llm_fn, max_attempts)


def recap_match(events, k: int, moments, profile, llm_fn=None, max_attempts: int = 3) -> Result:
    """Personalised full-match recap built only from verified moments and engine statistics."""
    llm_fn = llm_fn or llm.chat
    lang, detail = profile.lang, profile.mode
    tr = i18n.T[lang]
    sc, poss = insight.score(events[:k]), insight.possession(events[:k])
    home, away = C.TEAMS
    clock = insight.clock(events[k - 1]) if k else "00:00"
    top = sorted(sorted(moments, key=lambda m: m.significance, reverse=True)[:4], key=lambda m: m.k)
    facts = [f"Match clock: {clock}", f"Score: {home} {sc[home]}-{sc[away]} {away}",
             f"Possession by passes: {home} {poss[home]}%, {away} {poss[away]}%"]
    facts += ["---\n" + i18n.facts_text(m) for m in top]
    parts = [tr["recap_open"].format(clock=clock, home=home, hs=sc[home], as_=sc[away], away=away)]
    parts.append(tr["recap_lead"] + " " + tr["sep"].join(i18n.render(m, lang, "Casual fan") for m in top)
                 if top else tr["recap_empty"])
    if detail == "Analyst":
        parts.append(tr["recap_poss"].format(home=home, home_pct=poss[home], away=away, away_pct=poss[away]))
    trace = [Step("Analyst", "tool: select_moments",
                  f"{len(top)} moments chosen for this viewer profile ({detail}, {lang}"
                  f"{', ' + profile.club if profile.club else ''}{', ' + profile.player if profile.player else ''})")]
    return _run("\n".join(facts), " ".join(parts), profile.persona,
                f"Write 3 to 5 sentences as a match recap in {i18n.LANGS[lang]}. Keep names, numbers, "
                "labels exactly.", trace, llm_fn, max_attempts)
