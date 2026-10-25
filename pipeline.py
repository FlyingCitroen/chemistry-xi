"""The five-stage pipeline from the brief, in one place.
(a) ingest  -> (b) interpret -> (c) explain -> (d) render -> (e) personalize"""
from __future__ import annotations

import chem_engine as engine
import insight
import overlays
import personalize


class MatchPipeline:
    def __init__(self, events):
        # (a) INGEST: events arrive time-ordered; `k` events have 'happened' at any moment of the replay.
        self.events = sorted(events, key=lambda e: (e["minute"], e["second"]))
        self.chem = engine.scan_all(self.events)                       # pair-link states for every pair
        self.tactical = insight.tactical_timeline(self.events)         # control / chaos / pressure / rhythm
        self.moments = insight.detect_moments(self.events, self.tactical, self.chem)   # (c) key moments

    def played(self, k):
        return self.events[:k]

    def interpret(self, k) -> dict:                                    # (b)
        p = self.played(k)
        return {"score": insight.score(p), "possession": insight.possession(p),
                "teams": {t: insight.team_stats(p, t) for t in insight.C.TEAMS},
                "tactical": self.tactical[k]}

    def explain(self, k):                                              # (c)
        return [m for m in self.moments if m.k <= k]

    def personalize(self, k, profile):                                 # (e)
        return personalize.select(self.explain(k), profile)

    def render(self, k, profile, texts=None):                          # (d) timed, machine-readable overlays
        import i18n
        out = []
        for m in self.personalize(k, profile):
            text = (texts or {}).get(m.idx) or i18n.render(m, profile.lang, profile.mode)
            out.append(overlays.overlay(m, profile.lang, profile.mode, text))
        return out
