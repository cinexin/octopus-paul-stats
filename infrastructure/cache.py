import json
import logging
from datetime import datetime

try:
    import redis as redis_lib

    _redis_available = True
except ImportError as e:
    _redis_available = False
    _redis_import_error = str(e)

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 3600
_REDIS_URL = 'redis://localhost:6379/0'


class _MatchCache:
    def __init__(self):
        self._client = None
        self._status_logged = False
        self._connect()

    def _connect(self):
        if not _redis_available:
            return
        try:
            client = redis_lib.from_url(
                _REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            client.ping()
            self._client = client
        except Exception as e:
            self._client = None

    _status_logged = False

    def _ensure_connected(self):
        if self._client is not None:
            return True
        if self._status_logged:
            return False
        self._connect()
        self._status_logged = True
        if self._client is not None:
            logger.info('Caché Redis activo en %s', _REDIS_URL)
        else:
            logger.warning('Redis no disponible — las estadísticas se obtendrán de BetExplorer sin caché')
        return self._client is not None

    @property
    def enabled(self):
        return self._client is not None

    def get(self, key):
        if not self._ensure_connected():
            return None
        try:
            data = self._client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error('Cache get error for key %s: %s', key, e)
            self._client = None
            return None

    def set(self, key, value, ttl=_DEFAULT_TTL):
        if not self._ensure_connected():
            return
        try:
            self._client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error('Cache set error for key %s: %s', key, e)
            self._client = None

    def clear(self, key):
        if not self._ensure_connected():
            return
        try:
            self._client.delete(key)
        except Exception as e:
            logger.error('Cache clear error for key %s: %s', key, e)
            self._client = None


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
