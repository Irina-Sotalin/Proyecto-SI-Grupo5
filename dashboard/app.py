import os
import pandas as pd
import plotly.express as px
from shiny import App, render, ui
from shinywidgets import output_widget, render_plotly

# --- 1. Carga y Procesamiento de Datos ---
def cargar_datos():
    rutas_train = [
        "../data/dataset_fifa_train.csv", "../data/train.csv", 
        "data/dataset_fifa_train.csv", "data/train.csv", 
        "train.csv", "datos_fifa.csv"
    ]
    rutas_test = [
        "../data/dataset_fifa_test.csv", "../data/test.csv", 
        "data/dataset_fifa_test.csv", "data/test.csv", 
        "test.csv"
    ]
    
    df_train = None
    df_test = None

    for ruta in rutas_train:
        if os.path.exists(ruta):
            df_train = pd.read_csv(ruta)
            break

    for ruta in rutas_test:
        if os.path.exists(ruta):
            df_test = pd.read_csv(ruta)
            break

    if df_train is not None and df_test is not None:
        df_raw = pd.concat([df_train, df_test], ignore_index=True)
    elif df_train is not None:
        df_raw = df_train
    elif df_test is not None:
        df_raw = df_test
    else:
        raise FileNotFoundError("No se encontraron los archivos de dataset FIFA en la carpeta data/")

    # Limpieza de columnas
    df_raw.columns = df_raw.columns.str.strip()

    # Identificar columna del equipo / país
    col_team = None
    for col in df_raw.columns:
        c = col.lower().strip()
        if c in ['team', 'equipo', 'pais', 'country', 'seleccion', 'home_team']:
            col_team = col
            break
    if not col_team:
        text_cols = df_raw.select_dtypes(include=['object']).columns
        col_team = text_cols[0] if len(text_cols) > 0 else df_raw.columns[0]

    # Buscar columna de victorias
    col_wins = None
    for col in df_raw.columns:
        c = col.lower().strip()
        if c in ['wins', 'victorias', 'victorias_totales', 'total_wins', 'win', 'wins_total', 'partidos_ganados'] and c not in ['year', 'ano', 'anio', 'date', 'fecha']:
            col_wins = col
            break

    # Buscar columna de rendimiento
    col_perf = None
    for col in df_raw.columns:
        c = col.lower().strip()
        if c in ['performance_index', 'indice_rendimiento', 'performance', 'indice', 'score', 'points']:
            col_perf = col
            break

    # Normalizar texto de países
    df_raw[col_team] = df_raw[col_team].astype(str).str.strip()

    # Agrupación de datos
    if col_wins and col_wins in df_raw.columns:
        df_raw[col_wins] = pd.to_numeric(df_raw[col_wins], errors='coerce').fillna(0)
        agg_dict = {col_wins: 'sum'}
        if col_perf and col_perf in df_raw.columns:
            df_raw[col_perf] = pd.to_numeric(df_raw[col_perf], errors='coerce')
            agg_dict[col_perf] = 'mean'
        
        df_grouped = df_raw.groupby(col_team, as_index=False).agg(agg_dict)
        df_grouped.rename(columns={col_team: 'Team', col_wins: 'Victorias'}, inplace=True)
        if col_perf and col_perf in df_grouped.columns:
            df_grouped.rename(columns={col_perf: 'Indice_Rendimiento'}, inplace=True)
    else:
        df_grouped = df_raw.groupby(col_team, as_index=False).size()
        df_grouped.rename(columns={col_team: 'Team', 'size': 'Victorias'}, inplace=True)

    df_grouped = df_grouped.dropna(subset=['Team'])
    df_grouped['Victorias'] = df_grouped['Victorias'].astype(int)

    # Cálculo proporcional si no venía la columna
    if 'Indice_Rendimiento' not in df_grouped.columns or df_grouped['Indice_Rendimiento'].isnull().all() or (df_grouped['Indice_Rendimiento'] == 1.0).all():
        max_v = df_grouped['Victorias'].max()
        if max_v > 0:
            df_grouped['Indice_Rendimiento'] = (0.50 + (df_grouped['Victorias'] / max_v)).round(2)
        else:
            df_grouped['Indice_Rendimiento'] = 1.00
    else:
        df_grouped['Indice_Rendimiento'] = df_grouped['Indice_Rendimiento'].round(2)

    return df_grouped

