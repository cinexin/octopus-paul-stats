from utils import normalize


class TestNormalize:
    def test_basic_lowercase(self):
        assert normalize('Spain') == 'spain'

    def test_strips_whitespace(self):
        assert normalize('  Spain  ') == 'spain'

    def test_removes_accents(self):
        assert normalize('España') == 'espana'
        assert normalize('Francia') == 'francia'
        assert normalize('Bélgica') == 'belgica'

    def test_handles_multi_word(self):
        assert normalize('United States') == 'united states'
        assert normalize('Países Bajos') == 'paises bajos'

    def test_handles_special_chars(self):
        assert normalize("Côte d'Ivoire") == "cote d'ivoire"

    def test_empty_string(self):
        assert normalize('') == ''

    def test_already_normalized(self):
        assert normalize('argentina') == 'argentina'

    def test_mixed_case(self):
        assert normalize('ArGEnTina') == 'argentina'

    def test_dot_handling(self):
        assert normalize('ee. uu.') == 'ee. uu.'
