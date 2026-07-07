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


class TeamStatsSchema(BaseModel):
    avg_goals: float
    avg_conceded: float
    n_matches: int
    matches: list[MatchResultSchema]
    h2h_avg_goals: float | None = None


class ProbabilitySchema(BaseModel):
    team1_win_90: float
    draw_90: float
    team2_win_90: float
    team1_win_et: float
    team2_win_et: float
    team1_win_pen: float
    team2_win_pen: float
    team1_total: float
    team2_total: float
    exp_t1: float
    exp_t2: float


class StatsResponse(BaseModel):
    local_team: str
    visitor_team: str
    local_team_stats: TeamStatsSchema
    visitor_team_stats: TeamStatsSchema
    h2h_matches: list[MatchResultSchema]
    probabilities: ProbabilitySchema


class ErrorResponse(BaseModel):
    detail: str
