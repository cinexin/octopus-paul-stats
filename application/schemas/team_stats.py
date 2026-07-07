from pydantic import BaseModel

from application.schemas.match_result import MatchResultSchema


class TeamStatsSchema(BaseModel):
    avg_goals: float
    avg_conceded: float
    n_matches: int
    matches: list[MatchResultSchema]
    h2h_avg_goals: float | None = None
