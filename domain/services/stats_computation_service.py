from abc import ABC, abstractmethod

from domain.models.probability_result import ProbabilityResult
from domain.models.team_stats import TeamStats


class StatsComputationService(ABC):

    @abstractmethod
    def calculate_probabilities(self, team1_stats: TeamStats, team2_stats: TeamStats) -> ProbabilityResult:
        ...
