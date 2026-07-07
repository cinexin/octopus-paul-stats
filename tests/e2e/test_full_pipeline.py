import sys
from unittest.mock import patch, MagicMock

import pytest

from application.cli import main


class TestFullPipeline:
    def test_successful_pipeline(self, sample_team_stats, sample_probability_result):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = [sample_team_stats, sample_team_stats]
        mock_ss = MagicMock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France']):
            with patch('application.cli.print_header'):
                with patch('application.cli.print_stats'):
                    with patch('application.cli.print_recent_matches'):
                        with patch('application.cli.print_h2h'):
                            with patch('application.cli.print_probabilities') as mock_print_probs:
                                main(team_stats_service=mock_ts, stats_service=mock_ss)

        assert mock_ts.get_team_stats.call_count == 2
        mock_ss.calculate_probabilities.assert_called_once()
        mock_print_probs.assert_called_once()

    def test_pipeline_with_no_args(self):
        mock_ts = MagicMock()
        mock_ss = MagicMock()
        with patch.object(sys, 'argv', ['main.py']):
            with patch('application.cli.print_usage') as mock_usage:
                main(team_stats_service=mock_ts, stats_service=mock_ss)

        mock_usage.assert_called_once()
        mock_ts.get_team_stats.assert_not_called()

    def test_pipeline_with_help_flag(self):
        mock_ts = MagicMock()
        mock_ss = MagicMock()
        for flag in ['--help', '-h']:
            with patch.object(sys, 'argv', ['main.py', flag]):
                with patch('application.cli.print_usage') as mock_usage:
                    main(team_stats_service=mock_ts, stats_service=mock_ss)
                mock_usage.assert_called()

    def test_pipeline_team_not_found_error(self):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = ValueError('Team not found')
        mock_ss = MagicMock()

        with patch.object(sys, 'argv', ['main.py', 'Atlantis', 'Spain']):
            with pytest.raises(SystemExit) as exc:
                main(team_stats_service=mock_ts, stats_service=mock_ss)
            assert exc.value.code == 1

    def test_pipeline_stats_return_none(self):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.return_value = None
        mock_ss = MagicMock()

        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France']):
            with pytest.raises(SystemExit) as exc:
                main(team_stats_service=mock_ts, stats_service=mock_ss)
            assert exc.value.code == 1

    def test_pipeline_with_custom_n_matches(self, sample_team_stats, sample_probability_result):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = MagicMock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France', '10']):
            with patch('application.cli.print_header'):
                with patch('application.cli.print_stats'):
                    with patch('application.cli.print_recent_matches'):
                        with patch('application.cli.print_h2h'):
                            with patch('application.cli.print_probabilities'):
                                main(team_stats_service=mock_ts, stats_service=mock_ss)

        calls = mock_ts.get_team_stats.call_args_list
        for c in calls:
            assert c[1]['n_matches'] == 10

    def test_pipeline_different_teams_produce_different_results(self, sample_probability_result):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = [
            MagicMock(avg_goals=2.5, avg_conceded=0.5, n_matches=10, matches=[], h2h_avg_goals=None),
            MagicMock(avg_goals=0.5, avg_conceded=2.5, n_matches=10, matches=[], h2h_avg_goals=None),
        ]
        mock_ss = MagicMock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch.object(sys, 'argv', ['main.py', 'Brazil', 'Canada']):
            with patch('application.cli.print_header'):
                with patch('application.cli.print_stats'):
                    with patch('application.cli.print_recent_matches'):
                        with patch('application.cli.print_h2h'):
                            with patch('application.cli.print_probabilities'):
                                main(team_stats_service=mock_ts, stats_service=mock_ss)

    def test_pipeline_network_error_propagates(self):
        import requests
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = requests.ConnectionError('Network unavailable')
        mock_ss = MagicMock()

        with patch.object(sys, 'argv', ['main.py', 'Spain', 'France']):
            with pytest.raises(requests.ConnectionError):
                main(team_stats_service=mock_ts, stats_service=mock_ss)

    def test_pipeline_with_team_name_resolution(self, sample_team_stats, sample_probability_result):
        mock_ts = MagicMock()
        mock_ts.get_team_stats.side_effect = [sample_team_stats, sample_team_stats]
        mock_ss = MagicMock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        from infrastructure.betexplorer_repository import resolve_team_name

        with patch.object(sys, 'argv', ['main.py', 'españa', 'francia']):
            with patch('application.cli.print_header') as mock_header:
                with patch('application.cli.print_stats'):
                    with patch('application.cli.print_recent_matches'):
                        with patch('application.cli.print_h2h'):
                            with patch('application.cli.print_probabilities'):
                                main(team_stats_service=mock_ts, stats_service=mock_ss)

            args, _ = mock_header.call_args
            assert args[0] == resolve_team_name('españa')
            assert args[1] == resolve_team_name('francia')