# Carga global de datos
df_rendimiento = cargar_datos()
lista_paises = ["Todas"] + sorted(df_rendimiento["Team"].dropna().unique().tolist())

# --- 2. Interfaz de Usuario (UI) ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h3("Acerca del Análisis:"),
        ui.markdown(
            """
            Este proyecto recopila, procesa y consolida el **histórico de desempeño de las selecciones nacionales de fútbol** registradas en los datasets de la FIFA.

            * **Objetivo Principal:** Superar las limitaciones de los registros individuales por torneo realizando un **agrupamiento total (ETL)** que suma las victorias históricas completas de cada país a lo largo del tiempo.
            * **Criterio de Desempate:** En casos donde múltiples selecciones comparten la misma cantidad de victorias, se integra y evalúa un **Índice de Rendimiento**, permitiendo ordenar de forma justa el ranking de jerarquía futbolística.
            """
        ),
        ui.hr(),
        ui.h4("Instrucciones de Uso:"),
        ui.markdown(
            """
            * **Filtro de Selección:** Selecciona una nación en específico para inspeccionar sus datos individuales o elige *Todas* para la comparativa global.
            * **Navegación:** Explora las tres pestañas para navegar entre indicadores macro, relaciones operativas internas y el detalle tabular.
            """
        ),
        ui.hr(),
        ui.input_select(
            id="pais_select",
            label="Selecciona una Selección:",
            choices=lista_paises,
            selected="Todas"
        ),
        width=330
    ),
    
    # Estructura de pestañas sugerida
    ui.navset_tab(
        
        # Pestaña 1: KPIs Externos
        ui.nav_panel(
            "1. KPIs Externos",
            ui.div(style="height: 10px;"),
            ui.layout_columns(
                ui.value_box("Países Procesados", ui.output_text("txt_total_paises"), showcase=None),
                ui.value_box("Total Victorias Acumuladas", ui.output_text("txt_total_victorias"), showcase=None),
                ui.value_box("Índice Rendimiento Promedio", ui.output_text("txt_promedio_rendimiento"), showcase=None),
                fill=False
            ),
            ui.div(style="height: 10px;"),
            ui.card(
                ui.card_header("Mapa Global de Victorias Históricas"),
                output_widget("mapa_paises")
            ),
            ui.card(
                ui.card_header("Top 15 Selecciones Destacadas (Acumulado Histórico)"),
                output_widget("barras_paises")
            ),
            ui.card(
                ui.card_header("Análisis macro de Distribución Geográfica y Desempeño"),
                ui.markdown(
                    """
                    ### Distribución Geográfica y Jerarquía Global
                    * **Concentración Geográfica:** El mapa interactivo resalta la acumulación histórica de victorias a nivel global, visibilizando la hegemonía competitiva concentrada en confederaciones tradicionales como Sudamérica (CONMEBOL) y Europa (UEFA).
                    * **Visualización del Top 15:** El gráfico de barras consolidado permite identificar rápidamente a los líderes globales, ordenados por total de triunfos acumulados y diferenciados según su densidad de rendimiento relativo.
                    """
                )
            )
        ),
        
        # Pestaña 2: KPIs Internos
        ui.nav_panel(
            "2. KPIs Internos",
            ui.div(style="height: 10px;"),
            ui.card(
                ui.card_header("Relación entre Victorias e Índice de Rendimiento"),
                output_widget("dispersion_rendimiento")
            ),
            ui.card(
                ui.card_header("Metodología y Análisis de Eficiencia Interna"),
                ui.markdown(
                    """
                    ### Análisis Detallado de Eficiencia y Correlación
                    * **Índice de Rendimiento:** Esta métrica evalúa la consistencia de cada selección. Mide el comportamiento proporcional del equipo frente al máximo número de victorias registradas en la base de datos.
                    * **Dispersión Operativa:** El gráfico de burbujas proyecta la posición de cada selección. Las naciones ubicadas en el extremo superior derecho representan aquellas con mayor solidez histórica, combinando un alto volumen de victorias con un índice de rendimiento destacado.
                    """
                )
            )
        ),
        
        # Pestaña 3: Datos
        ui.nav_panel(
            "3. Datos",
            ui.div(style="height: 10px;"),
            ui.card(
                ui.card_header("Descripción de la Base de Datos y Proceso ETL"),
                ui.markdown(
                    """
                    ### Estructura y Origen del Dataset Consolidado
                    * **Fuente de Origen:** Los datos provienen del procesamiento unificado de los archivos de entrenamiento y prueba (`dataset_fifa_train.csv` y `dataset_fifa_test.csv`).
                    * **Tratamiento y Limpieza (ETL):** Se realizó una estandarización de variables de texto, eliminación de valores nulos en los identificadores de país y suma agrupada por selección nacional para consolidar registros dispersos.
                    * **Campos del Tablero:**
                      * **Selección / País:** Nombre de la federación o selección nacional procesada.
                      * **Victorias Acumuladas:** Suma total de encuentros ganados a lo largo de los registros.
                      * **Índice de Rendimiento:** Valor numérico ajustado que refleja la efectividad ponderada de la selección.
                    """
                )
            ),
            ui.card(
                ui.card_header("Tabla Consolidada de Datos Procesados"),
                ui.output_data_frame("tabla_datos")
            )
        )
    ),
    
    title="Dashboard Histórico de Rendimiento FIFA"
)

