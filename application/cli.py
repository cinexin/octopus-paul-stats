import logging
import sys

from injection import inject, Provide

from application.constants import (
    DEFAULT_N_MATCHES, SEPARATOR_WIDTH, RECENT_MATCHES_DISPLAY,
    MIN_ARGS_TEAMS, ARG_INDEX_N_MATCHES,
)
from application.container import AppContainer
from domain.models.team_stats import TeamStats
from domain.services.stats_computation_service import StatsComputationService
from domain.services.team_stats_query_service import TeamStatsService

logger = logging.getLogger(__name__)
from infrastructure.betexplorer_repository import resolve_team_name
from utils import normalize


def compute_h2h(stats, team1_name, team2_name):
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


def print_header(team1_name, team2_name):
    print("=" * SEPARATOR_WIDTH)
    print(f"  {team1_name.upper()} vs {team2_name.upper()} - ANÁLISIS DE PROBABILIDADES")
    print("=" * SEPARATOR_WIDTH)


def print_stats(team1_name, team2_name, stats1, stats2):
    print(f"\n📊 ESTADÍSTICAS EXTRAÍDAS (BetExplorer):")
    print(f"  {team1_name}:   {stats1.avg_goals:.2f} goles a favor, {stats1.avg_conceded:.2f} en contra ({stats1.n_matches} partidos)")
    print(f"  {team2_name}:  {stats2.avg_goals:.2f} goles a favor, {stats2.avg_conceded:.2f} en contra ({stats2.n_matches} partidos)")


def print_recent_matches(team1_name, team2_name, stats1, stats2):
    print(f"\n📋 PARTIDOS RECIENTES:")
    print(f"  {team1_name}:")
    for m in stats1.matches[:RECENT_MATCHES_DISPLAY]:
        score = f"{m.home_goals}-{m.away_goals}"
        print(f"    {m.home_team:20} {score:>5} {m.away_team:20} ({m.date_str})")
    print(f"  {team2_name}:")
    for m in stats2.matches[:RECENT_MATCHES_DISPLAY]:
        score = f"{m.home_goals}-{m.away_goals}"
        print(f"    {m.home_team:20} {score:>5} {m.away_team:20} ({m.date_str})")


def print_h2h(h2h_matches, team1_name):
    if not h2h_matches:
        return
    print(f"\n🤝 H2H ({team1_name} vs {h2h_matches[0].away_team if normalize(h2h_matches[0].home_team) == resolve_team_name(team1_name) else h2h_matches[0].home_team}):")
    for m in h2h_matches:
        score = f"{m.home_goals}-{m.away_goals}"
        print(f"    {m.home_team:20} {score:>5} {m.away_team:20} ({m.date_str})")


def print_probabilities(probs, team1_name, team2_name):
    print(f"\n🔮 GOLES ESPERADOS (Poisson):")
    print(f"  {team1_name}:   {probs.exp_t1:.2f} goles esperados")
    print(f"  {team2_name}:  {probs.exp_t2:.2f} goles esperados")

    print(f"\n🏆 PROBABILIDADES TIEMPO REGULAR (90'):")
    print(f"  Victoria {team1_name}:   {probs.team1_win_90*100:.1f}%")
    print(f"  Empate:                {probs.draw_90*100:.1f}%")
    print(f"  Victoria {team2_name}:  {probs.team2_win_90*100:.1f}%")

    print(f"\n⏱️  PRÓRROGA (tras empate en 90'):")
    print(f"  {team1_name} gana en prórroga: {probs.team1_win_et*100:.1f}%")
    print(f"  {team2_name} gana en prórroga: {probs.team2_win_et*100:.1f}%")

    print(f"\n⚽ PENALTIS (tras empate en 120'):")
    print(f"  {team1_name} gana en penaltis:  {probs.team1_win_pen*100:.1f}%")
    print(f"  {team2_name} gana en penaltis: {probs.team2_win_pen*100:.1f}%")

    print(f"\n📈 PROBABILIDAD TOTAL:")
    print(f"  {team1_name}:   {probs.team1_total*100:.1f}%")
    print(f"  {team2_name}:  {probs.team2_total*100:.1f}%")

    print(f"\n📋 DESGLOSE COMPLETO:")
    print(f"  {'Resultado':<30} {'Probabilidad':<15}")
    print(f"  {'-'*45}")
    labels = [
        (f"{team1_name} gana en 90'", probs.team1_win_90),
        (f"{team1_name} gana en prórroga", probs.team1_win_et),
        (f"{team1_name} gana en penaltis", probs.team1_win_pen),
        (f"{team2_name} gana en 90'", probs.team2_win_90),
        (f"{team2_name} gana en prórroga", probs.team2_win_et),
        (f"{team2_name} gana en penaltis", probs.team2_win_pen),
    ]
    for label, prob in labels:
        print(f"  {label:<30} {prob*100:>6.1f}%")


