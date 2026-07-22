import pandas as pd
from sqlalchemy import create_engine
import datetime
import sys

def ejecutar_etl():
    print(f"[{datetime.datetime.now()}] Iniciando proceso ETL...")
    
    try:
        # 1. CONEXIONES A LAS BASES DE DATOS
        # Servidor 1 (Origen - Roxana vía Tailscale)
        engine_origen = create_engine('mysql+pymysql://etl_alex:Proyecto2026!@100.107.153.6:3306/fifa_db')
        
        # Servidor 2 (Destino y Parámetros - Tu máquina local)
        engine_local = create_engine('mysql+pymysql://etl_local:Proceso2026!@localhost:3306/parametros_db')
        engine_bi = create_engine('mysql+pymysql://etl_local:Proceso2026!@localhost:3306/bi_db')
        
        print("Conexiones a bases de datos establecidas con éxito.")
        
        # 2. LECTURA DE PARÁMETROS DE CONFIGURACIÓN
        print("Leyendo parámetros de configuración...")
        config_df = pd.read_sql("SELECT parametro, valor FROM configuracion", con=engine_local)
        parametros = dict(zip(config_df['parametro'], config_df['valor']))
        
        year_from = int(parametros.get('year_from', 1990))
        top_n = int(parametros.get('top_n', 10))
        min_avg_goals = float(parametros.get('min_avg_goals', 1.80))
        
        print(f"Parámetros cargados: year_from={year_from}, top_n={top_n}, min_avg_goals={min_avg_goals}")
        
        # 3. EXTRACCIÓN DE DATOS (E)
        print(f"Extrayendo datos históricos desde la versión {year_from}...")
        query_datos = f"SELECT * FROM historico_mundiales WHERE version >= {year_from}"
        df_fifa = pd.read_sql(query_datos, con=engine_origen)
        print(f"Extracción completada. {len(df_fifa)} registros recuperados.")
        
        # 4. TRANSFORMACIÓN Y CÁLCULO DE KPIS (T)
        print("Calculando Indicadores Clave de Rendimiento (KPIs)...")
        
        df_fifa['matches_played'] = df_fifa['wins_last_4y'] + df_fifa['draws_last_4y'] + df_fifa['losses_last_4y']
        df_fifa['matches_played_safe'] = df_fifa['matches_played'].replace(0, 1)

        # KPI 1: Ranking Top N por Porcentaje de victorias -> kpi_ranking
        kpi1 = df_fifa.groupby('team').agg(
            victorias=('wins_last_4y', 'sum'), 
            partidos_jugados=('matches_played', 'sum'), 
            partidos_jugados_safe=('matches_played_safe', 'sum')
        ).reset_index()
        kpi1['porcentaje_victorias'] = (kpi1['victorias'] / kpi1['partidos_jugados_safe']) * 100
        kpi1 = kpi1.drop(columns=['partidos_jugados_safe']).sort_values(by='victorias', ascending=False).head(top_n)

        # KPI 2: Perfil Ofensivo (Filtro por min_avg_goals) -> kpi_ofensiva
        kpi2 = df_fifa.groupby('team').agg(
            goles_anotados=('goals_scored_last_4y', 'sum'), 
            partidos_jugados=('matches_played', 'sum'), 
            partidos_jugados_safe=('matches_played_safe', 'sum')
        ).reset_index()
        kpi2['promedio_goles'] = kpi2['goles_anotados'] / kpi2['partidos_jugados_safe']
        kpi2 = kpi2[kpi2['promedio_goles'] > min_avg_goals].drop(columns=['partidos_jugados_safe'])

        # KPI 3: Evolución Histórica por mundial -> kpi_evolucion
        kpi3 = df_fifa.groupby('version').agg(
            total_goles=('goals_scored_last_4y', 'sum'), 
            promedio_goles_partido=('goals_scored_last_4y', 'mean'), 
            selecciones_participantes=('team', 'nunique')
        ).reset_index()

        # KPI 4: Índice de rendimiento histórico -> kpi_rendimiento
        kpi4 = df_fifa.groupby('team').agg(
            wins=('wins_last_4y', 'sum'), 
            draws=('draws_last_4y', 'sum'), 
            matches_played=('matches_played', 'sum'), 
            partidos_jugados_safe=('matches_played_safe', 'sum')
        ).reset_index()
        kpi4['indice_rendimiento'] = ((kpi4['wins'] * 3) + kpi4['draws']) / kpi4['partidos_jugados_safe']
        kpi4 = kpi4.drop(columns=['partidos_jugados_safe']).sort_values(by='indice_rendimiento', ascending=False).head(5)
        
        # 5. CARGA DE DATOS IDEMPOTENTE (L)
        print("Cargando resultados en repositorio bi_db de forma idempotente...")
        kpi1.to_sql('kpi_ranking', con=engine_bi, if_exists='replace', index=False)
        kpi2.to_sql('kpi_ofensiva', con=engine_bi, if_exists='replace', index=False)
        kpi3.to_sql('kpi_evolucion', con=engine_bi, if_exists='replace', index=False)
        kpi4.to_sql('kpi_rendimiento', con=engine_bi, if_exists='replace', index=False)
        print("Carga en repositorio bi_db completada exitosamente.")
        
        # 6. CRITERIO DE RÚBRICA: EXPORTACIÓN AUTOMÁTICA DE REPORTES
        print("Generando exportación automática de reportes de negocio...")
        fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        nombre_reporte = f"reporte_rendimiento_{fecha_hoy}.csv"
        
        # Guardar copia física en CSV del KPI de rendimiento
        kpi4.to_csv(nombre_reporte, index=False)
        print(f"¡Reporte técnico guardado automáticamente como: {nombre_reporte}!")
        print("¡Proceso ETL completado exitosamente!")
        
    except Exception as e:
        print(f"ERROR CRÍTICO EN EL PROCESO ETL: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_etl()
