"""Pure, deterministic rule engine (no Streamlit). Timeline[k] only uses events[:k]."""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import sqrt

from chem_config import (COOLING, INSUFFICIENT, NORMAL, POTENTIAL, R, SUPER,
                    TEAM_BASELINE as B)

Z80 = 1.2816  # normal quantile for an ~80% interval


@dataclass(frozen=True)
class WindowStats:
    attempts: int = 0
    successes: int = 0
    progressive: int = 0
    chances: int = 0
    raw: float | None = None
    smoothed: float | None = None
    lo: float | None = None
    hi: float | None = None
    evidence: tuple = ()  # event_ids in the current window


@dataclass(frozen=True)
class State:
    k: int = 0
    buff: str = INSUFFICIENT
    reason: str = "No pair passes yet."
    stats: WindowStats = WindowStats()
    unmet: tuple = ()      # what is still missing for SUPER_LINK (counterfactual)
    pair_n: int = 0        # total pair passes so far (not windowed)
    cooldown_left: int = 0


def is_pair_event(e, pair) -> bool:
    return (e["player_from"], e["player_to"]) == tuple(pair) and e["event_type"] == "forward_pass"


def window_stats(pair_events) -> WindowStats:
    recent = pair_events[-R.window:]
    n = len(recent)
    if n == 0:
        return WindowStats()
    s = sum(e["successful"] for e in recent)
    # Beta(alpha*B, alpha*(1-B)) prior -> posterior mean == (s + alpha*B) / (n + alpha)
    a = s + R.prior_weight * B
    b = (n - s) + R.prior_weight * (1 - B)
    mean = a / (a + b)
    sd = sqrt(mean * (1 - mean) / (a + b + 1))
    return WindowStats(
        attempts=n, successes=s,
        progressive=sum(e["progressive"] for e in recent),
        chances=sum(e["chance_created"] for e in recent),
        raw=s / n, smoothed=mean,
        lo=max(0.0, mean - Z80 * sd), hi=min(1.0, mean + Z80 * sd),
        evidence=tuple(e["event_id"] for e in recent),
    )


def super_threshold() -> float:
    return B + R.super_margin


def unmet_super(st: WindowStats) -> list[str]:
    out = []
    if st.attempts < R.super_min_attempts:
        out.append(f"Needs {R.super_min_attempts} passes in the window (has {st.attempts}).")
    if st.smoothed is None or st.smoothed < super_threshold():
        cur = "n/a" if st.smoothed is None else f"{st.smoothed:.1%}"
        out.append(f"Smoothed rate must be ≥ {super_threshold():.1%} (now {cur}).")
    if st.progressive < R.super_min_progressive:
        out.append(f"Needs {R.super_min_progressive} progressive passes (has {st.progressive}).")
    if st.chances < R.super_min_chances:
        out.append(f"Needs {R.super_min_chances} chance created (has {st.chances}).")
    return out


def step(st: WindowStats, prev: str, cool: int):
    """Decide the next buff after a new pair pass. Returns (buff, cooldown_left, reason)."""
    n = st.attempts
    if n < R.min_attempts:
        return INSUFFICIENT, 0, (f"Only {n} pair pass(es) so far; at least {R.min_attempts} "
                                 "are needed before any judgment.")
    if not unmet_super(st):
        return SUPER, 0, (f"Smoothed rate {st.smoothed:.1%} ≥ {super_threshold():.1%} over the last "
                          f"{n} passes, with {st.progressive} progressive passes and "
                          f"{st.chances} chance(s) created.")
    if prev == SUPER:
        return COOLING, R.cooldown_events, (
            "No longer meets Super Link criteria. Holding for "
            f"{R.cooldown_events} pair passes before downgrading.")
    if prev == COOLING and cool > 1:
        return COOLING, cool - 1, f"Cooling down: {cool - 1} pair pass(es) left in the hold period."
    if st.smoothed >= B + R.potential_margin:
        return POTENTIAL, 0, (f"Smoothed rate {st.smoothed:.1%} is above the {B:.0%} baseline, "
                              "but not all Super Link criteria are met.")
    return NORMAL, 0, f"Smoothed rate {st.smoothed:.1%} is not clearly above the {B:.0%} team baseline."


def build_timeline(events, pair) -> list[State]:
    """states[k] = analysis after the first k events. Events must be time-sorted."""
    states, pair_events = [State()], []
    for k, e in enumerate(events, 1):
        prev = states[-1]
        if not is_pair_event(e, pair):
            states.append(replace(prev, k=k))
            continue
        pair_events.append(e)
        st = window_stats(pair_events)
        buff, cool, reason = step(st, prev.buff, prev.cooldown_left)
        states.append(State(k, buff, reason, st, tuple(unmet_super(st)), len(pair_events), cool))
    return states


def transitions(states, events, upto: int) -> list[dict]:
    out = []
    for i in range(1, upto + 1):
        if states[i].buff != states[i - 1].buff:
            e = events[i - 1]
            sm = states[i].stats.smoothed
            out.append({
                "Event #": i,
                "Time": f"{e['minute']:02d}:{e['second']:02d}",
                "From": states[i - 1].buff,
                "To": states[i].buff,
                "Smoothed": None if sm is None else round(sm, 3),
                "Reason": states[i].reason,
            })
    return out


def all_pairs(events):
    return sorted({(e["player_from"], e["player_to"]) for e in events if e["event_type"] == "forward_pass"})


def scan_all(events) -> dict:
    """Timeline for every directed pair that has at least one forward pass."""
    return {p: build_timeline(events, p) for p in all_pairs(events)}


def leaderboard(timelines: dict, k: int, min_n: int | None = None) -> list[dict]:
    """Rank pairs at event k by the LOWER credible bound, so tiny samples cannot top the table."""
    rows = []
    for (a, b), tl in timelines.items():
        s = tl[min(k, len(tl) - 1)]
        if s.stats.attempts >= (R.min_attempts if min_n is None else min_n):
            rows.append({"label": f"{a} → {b}", "Pair": f"{a} → {b}", "Passes": s.pair_n,
                         "Window": s.stats.attempts, "Buff": s.buff, "Smoothed": s.stats.smoothed,
                         "Low": s.stats.lo, "High": s.stats.hi})
    return sorted(rows, key=lambda r: r["Low"], reverse=True)
