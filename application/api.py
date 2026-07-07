import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from application.container import AppContainer
from application.schemas import (
    ErrorResponse,
    MatchResultSchema,
    ProbabilitySchema,
    StatsResponse,
    TeamStatsSchema,
)
from domain.models.team_stats import TeamStats
from infrastructure.betexplorer_repository import resolve_team_name
from utils import normalize

logger = logging.getLogger(__name__)

_container = AppContainer()


def _compute_h2h(stats, team1_name, team2_name):
    matches = stats.matches
    h2h = [m for m in matches
           if normalize(m.home_team) == resolve_team_name(team2_name)
           or normalize(m.away_team) == resolve_team_name(team2_name)]
    if not h2h:
        return None, None

    t1_goals = []
    t2_goals = []
    for m in h2h:
        if normalize(m.home_team) == resolve_team_name(team1_name):
            t1_goals.append(m.home_goals)
            t2_goals.append(m.away_goals)
        else:
            t1_goals.append(m.away_goals)
            t2_goals.append(m.home_goals)

    t1_avg = sum(t1_goals) / len(t1_goals) if t1_goals else None
    t2_avg = sum(t2_goals) / len(t2_goals) if t2_goals else None
    return t1_avg, t2_avg


_FAVICON_PATH = Path(__file__).parent / 'static' / 'favicon.svg'

app = FastAPI(
    title='Octopus Paul Stats API',
    description='Calcula probabilidades de partidos de fútbol usando distribución de Poisson con datos extraídos de BetExplorer.',
    version='1.0.0',
)


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(_FAVICON_PATH)


@app.get(
    '/stats',
    response_model=StatsResponse,
    responses={404: {'model': ErrorResponse}, 422: {'model': ErrorResponse}},
    summary='Obtener estadísticas y probabilidades',
    description='Dados dos equipos (local y visitante), devuelve estadísticas recientes, enfrentamientos directos y probabilidades calculadas con Poisson.',
)
def get_stats(
    local: str = Query(..., description='Nombre del equipo local'),
    visitor: str = Query(..., description='Nombre del equipo visitante'),
    n_matches: int = Query(5, description='Número de partidos recientes a analizar'),
):
    if n_matches < 1:
        raise HTTPException(status_code=422, detail='n_matches debe ser mayor o igual a 1')

    team_stats_service = _container.team_stats_service()
    stats_service = _container.stats_service()

    local_resolved = resolve_team_name(local)
    visitor_resolved = resolve_team_name(visitor)

    try:
        t1_stats = team_stats_service.get_team_stats(local_resolved, n_matches=n_matches)
        t2_stats = team_stats_service.get_team_stats(visitor_resolved, n_matches=n_matches)
    except ValueError as e:
        logger.error('Team stats error: %s', e)
        raise HTTPException(status_code=404, detail=str(e))

    if t1_stats is None or t2_stats is None:
        raise HTTPException(
            status_code=404,
            detail='No se pudieron obtener estadísticas de uno o ambos equipos.',
        )

    t1_h2h_avg, t2_h2h_avg = _compute_h2h(t1_stats, local_resolved, visitor_resolved)

    h2h_matches = [
        MatchResultSchema(
            home_team=m.home_team,
            away_team=m.away_team,
            home_goals=m.home_goals,
            away_goals=m.away_goals,
            date_str=m.date_str,
            stage=m.stage,
            round_name=m.round_name,
            tournament=m.tournament,
        )
        for m in t1_stats.matches
        if normalize(m.home_team) == resolve_team_name(visitor_resolved)
        or normalize(m.away_team) == resolve_team_name(visitor_resolved)
    ]

    t1_stats_with_h2h = TeamStats(
        avg_goals=t1_stats.avg_goals,
        avg_conceded=t1_stats.avg_conceded,
        n_matches=t1_stats.n_matches,
        matches=t1_stats.matches,
        h2h_avg_goals=t1_h2h_avg,
    )
    t2_stats_with_h2h = TeamStats(
        avg_goals=t2_stats.avg_goals,
        avg_conceded=t2_stats.avg_conceded,
        n_matches=t2_stats.n_matches,
        matches=t2_stats.matches,
        h2h_avg_goals=t2_h2h_avg,
    )

    probs = stats_service.calculate_probabilities(t1_stats_with_h2h, t2_stats_with_h2h)

    def _match_to_schema(m):
        return MatchResultSchema(
            home_team=m.home_team,
            away_team=m.away_team,
            home_goals=m.home_goals,
            away_goals=m.away_goals,
            date_str=m.date_str,
            stage=m.stage,
            round_name=m.round_name,
            tournament=m.tournament,
        )

    return StatsResponse(
        local_team=local_resolved,
        visitor_team=visitor_resolved,
        local_team_stats=TeamStatsSchema(
            avg_goals=t1_stats.avg_goals,
            avg_conceded=t1_stats.avg_conceded,
            n_matches=t1_stats.n_matches,
            matches=[_match_to_schema(m) for m in t1_stats.matches],
            h2h_avg_goals=t1_h2h_avg,
        ),
        visitor_team_stats=TeamStatsSchema(
            avg_goals=t2_stats.avg_goals,
            avg_conceded=t2_stats.avg_conceded,
            n_matches=t2_stats.n_matches,
            matches=[_match_to_schema(m) for m in t2_stats.matches],
            h2h_avg_goals=t2_h2h_avg,
        ),
        h2h_matches=h2h_matches,
        probabilities=ProbabilitySchema(
            team1_win_90=probs.team1_win_90,
            draw_90=probs.draw_90,
            team2_win_90=probs.team2_win_90,
            team1_win_et=probs.team1_win_et,
            team2_win_et=probs.team2_win_et,
            team1_win_pen=probs.team1_win_pen,
            team2_win_pen=probs.team2_win_pen,
            team1_total=probs.team1_total,
            team2_total=probs.team2_total,
            exp_t1=probs.exp_t1,
            exp_t2=probs.exp_t2,
        ),
    )
