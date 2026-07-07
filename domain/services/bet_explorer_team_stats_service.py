from domain.models.team_stats import TeamStats
from domain.services.team_stats_query_service import TeamStatsService
from infrastructure.betexplorer_repository import BetExplorerRepository, resolve_team_name
from utils import normalize


class BetExplorerTeamStatsService(TeamStatsService):

    def __init__(self, repo: BetExplorerRepository):
        self._repo = repo

    def get_team_stats(self, team_name, n_matches):
        team_url = self._repo.find_team_url(team_name)
        if not team_url:
            raise ValueError(f'Team "{team_name}" not found in World Cup 2026')

        matches = self._repo.get_team_matches(team_url)

        if not matches:
            return None

        recent = matches[:min(n_matches, len(matches))]

        scores = []
        conceded = []

        team_name_norm = resolve_team_name(team_name)
        for m in recent:
            if normalize(m.home_team) == team_name_norm:
                scores.append(m.home_goals)
                conceded.append(m.away_goals)
            else:
                scores.append(m.away_goals)
                conceded.append(m.home_goals)

        n = len(scores)
        if n == 0:
            return None

        return TeamStats(
            avg_goals=sum(scores) / n,
            avg_conceded=sum(conceded) / n,
            n_matches=n,
            matches=recent,
        )
