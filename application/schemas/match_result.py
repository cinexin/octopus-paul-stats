from pydantic import BaseModel


class MatchResultSchema(BaseModel):
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    date_str: str
    stage: str = ''
    round_name: str = ''
    tournament: str = ''