def print_usage():
    print("Uso: octopus-paul-stats [equipo1] [equipo2] [num_partidos]")
    print("  equipo1       Nombre del primer equipo (default: Spain)")
    print("  equipo2       Nombre del segundo equipo (default: Belgium)")
    print("  num_partidos  Partidos recientes a analizar (default: 5)")
    print("  --help, -h    Muestra esta ayuda")
    print()
    print("Ejemplos:")
    print("  octopus-paul-stats")
    print('  octopus-paul-stats "Argentina" "Brasil"')
    print('  octopus-paul-stats "Francia" "Inglaterra" 10')


@inject
def main(
    team_stats_service: TeamStatsService = Provide[AppContainer.team_stats_service],
    stats_service: StatsComputationService = Provide[AppContainer.stats_service],
):
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print_usage()
        return

    if len(args) >= MIN_ARGS_TEAMS:
        team1_name = resolve_team_name(args[0])
        team2_name = resolve_team_name(args[1])
    else:
        print_usage()
        sys.exit(1)

    n_matches = DEFAULT_N_MATCHES
    if len(args) >= ARG_INDEX_N_MATCHES + 1:
        try:
            n_matches = int(args[ARG_INDEX_N_MATCHES])
        except ValueError as e:
            logger.error('Invalid n_matches argument "%s": %s', args[ARG_INDEX_N_MATCHES], e)

    print(f"Obteniendo datos de {team1_name} y {team2_name} desde BetExplorer...")
    try:
        t1_stats = team_stats_service.get_team_stats(team1_name, n_matches=n_matches)
        t2_stats = team_stats_service.get_team_stats(team2_name, n_matches=n_matches)
    except ValueError as e:
        logger.error('Team stats error: %s', e)
        print(f"Error: {e}")
        sys.exit(1)

    if t1_stats is None or t2_stats is None:
        print("Error: No se pudieron obtener estadísticas de uno o ambos equipos.")
        sys.exit(1)

    t1_h2h_avg, t2_h2h_avg = compute_h2h(t1_stats, team1_name, team2_name)

    t1_h2h_matches = [m for m in t1_stats.matches
                      if normalize(m.home_team) == resolve_team_name(team2_name)
                      or normalize(m.away_team) == resolve_team_name(team2_name)]

    t1_stats = TeamStats(
        avg_goals=t1_stats.avg_goals,
        avg_conceded=t1_stats.avg_conceded,
        n_matches=t1_stats.n_matches,
        matches=t1_stats.matches,
        h2h_avg_goals=t1_h2h_avg,
    )
    t2_stats = TeamStats(
        avg_goals=t2_stats.avg_goals,
        avg_conceded=t2_stats.avg_conceded,
        n_matches=t2_stats.n_matches,
        matches=t2_stats.matches,
        h2h_avg_goals=t2_h2h_avg,
    )

    print_header(team1_name, team2_name)
    print_stats(team1_name, team2_name, t1_stats, t2_stats)
    print_recent_matches(team1_name, team2_name, t1_stats, t2_stats)
    print_h2h(t1_h2h_matches, team1_name)

    probs = stats_service.calculate_probabilities(t1_stats, t2_stats)
    print_probabilities(probs, team1_name, team2_name)
