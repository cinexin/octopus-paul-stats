# 🐙 octopus-paul-stats

> **⚠️ AVISO: Esto es un proyecto lúdico/de aprendizaje — un JUEGO.**
> Su única finalidad es divertirse programando. No está diseñado para incentivar ni apoyar las apuestas deportivas. Aquí no nos gustan las casas de apuestas.

Calcula probabilidades de partidos de fútbol usando distribución de Poisson con datos extraídos de BetExplorer.

## Requisitos

- Python 3.10+
- pip

## Instalación

```bash
pip install -r requirements.txt
```

## Uso (con Python)

```bash
python -m main [equipo1] [equipo2] [num_partidos]
```

### Ejemplos

```bash
# Por defecto: Spain vs Belgium (5 partidos)
python -m main

# Equipos personalizados
python -m main "Argentina" "Brasil"

# Con número de partidos recientes a considerar
python -m main "Francia" "Inglaterra" 10
```

## API REST

El proyecto incluye una API REST construida con **FastAPI** con documentación Swagger interactiva.

### Redis (caché)

```bash
docker compose up -d
```

### Arrancar el servidor

```bash
pip install -r requirements.txt
uvicorn application.api:app --reload
```

### Endpoint

| Método | Ruta    | Parámetros                                                            | Descripción                                          |
|--------|---------|-----------------------------------------------------------------------|------------------------------------------------------|
| GET    | `/stats`| `local` (requerido), `visitor` (requerido), `n_matches` (opcional, default 5) | Estadísticas y probabilidades para dos equipos       |

### Ejemplos con curl

```bash
curl "http://localhost:8000/stats?local=spain&visitor=france"

curl "http://localhost:8000/stats?local=españa&visitor=inglaterra&n_matches=10"
```

### Documentación interactiva (Swagger)

Una vez arrancado el servidor, abre en el navegador:

- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Respuesta (JSON)

```json
{
  "local_team": "spain",
  "visitor_team": "france",
  "local_team_stats": {
    "avg_goals": 1.8,
    "avg_conceded": 0.0,
    "n_matches": 5,
    "matches": [...],
    "h2h_avg_goals": 1.5
  },
  "visitor_team_stats": {...},
  "h2h_matches": [...],
  "probabilities": {
    "team1_win_90": 0.42,
    "draw_90": 0.38,
    "team2_win_90": 0.20,
    "team1_win_et": 0.08,
    "team2_win_et": 0.08,
    "team1_win_pen": 0.13,
    "team2_win_pen": 0.10,
    "team1_total": 0.62,
    "team2_total": 0.38,
    "exp_t1": 0.85,
    "exp_t2": 0.49
  }
}
```

### Parámetros

| Parámetro     | Descripción                                      | Default       |
|---------------|--------------------------------------------------|---------------|
| `equipo1`     | Nombre del primer equipo                         | Spain         |
| `equipo2`     | Nombre del segundo equipo                        | Belgium       |
| `num_partidos`| Partidos recientes a analizar por equipo         | 5             |

### Equipos soportados

España, Bélgica, Portugal, Francia, Inglaterra, Alemania, Países Bajos, Argentina, Brasil, Uruguay, Colombia, México, USA, Suiza, Marruecos, Senegal, Egipto, Croacia, Suecia, Noruega, Japón, Australia, Paraguay, Canadá, Ghana, Argelia, Sudáfrica, Austria, Cabo Verde, Ecuador, Arabia Saudí, Turquía, Nueva Zelanda, y otros.

## Tests

El proyecto incluye tests unitarios, de integración y end-to-end.

```bash
# Instalar dependencias (incluye pytest)
pip install -r requirements.txt

# Ejecutar todos los tests
python -m pytest

# Ejecutar solo tests unitarios
python -m pytest tests/unit/

# Ejecutar solo tests de integración
python -m pytest tests/integration/

# Ejecutar solo tests end-to-end
python -m pytest tests/e2e/

# Ejecutar con más detalle
python -m pytest -v

# Ejecutar un archivo específico
python -m pytest tests/unit/test_poisson_stats_service.py
```

Los tests cubren:
- **Unitarios**: `normalize()`, modelos, cálculo Poisson, scraping (con HTML simulado y errores de red), CLI
- **Integración**: interacción repositorio-servicio, flujo completo de estadísticas
- **E2E**: pipeline completo desde argumentos CLI hasta salida de probabilidades, incluyendo errores de conexión, equipo no encontrado, y argumentos inválidos

