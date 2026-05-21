import pandas as pd
from pathlib import Path
from shiny import App, ui, reactive
from dotenv import load_dotenv

from modules.config import AppConfig
from modules.data_module import data_server
from modules.sidebar_module import sidebar_ui, sidebar_server
from modules.map_module import map_ui, map_server
from modules.table_module import table_ui, table_server
from modules.navbar_module import create_navbar_decorations, geolocation_script
from modules.status_module import status_ui, status_server

load_dotenv()

BASE_DIR = Path(__file__).parent
METADATA_PATH = BASE_DIR / "routes_metadata.json"

config = AppConfig(METADATA_PATH)

theme = ui.Theme.from_brand(__file__)
theme.add_rules((BASE_DIR / "_colors.scss").read_text())

app_ui = ui.page_navbar(
    geolocation_script(),
    ui.nav_panel(
        "Rastreador en Vivo",
        ui.layout_sidebar(
            sidebar_ui("sidebar", config.LINE_CHOICES),
            status_ui("status"),
            ui.card(
                ui.card_header("Mapa de Vehículos"),
                map_ui("main_map"),
                full_screen=True,
            ),
            table_ui("main_table")
        )
    ),
    ui.nav_panel(
        "Documentación",
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("Información del Proyecto"),
                ui.markdown("""
                ### Metrobús CDMX - Live Tracker
                Esta aplicación proporciona una visualización interactiva y en tiempo real de la flota del Metrobús de la Ciudad de México.
                
                #### Fuentes de Datos
                1.  **GTFS-RT (Real-Time)**: Posiciones GPS de los autobuses obtenidas directamente de la API de Sonda/Metrobús.
                2.  **GTFS Estático**: Información de rutas, paradas y metadatos de las líneas (L1-L7).
                
                #### Tecnologías
                - **Shiny for Python**: Framework para la interfaz reactiva.
                - **ipyleaflet**: Integración de mapas interactivos.
                - **Protocol Buffers**: Decodificación de feeds binarios GTFS-RT.
                - **brand.yml**: Identidad visual corporativa.
                
                #### Actualización
                Los datos se actualizan a petición del usuario o mediante el botón de actualización, garantizando que siempre veas la posición más reciente reportada por el sistema.
                """)
            ),
            ui.card(
                ui.card_header("Guía de Uso"),
                ui.markdown("""
                1.  **Seleccionar Línea**: Filtra los vehículos por la línea correspondiente.
                2.  **Filtrar por Ruta**: Permite aislar recorridos específicos dentro de una línea.
                3.  **Actualizar**: Presiona el botón para obtener las posiciones más recientes.
                4.  **Mapa**: Haz clic en los iconos de autobús para ver el ID del vehículo y el nombre de la ruta.
                """)
            ),
            width=1/2,
        )
    ),
    *create_navbar_decorations(),
    title="Metrobús CDMX - Live Tracker",
    fillable=True,
    theme=theme,
)

def server(input, output, session):
    print("DEBUG: Server function starting...")
    data_state = data_server(
        "data",
        config.ROUTE_TO_LINE,
        config.ROUTE_ID_TO_NAME,
        config.AUTH_URL
    )
    print("DEBUG: data_server initialized")
    
    # Define vehicle count calculator that will be used by sidebar
    @reactive.Calc
    def vehicle_count():
        df = filtered_data()
        return len(df)
    
    # Initialize sidebar first to get access to its inputs
    sidebar_state = sidebar_server(
        "sidebar",
        config.metadata,
        data_state.trigger_refresh,
        vehicle_count
    )
    print("DEBUG: sidebar_server initialized")
    
    @reactive.Calc
    def filtered_data():
        raw_data = data_state.vehicles_data()
        print(f"DEBUG: filtered_data() - raw data has {len(raw_data)} vehicles")
        df = pd.DataFrame(raw_data)
        if df.empty:
            print("DEBUG: filtered_data() - DataFrame is empty")
            return df
        
        selected_line = sidebar_state.selected_line()
        print(f"DEBUG: filtered_data() - filtering by line={selected_line}")
        print(f"DEBUG: filtered_data() - unique lines in data: {df['line'].unique().tolist()}")
        df = df[df["line"] == selected_line]
        print(f"DEBUG: filtered_data() - after line filter: {len(df)} vehicles")
        
        selected_route = sidebar_state.selected_route()
        if selected_route != "all":
            print(f"DEBUG: filtered_data() - filtering by route={selected_route}")
            df = df[df["route_id"] == selected_route]
            print(f"DEBUG: filtered_data() - after route filter: {len(df)} vehicles")
        else:
            print(f"DEBUG: filtered_data() - route filter is 'all', keeping all routes")
        
        return df
    
    status_server("status", data_state.fetch_error, data_state.last_fetch_time)
    
    map_server(
        "main_map",
        filtered_data,
        sidebar_state.selected_line,
        config.metadata,
        data_state.is_loading
    )
    
    table_server("main_table", filtered_data)

app = App(app_ui, server)
