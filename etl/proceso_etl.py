import pandas as pd
from sqlalchemy import create_engine
import sys

# 1. Configuración de Conexiones
DB_NEGOCIO_URI = 'mysql+pymysql://etl_alex:Proyecto2026!@100.107.153.6:3306/fifa_db'
DB_PARAMETROS_URI = 'mysql+pymysql://etl_local:Proceso2026!@localhost:3306/parametros_db'
DB_BI_URI = 'mysql+pymysql://etl_local:Proceso2026!@localhost:3306/bi_db'

try:
    engine_negocio = create_engine(DB_NEGOCIO_URI)
    engine_parametros = create_engine(DB_PARAMETROS_URI)
    engine_bi = create_engine(DB_BI_URI)
except Exception as e:
    print(f"Error crítico al conectar con los servidores: {e}")
    sys.exit(1)

# 2. Leer Parámetros
print("Leyendo parámetros de configuración...")
query_params = "SELECT parametro, valor FROM configuracion"
df_params = pd.read_sql(query_params, engine_parametros)
parametros = dict(zip(df_params['parametro'], df_params['valor']))

top_n = int(parametros.get('top_n', 10))
min_avg_goals = parametros.get('min_avg_goals', 1.80)
year_from = int(parametros.get('year_from', 1990))

# 3. Extraer Datos del Servidor 1 (Roxana)
print(f"Extrayendo datos históricos desde la versión {year_from}...")
query_datos = f"SELECT * FROM historico_mundiales WHERE version >= {year_from}"
df_fifa = pd.read_sql(query_datos, engine_negocio)

# Transformaciones y cálculos
df_fifa['matches_played'] = df_fifa['wins_last_4y'] + df_fifa['draws_last_4y'] + df_fifa['losses_last_4y']
df_fifa['matches_played_safe'] = df_fifa['matches_played'].replace(0, 1)

# KPIs
print("Calculando KPIs...")
kpi1 = df_fifa.groupby('team').agg(victorias=('wins_last_4y', 'sum'), partidos_jugados=('matches_played', 'sum'), partidos_jugados_safe=('matches_played_safe', 'sum')).reset_index()
kpi1['porcentaje_victorias'] = (kpi1['victorias'] / kpi1['partidos_jugados_safe']) * 100
kpi1 = kpi1.drop(columns=['partidos_jugados_safe']).sort_values(by='victorias', ascending=False).head(top_n)

kpi2 = df_fifa.groupby('team').agg(goles_anotados=('goals_scored_last_4y', 'sum'), partidos_jugados=('matches_played', 'sum'), partidos_jugados_safe=('matches_played_safe', 'sum')).reset_index()
kpi2['promedio_goles'] = kpi2['goles_anotados'] / kpi2['partidos_jugados_safe']
kpi2 = kpi2[kpi2['promedio_goles'] > min_avg_goals].drop(columns=['partidos_jugados_safe'])

kpi3 = df_fifa.groupby('version').agg(total_goles=('goals_scored_last_4y', 'sum'), promedio_goles_partido=('goals_scored_last_4y', 'mean'), selecciones_participantes=('team', 'nunique')).reset_index()

kpi4 = df_fifa.groupby('team').agg(wins=('wins_last_4y', 'sum'), draws=('draws_last_4y', 'sum'), matches_played=('matches_played', 'sum'), partidos_jugados_safe=('matches_played_safe', 'sum')).reset_index()
kpi4['indice_rendimiento'] = ((kpi4['wins'] * 3) + kpi4['draws']) / kpi4['partidos_jugados_safe']
kpi4 = kpi4.drop(columns=['partidos_jugados_safe']).sort_values(by='indice_rendimiento', ascending=False).head(5)

# 4. Carga de Datos (Idempotente)
print("Cargando resultados al Servidor 2...")
kpi1.to_sql('kpi_ranking', con=engine_bi, if_exists='replace', index=False)
kpi2.to_sql('kpi_ofensiva', con=engine_bi, if_exists='replace', index=False)
kpi3.to_sql('kpi_evolucion', con=engine_bi, if_exists='replace', index=False)
kpi4.to_sql('kpi_rendimiento', con=engine_bi, if_exists='replace', index=False)

print("¡Proceso ETL completado exitosamente!")
