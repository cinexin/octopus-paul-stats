from dataclasses import dataclass


@dataclass
class MatchResult:
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    date_str: str = ''
    stage: str = ''
    round_name: str = ''
    detail_url: str = ''
    tournament: str = ''
