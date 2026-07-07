from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from infrastructure.cache import cache, _MatchCache
from infrastructure.betexplorer_repository import BetExplorerRepository


class TestRedisCache:
    def setup_method(self):
        self.repo = BetExplorerRepository()

    def test_cache_disabled_when_redis_unavailable(self):
        with patch('infrastructure.cache._redis_available', False):
            c = _MatchCache()
            assert c.enabled is False
            assert c.get('some_key') is None
            c.set('some_key', {'data': 1})
            c.clear('some_key')

    def test_cache_get_set(self):
        c = _MatchCache()
        c._client = MagicMock()
        c._client.ping.return_value = True

        import json
        c._client.get.return_value = json.dumps({'foo': 'bar'})
        result = c.get('test_key')
        assert result == {'foo': 'bar'}
        c._client.get.assert_called_with('test_key')

    def test_cache_get_miss(self):
        c = _MatchCache()
        c._client = MagicMock()
        c._client.get.return_value = None
        result = c.get('missing_key')
        assert result is None

    def test_cache_set_calls_setex(self):
        c = _MatchCache()
        c._client = MagicMock()
        c.set('my_key', {'value': 42}, ttl=3600)
        c._client.setex.assert_called_once()

    def test_cache_clear_calls_delete(self):
        c = _MatchCache()
        c._client = MagicMock()
        c.clear('my_key')
        c._client.delete.assert_called_with('my_key')

    def test_cache_get_error_logged(self):
        c = _MatchCache()
        c._client = MagicMock()
        c._client.get.side_effect = Exception('Redis error')
        with patch('infrastructure.cache.logger.error') as mock_log:
            result = c.get('key')
            assert result is None
            mock_log.assert_called_once()

    def test_cache_set_error_logged(self):
        c = _MatchCache()
        c._client = MagicMock()
        c._client.setex.side_effect = Exception('Redis error')
        with patch('infrastructure.cache.logger.error') as mock_log:
            c.set('key', {})
            mock_log.assert_called_once()

    def test_cache_clear_error_logged(self):
        c = _MatchCache()
        c._client = MagicMock()
        c._client.delete.side_effect = Exception('Redis error')
        with patch('infrastructure.cache.logger.error') as mock_log:
            c.clear('key')
            mock_log.assert_called_once()


class TestRepositoryWithCache:
    def setup_method(self):
        self.repo = BetExplorerRepository()

    def test_get_team_matches_cache_hit_and_fresh(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'
        ck = 'team_matches:team_spain:final_tournament'

        with patch('infrastructure.betexplorer_repository.cache') as mock_cache:
            mock_cache.get.return_value = {
                'matches': [
                    {
                        'home_team': 'Spain',
                        'away_team': 'France',
                        'home_goals': 2,
                        'away_goals': 1,
                        'date_str': '01.06.2026',
                        'round_name': 'Group stage',
                        'detail_url': '',
                        'tournament': 'World Championship 2026 - Final tournament',
                    },
                ],
                'cached_at': '2026-07-07T12:00:00',
            }
            from infrastructure.cache import is_cache_fresh
            original_fresh = is_cache_fresh

            def mock_fresh(data):
                return True

            with patch('infrastructure.betexplorer_repository.is_cache_fresh', side_effect=mock_fresh):
                matches = self.repo.get_team_matches('/team/spain/')

        assert len(matches) == 1
        assert matches[0].home_team == 'Spain'

    def test_get_team_matches_cache_miss_fetches(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'
        ck = 'team_matches:team_spain:final_tournament'

        mock_resp = MagicMock()
        mock_resp.text = mock_team_page_html
        mock_resp.raise_for_status = MagicMock()

        with patch('infrastructure.betexplorer_repository.cache') as mock_cache:
            mock_cache.get.return_value = None
            with patch.object(self.repo.session, 'get', return_value=mock_resp):
                matches = self.repo.get_team_matches('/team/spain/')

        assert len(matches) == 2
        mock_cache.set.assert_called_once()

    def test_get_team_matches_cache_stale_refetches(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'

        mock_resp = MagicMock()
        mock_resp.text = mock_team_page_html
        mock_resp.raise_for_status = MagicMock()

        with patch('infrastructure.betexplorer_repository.cache') as mock_cache:
            mock_cache.get.return_value = {
                'matches': [
                    {
                        'home_team': 'Spain',
                        'away_team': 'France',
                        'home_goals': 2,
                        'away_goals': 1,
                        'date_str': '01.06.2026',
                        'round_name': 'Group stage',
                        'detail_url': '',
                        'tournament': 'World Championship 2026 - Final tournament',
                    },
                ],
                'cached_at': '2026-07-07T12:00:00',
            }
            with patch('infrastructure.betexplorer_repository.is_cache_fresh', return_value=False):
                with patch.object(self.repo.session, 'get', return_value=mock_resp):
                    matches = self.repo.get_team_matches('/team/spain/')

        assert len(matches) == 2
        mock_cache.set.assert_called_once()
