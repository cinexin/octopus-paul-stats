from domain.models.match_result import MatchResult
from domain.models.probability_result import ProbabilityResult
from domain.models.team_stats import TeamStats


class TestMatchResult:
    def test_create_match_result(self):
        m = MatchResult(
            home_team='Spain',
            away_team='France',
            home_goals=2,
            away_goals=1,
            date_str='01.06.2026',
        )
        assert m.home_team == 'Spain'
        assert m.away_team == 'France'
        assert m.home_goals == 2
        assert m.away_goals == 1
        assert m.date_str == '01.06.2026'

    def test_default_values(self):
        m = MatchResult(home_team='A', away_team='B', home_goals=0, away_goals=0)
        assert m.date_str == ''
        assert m.stage == ''
        assert m.round_name == ''
        assert m.detail_url == ''
        assert m.tournament == ''


class TestTeamStats:
    def test_create_team_stats(self):
        ts = TeamStats(avg_goals=1.5, avg_conceded=0.8, n_matches=10)
        assert ts.avg_goals == 1.5
        assert ts.avg_conceded == 0.8
        assert ts.n_matches == 10
        assert ts.matches == []
        assert ts.h2h_avg_goals is None

    def test_with_matches_and_h2h(self):
        ts = TeamStats(
            avg_goals=2.0,
            avg_conceded=1.0,
            n_matches=5,
            matches=[1, 2, 3],
            h2h_avg_goals=1.5,
        )
        assert len(ts.matches) == 3
        assert ts.h2h_avg_goals == 1.5


class TestProbabilityResult:
    def test_all_fields(self):
        pr = ProbabilityResult(
            team1_win_90=0.4,
            draw_90=0.3,
            team2_win_90=0.3,
            team1_win_et=0.06,
            team2_win_et=0.06,
            team1_win_pen=0.18,
            team2_win_pen=0.12,
            team1_total=0.64,
            team2_total=0.48,
            exp_t1=1.5,
            exp_t2=1.2,
        )
        assert abs(pr.team1_total - (0.4 + 0.06 + 0.18)) < 1e-10
        assert abs(pr.team2_total - (0.3 + 0.06 + 0.12)) < 1e-10
