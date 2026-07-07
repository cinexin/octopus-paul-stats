from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TeamStats:
    avg_goals: float
    avg_conceded: float
    n_matches: int
    matches: list = field(default_factory=list)
    h2h_avg_goals: Optional[float] = None
