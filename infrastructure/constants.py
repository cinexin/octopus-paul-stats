# Cabeceras HTTP para simular un navegador real
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

# URL base de BetExplorer
BASE_URL = 'https://www.betexplorer.com'

# URL de la página del Mundial 2026 en BetExplorer
WC_URL = f'{BASE_URL}/football/world/world-championship-2026'

# URL de la página de resultados del Mundial 2026
WC_RESULTS_URL = f'{WC_URL}/results/'

# Traducciones de nombres de equipos a inglés canónico
TEAM_TRANSLATIONS = {
    'spain': ['spain', 'españa', 'espana'],
    'belgium': ['belgium', 'bélgica', 'belgica'],
    'portugal': ['portugal'],
    'france': ['france', 'francia'],
    'england': ['england', 'inglaterra'],
    'germany': ['germany', 'alemania'],
    'netherlands': ['netherlands', 'holanda', 'países bajos', 'paises bajos'],
    'argentina': ['argentina'],
    'brazil': ['brazil', 'brasil'],
    'uruguay': ['uruguay'],
    'colombia': ['colombia'],
    'mexico': ['mexico', 'méxico'],
    'usa': ['usa', 'united states', 'estados unidos', 'ee. uu.', 'eeuu'],
    'switzerland': ['switzerland', 'suiza'],
    'morocco': ['morocco', 'marruecos'],
    'senegal': ['senegal'],
    'egypt': ['egypt', 'egipto'],
    'ivory coast': ['ivory coast', 'costa de marfil', "côte d'ivoire"],
    'croatia': ['croatia', 'croacia'],
    'sweden': ['sweden', 'suecia'],
    'norway': ['norway', 'noruega'],
    'japan': ['japan', 'japón'],
    'australia': ['australia'],
    'paraguay': ['paraguay'],
    'canada': ['canada', 'canadá'],
    'ghana': ['ghana'],
    'algeria': ['algeria', 'argelia'],
    'south africa': ['south africa', 'sudáfrica'],
    'austria': ['austria'],
    'cape verde': ['cape verde', 'cabo verde'],
    'd.r. congo': ['d.r. congo', 'dr congo', 'república democrática del congo'],
    'ecuador': ['ecuador'],
    'saudi arabia': ['saudi arabia', 'arabia saudí'],
    'bosnia & herzegovina': ['bosnia & herzegovina', 'bosnia', 'bosnia y herzegovina'],
    'turkey': ['turkey', 'turquía'],
    'new zealand': ['new zealand', 'nueva zelanda'],
}
