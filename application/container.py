from injection import DeclarativeContainer, providers

from domain.services.bet_explorer_team_stats_service import BetExplorerTeamStatsService
from domain.services.poisson_stats_service import PoissonStatsService
from infrastructure.betexplorer_repository import BetExplorerRepository


class AppContainer(DeclarativeContainer):
    stats_service = providers.Singleton(PoissonStatsService)
    repo = providers.Singleton(BetExplorerRepository)
    team_stats_service = providers.Singleton(
        BetExplorerTeamStatsService,
        repo=repo,
    )
