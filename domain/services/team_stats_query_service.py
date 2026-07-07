from abc import ABC, abstractmethod

from domain.models.team_stats import TeamStats


class TeamStatsService(ABC):

    @abstractmethod
    def get_team_stats(self, team_name: str, n_matches: int) -> TeamStats | None:
        ...
