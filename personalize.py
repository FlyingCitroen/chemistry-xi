"""Stage (e) PERSONALIZE: the same moments reach an analyst and a casual fan very differently."""
from __future__ import annotations

from dataclasses import dataclass

METRIC_TYPES = {"shot_speed": {"fast_shot", "goal", "big_chance"},
                "pass_quality": {"long_pass", "link", "milestone"},
                "pressure": {"momentum"},
                "chemistry": {"link"}}
THRESHOLD = {"Casual fan": 0.7, "Analyst": 0.3}


@dataclass(frozen=True)
class Profile:
    mode: str = "Casual fan"        # Casual fan | Analyst
    lang: str = "en"
    club: str | None = None
    player: str | None = None
    player_focus: bool = False      # only show moments involving `player`
    metric: str = "auto"
    persona: str = "Fan"

    def key(self) -> tuple:
        return (self.mode, self.lang, self.club, self.player, self.player_focus, self.metric, self.persona)

    @staticmethod
    def from_key(k) -> "Profile":
        return Profile(*k)


def relevance(m, p: Profile) -> float:
    s = m.significance
    if p.club and m.team == p.club:
        s += 0.3
    if p.player and p.player in m.players:
        s += 0.5
    if m.type in METRIC_TYPES.get(p.metric, ()):
        s += 0.3
    return round(s, 3)


def select(moments, p: Profile) -> list:
    keep = []
    for m in moments:
        if p.player_focus and p.player and p.player not in m.players:
            continue
        if relevance(m, p) >= THRESHOLD.get(p.mode, 0.7):
            keep.append(m)
    return keep
