import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from domain.models.match_result import MatchResult
from infrastructure.cache import cache, cache_key, is_cache_fresh
from infrastructure.constants import HEADERS, BASE_URL, WC_RESULTS_URL, TEAM_TRANSLATIONS
from utils import normalize

logger = logging.getLogger(__name__)

_NORMALIZED_TO_CANONICAL = {}
for _canonical, _variants in TEAM_TRANSLATIONS.items():
    for _v in _variants:
        _NORMALIZED_TO_CANONICAL[normalize(_v)] = _canonical
    _NORMALIZED_TO_CANONICAL[normalize(_canonical)] = _canonical


def resolve_team_name(name):
    n = normalize(name)
    return _NORMALIZED_TO_CANONICAL.get(n, n)


class BetExplorerRepository:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._team_cache = {}
        self._all_teams = None
        self._all_matches = None

    def _soup(self, url):
        r = self.session.get(url, timeout=30)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')

    def get_all_matches_from_results(self):
        soup = self._soup(WC_RESULTS_URL)
        table = soup.find('table', class_='table-main')
        if not table:
            return []

        matches = []
        current_stage = None
        for tr in table.find_all('tr'):
            th = tr.find('th')
            if th:
                current_stage = th.get_text(strip=True)
                continue

            tds = tr.find_all('td')
            if len(tds) < 2:
                continue

            match_link_a = tds[0].find('a', href=True) if tds[0] else None
            score_a = tds[1].find('a', href=True) if tds[1] else None

            if not match_link_a:
                continue

            match_url = match_link_a['href']
            match_name = match_link_a.get_text(strip=True)
            score_text = (score_a or match_link_a).get_text(strip=True)

            score_match = re.match(r'^(\d+)\s*:\s*(\d+)', score_text)
            home_goals = int(score_match.group(1)) if score_match else 0
            away_goals = int(score_match.group(2)) if score_match else 0

            date_cell = tds[-1] if len(tds) > 1 else None
            date_text = date_cell.get_text(strip=True) if date_cell else ''

            parts = match_name.split('-', 1)
            home_team_name = parts[0].strip() if parts else ''
            away_team_name = parts[1].strip() if len(parts) > 1 else ''

            matches.append(MatchResult(
                home_team=home_team_name,
                away_team=away_team_name,
                home_goals=home_goals,
                away_goals=away_goals,
                date_str=date_text,
                stage=current_stage or '',
                detail_url=match_url,
            ))

        return matches

    def find_team_url(self, team_name):
        key = resolve_team_name(team_name)
        if key in self._team_cache:
            return self._team_cache[key]

        matches = self.get_all_matches_from_results()
        for m in matches:
            if key in normalize(m.home_team) or key in normalize(m.away_team):
                try:
                    soup = self._soup(f'{BASE_URL}{m.detail_url}')
                    for a in soup.find_all('a', href=True):
                        if '/team/' in a['href']:
                            tname = a.get_text(strip=True)
                            if tname and key == normalize(tname):
                                self._team_cache[key] = a['href']
                                return a['href']
                            if tname and key in normalize(tname):
                                self._team_cache[key] = a['href']
                                return a['href']
                except Exception as e:
                    logger.error('Error fetching detail page %s: %s', m.detail_url, e)
                    continue

        return None

    def _parse_team_matches(self, soup, tournament_filter):
        matches = []
        current_tournament = None

        for tr in soup.find_all('tr'):
            th = tr.find('th')
            if th:
                txt = th.get_text(strip=True)
                txt_norm = normalize(txt)
                has_wc = 'world championship' in txt_norm or 'world cup' in txt_norm
                is_final = normalize(tournament_filter) in txt_norm
                is_not_qualification = 'qualification' not in txt_norm
                if has_wc and is_final and is_not_qualification:
                    current_tournament = txt
                else:
                    current_tournament = None
                continue

            if current_tournament is None:
                continue

            tds = tr.find_all('td')
            if len(tds) < 7:
                continue

            round_name = tds[1].get_text(strip=True)
            team1_elem = tds[2]
            team2_elem = tds[3]

            home_team = team1_elem.get_text(strip=True)
            away_team = team2_elem.get_text(strip=True)

            score_cell = tds[4]
            score_text = score_cell.get_text(strip=True)

            ft_match = re.match(r'^(\d+)\s*:\s*(\d+)', score_text)
            if not ft_match:
                continue

            home_goals = int(ft_match.group(1))
            away_goals = int(ft_match.group(2))

            detail_link = ''
            details_td = tds[5]
            da = details_td.find('a', href=True)
            if da:
                detail_link = da['href']

            date_str = tds[-1].get_text(strip=True)

            matches.append(MatchResult(
                home_team=home_team,
                away_team=away_team,
                home_goals=home_goals,
                away_goals=away_goals,
                date_str=date_str,
                round_name=round_name,
                detail_url=detail_link,
                tournament=current_tournament,
            ))

        return matches

    def _match_to_dict(self, m):
        return {
            'home_team': m.home_team,
            'away_team': m.away_team,
            'home_goals': m.home_goals,
            'away_goals': m.away_goals,
            'date_str': m.date_str,
            'round_name': m.round_name,
            'detail_url': m.detail_url,
            'tournament': m.tournament,
        }

    @staticmethod
    def _match_from_dict(d):
        return MatchResult(
            home_team=d['home_team'],
            away_team=d['away_team'],
            home_goals=d['home_goals'],
            away_goals=d['away_goals'],
            date_str=d['date_str'],
            round_name=d['round_name'],
            detail_url=d['detail_url'],
            tournament=d['tournament'],
        )

    def get_team_matches(self, team_url, tournament_filter='Final tournament'):
        ck = cache_key(team_url, tournament_filter)
        cached = cache.get(ck)
        if cached is not None and is_cache_fresh(cached):
            logger.info('Cache hit for %s', ck)
            return [self._match_from_dict(m) for m in cached['matches']]

        logger.info('Cache miss or stale for %s, fetching...', ck)
        soup = self._soup(f'{BASE_URL}{team_url}results/')
        matches = self._parse_team_matches(soup, tournament_filter)

        cache.set(ck, {
            'matches': [self._match_to_dict(m) for m in matches],
            'cached_at': datetime.now().isoformat(),
        })

        return matches