## Compilar ejecutable

Genera un binario independiente para tu SO (no necesita Python instalado):

```bash
# Instalar PyInstaller (ya incluido en requirements.txt)
pip install -r requirements.txt

# Compilar
pyinstaller octopus-paul-stats.spec

# El ejecutable se genera en dist/octopus-paul-stats
./dist/octopus-paul-stats "Argentina" "Brasil" 10

# Opcional: mover a una ruta del PATH
sudo cp dist/octopus-paul-stats /usr/local/bin/
octopus-paul-stats "Argentina" "Brasil"
```

## Estructura del proyecto

Sigue el patrón **Domain-Driven Design (DDD)** con **inyección de dependencias** (`injection`):

```
octopus-paul-stats/
├── main.py                                # Entry point (crea contenedor, wirea y ejecuta)
├── utils.py                               # Utilidades transversales (normalize)
│
├── domain/
│   ├── models/
│   │   ├── constants.py                   # Constantes de dominio (pesos Bayesianos, Poisson)
│   │   ├── match_result.py                # @dataclass MatchResult
│   │   ├── team_stats.py                  # @dataclass TeamStats
│   │   └── probability_result.py          # @dataclass ProbabilityResult
│   └── services/
│       ├── stats_computation_service.py   # Interfaz: StatsComputationService
│       ├── poisson_stats_service.py       # Implementación: PoissonStatsService
│       ├── team_stats_query_service.py    # Interfaz: TeamStatsService
│       └── bet_explorer_team_stats_service.py  # Implementación: BetExplorerTeamStatsService
│
├── infrastructure/
│   ├── constants.py                       # Constantes de scraping (URLs, headers, traducciones)
│   └── betexplorer_repository.py          # BetExplorerRepository (scraping puro)
│
├── application/
│   ├── api.py                             # API REST (FastAPI): endpoint /stats
│   ├── schemas.py                         # Pydantic models para la API
│   ├── constants.py                       # Constantes de presentación/CLI
│   ├── container.py                       # Contenedor DI (AppContainer con providers)
│   └── cli.py                             # Orquestación: fetch → compute H2H → probabilities → display
│
├── docker-compose.yml                     # Redis local para caché
├── octopus-paul-stats.spec                # Configuración de PyInstaller
├── requirements.txt
└── tests/
    ├── conftest.py                        # Fixtures compartidos (mocks HTML, sample data)
    ├── unit/
    │   ├── test_utils.py                  # normalize()
    │   ├── test_models.py                 # MatchResult, TeamStats, ProbabilityResult
    │   ├── test_poisson_stats_service.py  # Cálculo Poisson, Bayesian prior, H2H
    │   ├── test_betexplorer_repository.py # Repositorio scraping + resolve_team_name
    │   └── test_cli.py                    # compute_h2h, print*, main()
    ├── integration/
    │   ├── test_api.py                               # API REST (FastAPI)
    │   ├── test_repository_service_integration.py    # Repo + TeamStatsService
    │   └── test_full_stats_flow.py                   # TeamStatsService + PoissonStatsService
    └── e2e/
        └── test_full_pipeline.py          # CLI completo: args → stats → probabilidades
```

### Capas

| Capa             | Responsabilidad                                                              |
|------------------|------------------------------------------------------------------------------|
| **Domain**       | Entidades del negocio, interfaces de servicio e implementaciones de cálculo. Sin efectos secundarios ni dependencias externas. |
| **Infrastructure** | Acceso a datos externos (scraping BetExplorer). Depende de `domain` (usa sus entidades). |
| **Application**  | Orquestación: configura el contenedor DI, recibe input, llama a servicios del dominio, presenta resultados. |

### Inyección de dependencias

Cada servicio del dominio sigue el patrón **interfaz + implementación**:

| Interfaz                          | Implementación                    | Provider en container             |
|-----------------------------------|-----------------------------------|-----------------------------------|
| `StatsComputationService`         | `PoissonStatsService`             | `AppContainer.stats_service`      |
| `TeamStatsService`                | `BetExplorerTeamStatsService`     | `AppContainer.team_stats_service` |

`BetExplorerTeamStatsService` inyecta `BetExplorerRepository` (infrastructure) para scrapear datos.

`main.py` llama a `main()` con los servicios inyectados vía `@inject` / `Provide` de la librería `injection`.
