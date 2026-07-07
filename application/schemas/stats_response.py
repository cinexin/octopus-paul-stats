from pydantic import BaseModel

from application.schemas.match_result import MatchResultSchema
from application.schemas.team_stats import TeamStatsSchema
from application.schemas.probability import ProbabilitySchema


class StatsResponse(BaseModel):
    local_team: str
    visitor_team: str
    local_team_stats: TeamStatsSchema
    visitor_team_stats: TeamStatsSchema
    h2h_matches: list[MatchResultSchema]
    probabilities: ProbabilitySchema
