import pytest
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

from application.api import app
from domain.models.team_stats import TeamStats
from domain.models.match_result import MatchResult
from domain.models.probability_result import ProbabilityResult


@pytest.fixture
def client():
    return TestClient(app)


class TestApiStatsEndpoint:
    def test_returns_stats_successfully(self, client, sample_team_stats, sample_probability_result):
        mock_ts = Mock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = Mock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            with patch('application.api._container.stats_service', return_value=mock_ss):
                response = client.get('/stats', params={'local': 'Spain', 'visitor': 'France'})

        assert response.status_code == 200
        data = response.json()
        assert data['local_team'] == 'spain'
        assert data['visitor_team'] == 'france'
        assert 'local_team_stats' in data
        assert 'visitor_team_stats' in data
        assert 'h2h_matches' in data
        assert 'probabilities' in data
        assert data['probabilities']['team1_win_90'] == sample_probability_result.team1_win_90

    def test_team_not_found_returns_404(self, client):
        mock_ts = Mock()
        mock_ts.get_team_stats.side_effect = ValueError('Team "atlantis" not found in World Cup 2026')

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            response = client.get('/stats', params={'local': 'Atlantis', 'visitor': 'Spain'})

        assert response.status_code == 404
        assert 'not found' in response.json()['detail']

    def test_stats_none_returns_404(self, client):
        mock_ts = Mock()
        mock_ts.get_team_stats.return_value = None

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            response = client.get('/stats', params={'local': 'Spain', 'visitor': 'France'})

        assert response.status_code == 404

    def test_missing_parameters_returns_422(self, client):
        response = client.get('/stats')
        assert response.status_code == 422

        response = client.get('/stats', params={'local': 'Spain'})
        assert response.status_code == 422

    def test_invalid_n_matches_returns_422(self, client):
        response = client.get('/stats', params={'local': 'Spain', 'visitor': 'France', 'n_matches': 0})
        assert response.status_code == 422

        response = client.get('/stats', params={'local': 'Spain', 'visitor': 'France', 'n_matches': -1})
        assert response.status_code == 422

    def test_custom_n_matches_passed_to_service(self, client, sample_team_stats, sample_probability_result):
        mock_ts = Mock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = Mock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            with patch('application.api._container.stats_service', return_value=mock_ss):
                client.get('/stats', params={'local': 'Spain', 'visitor': 'France', 'n_matches': 10})

        calls = mock_ts.get_team_stats.call_args_list
        for c in calls:
            assert c[1]['n_matches'] == 10

    def test_local_team_stats_structure(self, client, sample_team_stats, sample_probability_result):
        mock_ts = Mock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = Mock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            with patch('application.api._container.stats_service', return_value=mock_ss):
                response = client.get('/stats', params={'local': 'Spain', 'visitor': 'France'})

        data = response.json()
        local_stats = data['local_team_stats']
        assert 'avg_goals' in local_stats
        assert 'avg_conceded' in local_stats
        assert 'n_matches' in local_stats
        assert 'matches' in local_stats
        assert 'h2h_avg_goals' in local_stats
        assert len(local_stats['matches']) > 0
        assert 'home_team' in local_stats['matches'][0]
        assert 'away_team' in local_stats['matches'][0]
        assert 'home_goals' in local_stats['matches'][0]
        assert 'away_goals' in local_stats['matches'][0]
        assert 'date_str' in local_stats['matches'][0]

    def test_probabilities_structure(self, client, sample_team_stats, sample_probability_result):
        mock_ts = Mock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = Mock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            with patch('application.api._container.stats_service', return_value=mock_ss):
                response = client.get('/stats', params={'local': 'Spain', 'visitor': 'France'})

        data = response.json()
        probs = data['probabilities']
        assert probs['team1_win_90'] + probs['draw_90'] + probs['team2_win_90'] == pytest.approx(1.0, abs=0.01)
        assert probs['team1_total'] > 0
        assert probs['team2_total'] > 0
        assert probs['exp_t1'] >= 0
        assert probs['exp_t2'] >= 0

    def test_spanish_team_names_resolved(self, client, sample_team_stats, sample_probability_result):
        mock_ts = Mock()
        mock_ts.get_team_stats.return_value = sample_team_stats
        mock_ss = Mock()
        mock_ss.calculate_probabilities.return_value = sample_probability_result

        with patch('application.api._container.team_stats_service', return_value=mock_ts):
            with patch('application.api._container.stats_service', return_value=mock_ss):
                response = client.get('/stats', params={'local': 'españa', 'visitor': 'francia'})

        assert response.status_code == 200
        data = response.json()
        assert data['local_team'] == 'spain'
        assert data['visitor_team'] == 'france'

    def test_swagger_docs_available(self, client):
        response = client.get('/docs')
        assert response.status_code == 200
        assert 'swagger' in response.text.lower() or 'openapi' in response.text.lower()

    def test_openapi_schema(self, client):
        response = client.get('/openapi.json')
        assert response.status_code == 200
        schema = response.json()
        assert '/stats' in schema['paths']
        assert schema['paths']['/stats']['get'] is not None
