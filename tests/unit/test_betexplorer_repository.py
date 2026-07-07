from unittest.mock import Mock, patch

import pytest
import requests

from infrastructure.betexplorer_repository import BetExplorerRepository, resolve_team_name


class TestResolveTeamName:
    def test_canonical_name(self):
        assert resolve_team_name('spain') == 'spain'

    def test_spanish_variant(self):
        assert resolve_team_name('españa') == 'spain'

    def test_english_team(self):
        assert resolve_team_name('inglaterra') == 'england'

    def test_unknown_team_returns_normalized(self):
        assert resolve_team_name('atlantis') == 'atlantis'

    def test_case_insensitive(self):
        assert resolve_team_name('España') == 'spain'

    def test_variant_with_accents(self):
        assert resolve_team_name('bélgica') == 'belgium'
        assert resolve_team_name('países bajos') == 'netherlands'


class TestBetExplorerRepositorySoup:
    def test_soup_success(self, mock_results_html):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = mock_results_html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            soup = repo._soup('https://example.com')
            assert soup is not None
            assert soup.find('table') is not None

    def test_soup_connection_error(self):
        repo = BetExplorerRepository()
        with patch.object(repo.session, 'get', side_effect=requests.ConnectionError('No connection')):
            with pytest.raises(requests.ConnectionError):
                repo._soup('https://example.com')

    def test_soup_timeout(self):
        repo = BetExplorerRepository()
        with patch.object(repo.session, 'get', side_effect=requests.Timeout('Timed out')):
            with pytest.raises(requests.Timeout):
                repo._soup('https://example.com')

    def test_soup_http_error(self):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError('404 Not Found')

        with patch.object(repo.session, 'get', return_value=mock_response):
            with pytest.raises(requests.HTTPError):
                repo._soup('https://example.com')


class TestBetExplorerRepositoryGetAllMatches:
    def test_returns_matches_from_table(self, mock_results_html):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = mock_results_html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_all_matches_from_results()

        assert len(matches) == 2
        assert matches[0].home_team == 'Spain'
        assert matches[0].away_team == 'France'
        assert matches[0].home_goals == 2
        assert matches[0].away_goals == 1
        assert matches[0].date_str == '01.06.2026'
        assert matches[0].stage == 'Group A'

    def test_empty_table(self, mock_empty_table_html):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = mock_empty_table_html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_all_matches_from_results()

        assert matches == []

    def test_no_table_found(self, mock_no_table_html):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = mock_no_table_html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_all_matches_from_results()

        assert matches == []

    def test_malformed_row_skipped(self, mock_results_html):
        malformed = mock_results_html.replace(
            '</tr>',
            '<tr><td>Bad row no links</td></tr></tr>',
            1,
        )
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = malformed
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_all_matches_from_results()

        assert len(matches) == 2

    def test_empty_html(self):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = ''
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_all_matches_from_results()

        assert matches == []


class TestBetExplorerRepositoryFindTeamUrl:
    def test_team_found_in_cache(self, mock_results_html):
        repo = BetExplorerRepository()
        repo._team_cache['spain'] = '/team/spain/'

        with patch.object(repo, 'get_all_matches_from_results') as mock_get_all:
            url = repo.find_team_url('spain')
            mock_get_all.assert_not_called()
        assert url == '/team/spain/'

    def test_team_found_via_detail_page(self, mock_results_html, mock_detail_html):
        repo = BetExplorerRepository()

        mock_results_resp = Mock()
        mock_results_resp.text = mock_results_html
        mock_results_resp.raise_for_status = Mock()

        mock_detail_resp = Mock()
        mock_detail_resp.text = mock_detail_html
        mock_detail_resp.raise_for_status = Mock()

        session_get_calls = [
            mock_results_resp,
            mock_detail_resp,
        ]

        with patch.object(repo.session, 'get', side_effect=session_get_calls):
            url = repo.find_team_url('Spain')

        assert url is not None
        assert '/team/spain/' in url or '/team/Spain/' in url

    def test_team_not_found(self, mock_no_table_html):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = mock_no_table_html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            url = repo.find_team_url('Atlantis')

        assert url is None

    def test_detail_page_fails_gracefully(self, mock_results_html):
        repo = BetExplorerRepository()
        mock_results_resp = Mock()
        mock_results_resp.text = mock_results_html
        mock_results_resp.raise_for_status = Mock()

        # Simulate failure on the detail page call
        session_calls = [
            mock_results_resp,
            requests.ConnectionError('Failed'),
        ]

        with patch.object(repo.session, 'get', side_effect=session_calls):
            url = repo.find_team_url('Spain')

        assert url is None


class TestBetExplorerRepositoryGetTeamMatches:
    def test_returns_matches_for_tournament(self, mock_team_page_html):
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = mock_team_page_html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_team_matches('/team/spain/')

        assert len(matches) == 2
        assert matches[0].home_team == 'Spain'
        assert matches[0].away_team == 'France'
        assert matches[0].home_goals == 2
        assert matches[0].away_goals == 1
        assert matches[0].round_name == 'Group stage'

    def test_connection_error(self):
        repo = BetExplorerRepository()
        with patch.object(repo.session, 'get', side_effect=requests.ConnectionError('No connection')):
            with pytest.raises(requests.ConnectionError):
                repo.get_team_matches('/team/spain/')

    def test_timeout_error(self):
        repo = BetExplorerRepository()
        with patch.object(repo.session, 'get', side_effect=requests.Timeout('Timed out')):
            with pytest.raises(requests.Timeout):
                repo.get_team_matches('/team/spain/')

    def test_no_tournament_match(self):
        html = '''
        <html><body>
        <table class="table-main">
          <tr><th>Qualification</th></tr>
          <tr>
            <td></td><td>Group stage</td>
            <td><a>Spain</a></td><td><a>France</a></td>
            <td><a>2 : 1</a></td><td></td><td>01.06.2026</td>
          </tr>
        </table>
        </body></html>
        '''
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_team_matches('/team/spain/')

        assert matches == []

    def test_skips_rows_without_full_score(self):
        html = '''
        <html><body>
        <table class="table-main">
          <tr><th>World Championship 2026 - Final tournament</th></tr>
          <tr>
            <td></td><td>Group stage</td>
            <td><a>Spain</a></td><td><a>France</a></td>
            <td><a>a.e.t.</a></td><td></td><td>01.06.2026</td>
          </tr>
        </table>
        </body></html>
        '''
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_team_matches('/team/spain/')

        assert matches == []

    def test_handles_date_parse_error(self):
        html = '''
        <html><body>
        <table class="table-main">
          <tr><th>World Championship 2026 - Final tournament</th></tr>
          <tr>
            <td></td><td>Group stage</td>
            <td><a>Spain</a></td><td><a>France</a></td>
            <td><a>2 : 1</a></td><td></td><td>invalid-date</td>
          </tr>
        </table>
        </body></html>
        '''
        repo = BetExplorerRepository()
        mock_response = Mock()
        mock_response.text = html
        mock_response.raise_for_status = Mock()

        with patch.object(repo.session, 'get', return_value=mock_response):
            matches = repo.get_team_matches('/team/spain/')

        assert len(matches) == 1
        assert matches[0].date_str == 'invalid-date'
