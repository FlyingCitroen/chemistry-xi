"""Single source of truth for all rules, so every module uses the same thresholds."""
from dataclasses import dataclass
from pathlib import Path

DATA_FILE = Path(__file__).parent / "match_events.json"
TEAM = "Northbridge FC"
OPPONENT = "Eastport United"
TEAMS = [TEAM, OPPONENT]
ROSTER = {  # fictional players: name -> (team, shirt number, position)
    "Alex": (TEAM, 9, "FW"), "Jamie": (TEAM, 10, "AM"), "Morgan": (TEAM, 8, "CM"),
    "Taylor": (TEAM, 7, "RW"), "Jordan": (TEAM, 6, "DM"), "Riley": (TEAM, 4, "CB"),
    "Casey": (TEAM, 3, "LB"), "Drew": (TEAM, 1, "GK"),
    "Sam": (OPPONENT, 9, "FW"), "Quinn": (OPPONENT, 10, "AM"), "Reese": (OPPONENT, 8, "CM"),
    "Blake": (OPPONENT, 11, "LW"), "Avery": (OPPONENT, 5, "CB"), "Rowan": (OPPONENT, 6, "DM"),
    "Skyler": (OPPONENT, 2, "RB"), "Emerson": (OPPONENT, 1, "GK"),
}
PLAYERS = [n for n, v in ROSTER.items() if v[0] == TEAM]   # Northbridge FC
ALL_PLAYERS = list(ROSTER)
META_FILE = Path(__file__).parent / "match_meta.json"

# Indicator / insight thresholds (illustrative)
LONG_PASS_M = 30
FAST_SHOT_KMH = 100
FAST_PASS_KMH = 85
BIG_CHANCE_XG = 0.25
MILESTONE_PASSES = 15
TACTICAL_WINDOW_S = 300
CONTROL_SHARE = 0.60
CONTROL_MAX_TURNOVERS = 2
CHAOS_MIN_TURNOVERS = 4
PRESS_MIN = 4
WARMUP_EVENTS = 8

# Pre-match team baseline (e.g. from previous matches). Fixed in advance, so it never
# peeks at the future of the match being replayed.
TEAM_BASELINE = 0.65

PAIRS = [("Alex", "Jamie"), ("Alex", "Morgan"), ("Taylor", "Jamie")]


@dataclass(frozen=True)
class Rules:
    window: int = 10               # most recent N pair passes
    prior_weight: int = 10         # Beta prior strength (alpha) for smoothing
    min_attempts: int = 3          # below this: INSUFFICIENT_EVIDENCE
    potential_margin: float = 0.03 # smoothed rate must beat baseline by this to be POTENTIAL (reduces flicker)
    super_min_attempts: int = 8
    super_margin: float = 0.07     # smoothed rate must be >= baseline + margin
    super_min_progressive: int = 2
    super_min_chances: int = 1
    cooldown_events: int = 3       # pair passes to hold COOLING_DOWN before downgrading


R = Rules()

INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
NORMAL = "NORMAL"
POTENTIAL = "POTENTIAL_LINK"
SUPER = "SUPER_LINK"
COOLING = "COOLING_DOWN"

BUFF_STYLE = {  # emoji, chart colour
    INSUFFICIENT: ("⚪", "#9aa0a6"),
    NORMAL: ("🔵", "#4c78a8"),
    POTENTIAL: ("🟡", "#f2b134"),
    SUPER: ("🟢", "#2ca02c"),
    COOLING: ("🟠", "#e4572e"),
}
