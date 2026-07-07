import pytest

from domain.models.match_result import MatchResult
from domain.models.probability_result import ProbabilityResult
from domain.models.team_stats import TeamStats


@pytest.fixture
def sample_match():
    return MatchResult(
        home_team='Spain',
        away_team='France',
        home_goals=2,
        away_goals=1,
        date_str='01.06.2026',
        stage='Group A',
        detail_url='/football/world/world-championship-2026/spain-france-2026/',
    )


@pytest.fixture
def sample_matches():
    return [
        MatchResult(home_team='Spain', away_team='France', home_goals=2, away_goals=1, date_str='01.06.2026'),
        MatchResult(home_team='Spain', away_team='Germany', home_goals=1, away_goals=1, date_str='05.06.2026'),
        MatchResult(home_team='Brazil', away_team='Spain', home_goals=0, away_goals=3, date_str='10.06.2026'),
        MatchResult(home_team='Spain', away_team='Argentina', home_goals=2, away_goals=2, date_str='15.06.2026'),
        MatchResult(home_team='Portugal', away_team='Spain', home_goals=1, away_goals=1, date_str='20.06.2026'),
    ]


@pytest.fixture
def sample_team_stats(sample_matches):
    return TeamStats(
        avg_goals=1.8,
        avg_conceded=1.0,
        n_matches=5,
        matches=sample_matches,
        h2h_avg_goals=1.5,
    )


@pytest.fixture
def sample_probability_result():
    return ProbabilityResult(
        team1_win_90=0.45,
        draw_90=0.25,
        team2_win_90=0.30,
        team1_win_et=0.05,
        team2_win_et=0.05,
        team1_win_pen=0.15,
        team2_win_pen=0.10,
        team1_total=0.65,
        team2_total=0.45,
        exp_t1=1.8,
        exp_t2=1.2,
    )


@pytest.fixture
def mock_results_html():
    return '''
    <html><body>
    <table class="table-main">
      <tr><th>Group A</th></tr>
      <tr>
        <td><a href="/match/1/">Spain - France</a></td>
        <td><a href="/match/1/">2 : 1</a></td>
        <td>01.06.2026</td>
      </tr>
      <tr>
        <td><a href="/match/2/">Germany - Spain</a></td>
        <td><a href="/match/2/">1 : 1</a></td>
        <td>05.06.2026</td>
      </tr>
    </table>
    </body></html>
    '''


@pytest.fixture
def mock_team_page_html():
    return '''
    <html><body>
    <table class="table-main">
      <tr><th>World Championship 2026 - Final tournament</th></tr>
      <tr>
        <td></td>
        <td>Group stage</td>
        <td><a href="/team/spain/">Spain</a></td>
        <td><a href="/team/france/">France</a></td>
        <td><a href="/score/1/">2 : 1</a></td>
        <td><a href="/detail/1/">Detail</a></td>
        <td>01.06.2026</td>
      </tr>
      <tr>
        <td></td>
        <td>Group stage</td>
        <td><a href="/team/germany/">Germany</a></td>
        <td><a href="/team/spain/">Spain</a></td>
        <td><a href="/score/2/">1 : 1</a></td>
        <td><a href="/detail/2/">Detail</a></td>
        <td>05.06.2026</td>
      </tr>
    </table>
    </body></html>
    '''


@pytest.fixture
def mock_detail_html():
    return '''
    <html><body>
    <a href="/team/spain/">Spain</a>
    <a href="/team/france/">France</a>
    </body></html>
    '''


@pytest.fixture
def mock_empty_table_html():
    return '<html><body><table class="table-main"></table></body></html>'


@pytest.fixture
def mock_no_table_html():
    return '<html><body><div>No table here</div></body></html>'
