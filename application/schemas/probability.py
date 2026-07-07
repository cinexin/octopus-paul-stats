from pydantic import BaseModel


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
