from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from infrastructure.cache import (
    cache_key,
    is_cache_fresh,
    _latest_match_date,
    normalize_filter,
)


class TestCacheHelpers:
    def test_cache_key_format(self):
        key = cache_key('/team/spain/', 'Final tournament')
        assert key.startswith('team_matches:')
        assert 'spain' in key
        assert 'final_tournament' in key

    def test_cache_key_strips_slashes(self):
        key = cache_key('//team/spain//', 'Final tournament')
        assert 'team_spain' in key

    def test_normalize_filter(self):
        assert normalize_filter('Final tournament') == 'final_tournament'
        assert normalize_filter('World Cup') == 'world_cup'

    def test_latest_match_date(self):
        matches = [
            {'date_str': '01.06.2026'},
            {'date_str': '15.06.2026'},
            {'date_str': '10.06.2026'},
        ]
        latest = _latest_match_date(matches)
        assert latest == datetime(2026, 6, 15)

    def test_latest_match_date_empty(self):
        assert _latest_match_date([]) is None

    def test_latest_match_date_invalid_dates(self):
        matches = [
            {'date_str': 'invalid'},
            {'date_str': ''},
        ]
        assert _latest_match_date(matches) is None

    def test_latest_match_date_mixed_validity(self):
        matches = [
            {'date_str': 'invalid'},
            {'date_str': '10.06.2026'},
        ]
        latest = _latest_match_date(matches)
        assert latest == datetime(2026, 6, 10)

    def test_is_cache_fresh_no_matches(self):
        data = {'cached_at': '2026-07-07T12:00:00', 'matches': []}
        assert is_cache_fresh(data) is False

    def test_is_cache_fresh_no_cached_at(self):
        data = {'matches': [{'date_str': '01.06.2026'}]}
        assert is_cache_fresh(data) is False

    def test_is_cache_fresh_recent(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
        data = {
            'cached_at': '2026-07-07T12:00:00',
            'matches': [{'date_str': yesterday}],
        }
        assert is_cache_fresh(data) is True

    def test_is_cache_fresh_future_match(self):
        future = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
        data = {
            'cached_at': '2026-07-07T12:00:00',
            'matches': [{'date_str': future}],
        }
        assert is_cache_fresh(data) is False
