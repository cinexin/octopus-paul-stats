import sys
from unittest.mock import patch, MagicMock

import pytest

from application.cli import (
    compute_h2h,
    print_header,
    print_stats,
    print_recent_matches,
    print_h2h,
    print_probabilities,
    print_usage,
    main,
)
from domain.models.match_result import MatchResult
from domain.models.team_stats import TeamStats


class TestComputeH2H:
    def test_h2h_found(self, sample_team_stats):
        t1_avg, t2_avg = compute_h2h(sample_team_stats, 'Spain', 'France')
        assert t1_avg is not None
        assert t2_avg is not None

    def test_h2h_not_found(self, sample_team_stats):
        t1_avg, t2_avg = compute_h2h(sample_team_stats, 'Spain', 'Atlantis')
        assert t1_avg is None
        assert t2_avg is None

    def test_h2h_single_match(self):
        stats = TeamStats(avg_goals=1.0, avg_conceded=1.0, n_matches=1, matches=[
            MatchResult(home_team='Spain', away_team='France', home_goals=3, away_goals=0, date_str='01.06.2026'),
        ])
        t1_avg, t2_avg = compute_h2h(stats, 'Spain', 'France')
        assert t1_avg == 3.0
        assert t2_avg == 0.0


class TestPrintFunctions:
    def test_print_header(self, capsys):
        print_header('Spain', 'France')
        captured = capsys.readouterr()
        assert 'SPAIN' in captured.out
        assert 'FRANCE' in captured.out

    def test_print_stats(self, capsys, sample_team_stats):
        print_stats('Spain', 'France', sample_team_stats, sample_team_stats)
        captured = capsys.readouterr()
        assert '1.80' in captured.out
        assert '1.00' in captured.out

    def test_print_recent_matches(self, capsys, sample_team_stats):
        print_recent_matches('Spain', 'France', sample_team_stats, sample_team_stats)
        captured = capsys.readouterr()
        assert 'Spain' in captured.out
        assert 'France' in captured.out

    def test_print_h2h_with_matches(self, capsys, sample_matches):
        print_h2h(sample_matches, 'Spain')
        captured = capsys.readouterr()
        assert 'H2H' in captured.out

    def test_print_h2h_empty(self, capsys):
        print_h2h([], 'Spain')
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_print_probabilities(self, capsys, sample_probability_result):
        print_probabilities(sample_probability_result, 'Spain', 'France')
        captured = capsys.readouterr()
        assert '45.0%' in captured.out
        assert '25.0%' in captured.out
        assert '65.0%' in captured.out

    def test_print_usage(self, capsys):
        print_usage()
        captured = capsys.readouterr()
        assert 'octopus-paul-stats' in captured.out


class TestMain:
    @pytest.fixture
    def mock_team_stats_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_stats_service(self):
        return MagicMock()

    def test_no_args_shows_usage(self, mock_team_stats_service, mock_stats_service):
        with patch.object(sys, 'argv', ['main.py']):
            with patch('application.cli.print_usage') as mock_usage:
                main(team_stats_service=mock_team_stats_service, stats_service=mock_stats_service)
                mock_usage.assert_called_once()

    def test_help_flag(self, mock_team_stats_service, mock_stats_service):
        for flag in ['--help', '-h']:
            with patch.object(sys, 'argv', ['main.py', flag]):
                with patch('application.cli.print_usage') as mock_usage:
                    main(team_stats_service=mock_team_stats_service, stats_service=mock_stats_service)
                    mock_usage.assert_called_once()

    def test_service_value_error_handled(self, mock_stats_service):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = ValueError('Team not found')
        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France']):
            with pytest.raises(SystemExit) as exc:
                main(team_stats_service=mock_ts, stats_service=mock_stats_service)
            assert exc.value.code == 1

    def test_service_returns_none_handled(self, mock_stats_service):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.return_value = None
        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France']):
            with pytest.raises(SystemExit) as exc:
                main(team_stats_service=mock_ts, stats_service=mock_stats_service)
            assert exc.value.code == 1

    def test_invalid_n_matches_defaults(self, sample_team_stats, sample_probability_result):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = MagicMock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result
        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France', 'notanumber']):
            main(team_stats_service=mock_ts, stats_service=mock_ss)

    def test_single_argument_shows_usage(self, mock_team_stats_service, mock_stats_service):
        with patch.object(sys, 'argv', ['main.py', 'Spain']):
            with patch('application.cli.print_usage') as mock_usage:
                with pytest.raises(SystemExit):
                    main(team_stats_service=mock_team_stats_service, stats_service=mock_stats_service)
                mock_usage.assert_called_once()

    def test_successful_execution(self, sample_team_stats, sample_probability_result):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = [sample_team_stats, sample_team_stats]
        mock_ss = MagicMock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result
        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France']):
            with patch('application.cli.print_header'):
                with patch('application.cli.print_stats'):
                    with patch('application.cli.print_recent_matches'):
                        with patch('application.cli.print_h2h'):
                            with patch('application.cli.print_probabilities'):
                                main(team_stats_service=mock_ts, stats_service=mock_ss)

        assert mock_ts.get_team_stats.call_count == 2
        mock_ss.calculate_probabilities.assert_called_once()
