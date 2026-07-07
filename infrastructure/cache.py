import json
import logging
from datetime import datetime

try:
    import redis as redis_lib

    _redis_available = True
except ImportError:
    _redis_available = False

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 3600
_REDIS_URL = 'redis://localhost:6379/0'


class _MatchCache:
    def __init__(self):
        self._client = None
        if _redis_available:
            try:
                self._client = redis_lib.from_url(
                    _REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                self._client.ping()
                logger.info('Redis connected at %s', _REDIS_URL)
            except Exception as e:
                logger.warning('Redis unavailable, cache disabled: %s', e)
                self._client = None

    @property
    def enabled(self):
        return self._client is not None

    def get(self, key):
        if not self._client:
            return None
        try:
            data = self._client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error('Cache get error for key %s: %s', key, e)
            return None

    def set(self, key, value, ttl=_DEFAULT_TTL):
        if not self._client:
            return
        try:
            self._client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error('Cache set error for key %s: %s', key, e)

    def clear(self, key):
        if not self._client:
            return
        try:
            self._client.delete(key)
        except Exception as e:
            logger.error('Cache clear error for key %s: %s', key, e)


cache = _MatchCache()


def _latest_match_date(matches):
    dates = []
    for m in matches:
        try:
            dates.append(datetime.strptime(m.get('date_str', ''), '%d.%m.%Y'))
        except (ValueError, TypeError):
            continue
    return max(dates) if dates else None


def cache_key(team_url, tournament_filter):
    norm_url = team_url.strip('/').replace('/', '_')
    filter_part = normalize_filter(tournament_filter)
    return f'team_matches:{norm_url}:{filter_part}'


def normalize_filter(f):
    return f.lower().replace(' ', '_').replace('-', '_')


def is_cache_fresh(cached_data):
    cached_at = cached_data.get('cached_at')
    matches = cached_data.get('matches', [])
    if not cached_at or not matches:
        return False
    latest = _latest_match_date(matches)
    if latest is None:
        return False
    return latest < datetime.now()
