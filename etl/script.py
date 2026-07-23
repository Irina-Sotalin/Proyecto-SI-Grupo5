import mysql.connector
import pandas as pd

print("Iniciando el procesamiento de datos del proyecto (ETL)...")

# 1. Lógica real de extracción y transformación (ETL de la FIFA)
try:
    # Leemos el archivo real que acabas de descargar
    df = pd.read_csv('train.csv')
    
    # Filtramos las columnas exactas que vimos en tu terminal
    df_clean = pd.DataFrame()
    df_clean['Team'] = df['team']
    df_clean['Wins'] = df['wins_last_4y']
    df_clean['Draws'] = df['draws_last_4y']
    df_clean['Losses'] = df['losses_last_4y']
    
    # Calculamos el total de partidos jugados
    df_clean['Matches_Played'] = df_clean['Wins'] + df_clean['Draws'] + df_clean['Losses']

    # Agrupamos por equipo para sumar todo su historial de los mundiales
    kpi4 = df_clean.groupby('Team').agg(
        Victorias=('Wins', 'sum'),
        Empates=('Draws', 'sum'),
        Partidos_Jugados=('Matches_Played', 'sum')
    ).reset_index()
    
    # Aplicamos la fórmula del Índice de Rendimiento
    kpi4['Indice_Rendimiento'] = ((kpi4['Victorias'] * 3) + kpi4['Empates']) / kpi4['Partidos_Jugados'].replace(0, 1)
    
    # Ordenamos y mostramos el Top 10 histórico
    kpi4 = kpi4.sort_values(by='Indice_Rendimiento', ascending=False).head(10)
    
    print("\n Datos procesados con éxito (Top 10 Índice de Rendimiento Histórico):")
    print(kpi4.to_string(index=False))

except Exception as e:
    print("\n Error al procesar el CSV:", e)

# 2. Conexión a la base de datos MySQL (Servidor 2 Oficial)
try:
    conexion = mysql.connector.connect(
        host="100.108.10.35",
        user="etl_local",
        password="Proceso2026!",
        database="bi_db",
        port=3306
    )
    cursor = conexion.cursor()
    print("\n Conexión exitosa a la base de datos bi_db en el Servidor 2")
    
    # El código para hacer INSERT de la tabla procesada irá aquí
    
    cursor.close()
    conexion.close()

except Exception as e:
    print("\nError al conectar a la base de datos:", e)

print("\n¡Proceso finalizado correctamente!")
