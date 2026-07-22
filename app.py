import pandas as pd 
import plotly.express as px
from shiny import App, ui
from shinywidgets import output_widget, render_plotly
from sqlalchemy import create_engine

# 1. CONEXIÓN A LA BASE servidor 2
# Nota: La contraseña y el puerto deben coincidir con la config de tu grupo
engine_bi = create_engine('mysql+pymysql://root:password_local@localhost:3306/bi_db')

def cargar_datos():
    try:
        # Intenta leer la tabla generada por el ETL de Alex
        df = pd.read_sql("SELECT * FROM kpi_rendimiento", con=engine_bi)
        return df
    except Exception as e:
        # PLAN DE CONTINGENCIA: Mientras Alex termina su parte, cargamos datos de prueba 
        # para que puedas diseñar el Dashboard y tomar las capturas hoy mismo.
        print("Esperando la conexión a bi_db. Usando datos de prueba temporalmente...")
        return pd.DataFrame({
            'Team': ['Argentina', 'France', 'Brazil', 'Germany', 'Spain', 'Ecuador', 'Angola'],
            'Victorias': [47, 34, 73, 67, 30, 4, 0],
            'Indice_Rendimiento': [2.5, 2.1, 2.8, 2.7, 2.0, 1.2, 0.5]
        })

df_rendimiento = cargar_datos()

# 2. DEFINIR LA INTERFAZ (UI)
app_ui = ui.page_fluid(
    ui.h2("Dashboard BI - Análisis Histórico FIFA", class_="text-center mt-3 mb-4"),
    
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Panel de Control"),
            ui.input_select(
                "seleccion",
                "Filtrar por Selección:",
                choices=["Todas"] + df_rendimiento['Team'].tolist(),
                selected="Todas"
            ),
            ui.hr(),
            ui.p("Datos procesados desde el Servidor 2 (ETL).")
        ),
        
        # Tarjeta para el Mapa Especializado (Requisito Rúbrica)
        ui.card(
            ui.h4("Mapa de Rendimiento Histórico"),
            output_widget("mapa_coropletico")
        ),
        
        # Tarjeta para el Gráfico Adicional
        ui.card(
            ui.h4("Top Selecciones (Victorias e Índice)"),
            output_widget("grafico_barras")
        )
    )
)

# 3. LÓGICA DEL SERVIDOR
def server(input, output, session):
    
    # Función reactiva para el filtro del sidebar
    def datos_filtrados():
        if input.seleccion() == "Todas":
            return df_rendimiento
        else:
            return df_rendimiento[df_rendimiento['Team'] == input.seleccion()]

    @render_plotly
    def mapa_coropletico():
        df_plot = datos_filtrados()
        # Creación del mapa especializado
        fig = px.choropleth(
            df_plot,
            locations="Team", 
            locationmode="country names", # Crucial: mapea usando el nombre en inglés del país
            color="Victorias",  
            hover_name="Team",
            color_continuous_scale=px.colors.sequential.Plasma,
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}) # Optimiza el espacio
        return fig
        
    @render_plotly
    def grafico_barras():
        df_plot = datos_filtrados()
        df_plot = df_plot.sort_values(by='Victorias', ascending=False).head(10)
        
        fig = px.bar(
            df_plot,
            x="Team",
            y="Victorias",
            color="Indice_Rendimiento",
            labels={'Team': 'Selección', 'Victorias': 'Total Victorias', 'Indice_Rendimiento': 'Índice KPI'}
        )
        return fig

# 4. LEVANTAR LA APLICACIÓN
app = App(app_ui, server)
