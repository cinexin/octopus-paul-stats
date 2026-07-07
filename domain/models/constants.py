# Pesos bayesianos para suavizado de medias hacia la media de la liga
PRIOR_WEIGHT = 3

# Media de goles por partido de la liga (valor por defecto)
LEAGUE_AVG_GOALS = 1.25

# Peso de los goles esperados "raw" al combinarlos con datos h2h
H2H_RAW_WEIGHT = 0.6
# Peso de los datos head-to-head al combinarlos con goles esperados raw
H2H_DATA_WEIGHT = 0.4

# Número máximo de goles considerados en la distribución de Poisson
MAX_GOALS_POISSON = 10

# Probabilidad de que un empate en 90' termine en victoria en prórroga (cada equipo)
DRAW_TO_ET_WIN_PROB = 0.20
# Probabilidad de que un empate en 90' llegue a penaltis
DRAW_TO_PENALTIES_PROB = 0.60

# Probabilidad de ganar en penaltis (cada equipo)
PENALTIES_WIN_PROB_T1 = 0.55
PENALTIES_WIN_PROB_T2 = 0.45