# --- 3. Lógica del Servidor (Server) ---
def server(input, output, session):

    def df_filtrado():
        pais = input.pais_select()
        if pais == "Todas":
            return df_rendimiento
        return df_rendimiento[df_rendimiento["Team"] == pais]

    # Métricas generales
    @render.text
    def txt_total_paises():
        return f"{len(df_filtrado())}"

    @render.text
    def txt_total_victorias():
        return f"{df_filtrado()['Victorias'].sum():,}"

    @render.text
    def txt_promedio_rendimiento():
        df = df_filtrado()
        if len(df) == 0:
            return "0.0"
        return f"{df['Indice_Rendimiento'].mean():.2f}"

    # Pestaña 1: KPIs Externos
    @render_plotly
    def barras_paises():
        df_plot = df_rendimiento.sort_values(
            by=['Victorias', 'Indice_Rendimiento'], 
            ascending=[False, False]
        ).head(15)
        
        fig = px.bar(
            df_plot,
            x="Victorias",
            y="Team",
            orientation="h",
            color="Indice_Rendimiento",
            labels={'Team': 'Selección', 'Victorias': 'Total Victorias', 'Indice_Rendimiento': 'Índice'},
            color_continuous_scale=px.colors.sequential.Plasma
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), margin={"l": 0, "r": 0, "t": 30, "b": 0})
        return fig

    @render_plotly
    def mapa_paises():
        fig = px.choropleth(
            df_filtrado(),
            locations="Team",
            locationmode="country names",
            color="Victorias",
            hover_name="Team",
            hover_data={"Indice_Rendimiento": True, "Victorias": True},
            color_continuous_scale=px.colors.sequential.Plasma,
            labels={'Victorias': 'Total Victorias', 'Indice_Rendimiento': 'Índice', 'Team': 'País'}
        )
        fig.update_layout(
            geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'),
            margin={"l": 0, "r": 0, "t": 0, "b": 0}
        )
        return fig

    # Pestaña 2: KPIs Internos
    @render_plotly
    def dispersion_rendimiento():
        fig = px.scatter(
            df_filtrado(),
            x="Victorias",
            y="Indice_Rendimiento",
            size="Victorias",
            color="Team",
            hover_name="Team",
            labels={'Victorias': 'Total Victorias', 'Indice_Rendimiento': 'Índice de Rendimiento', 'Team': 'Selección'}
        )
        fig.update_layout(margin={"l": 0, "r": 0, "t": 30, "b": 0})
        return fig

    # Pestaña 3: Datos
    @render.data_frame
    def tabla_datos():
        df = df_filtrado().rename(columns={
            "Team": "Selección / País",
            "Victorias": "Victorias Acumuladas",
            "Indice_Rendimiento": "Índice de Rendimiento"
        })
        return render.DataGrid(df, selection_mode="none")

# --- 4. Ejecución ---
app = App(app_ui, server)
