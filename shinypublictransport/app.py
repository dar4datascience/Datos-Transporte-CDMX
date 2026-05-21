import asyncio
import os
import json
import time
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from google.transit import gtfs_realtime_pb2
from shiny import App, ui, render, reactive, session
from dotenv import load_dotenv

# Import modules
from modules.map_module import map_ui, map_server
from modules.table_module import table_ui, table_server

# Load environment variables if .env exists (for local testing)
load_dotenv()

# --- Configuration & Theme ---
BASE_DIR = Path(__file__).parent
METADATA_PATH = BASE_DIR / "routes_metadata.json"
AUTH_URL = "https://metrobus-gtfs.sinopticoplus.com/gtfs-api/partnerValidation"

# Load theme from brand.yml
theme = ui.Theme.from_brand(__file__)
theme.add_rules((Path(__file__).parent / "_colors.scss").read_text())

# Load metadata once
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

LINES = sorted(metadata["lines"].keys(), key=lambda x: int(x))
LINE_CHOICES = {line: f"Línea {line}" for line in LINES}

# Build mappings for filtering and names
ROUTE_TO_LINE = {}
ROUTE_ID_TO_NAME = {}
for line_num, line_data in metadata["lines"].items():
    for route in line_data["routes"]:
        rid_str = str(route["route_id"])
        ROUTE_TO_LINE[rid_str] = line_num
        ROUTE_ID_TO_NAME[rid_str] = route["name"]

# --- UI Definition ---
app_ui = ui.page_navbar(
    ui.head_content(
        ui.tags.script("""
            function getLocation() {
                if (navigator.geolocation) {
                    const options = {
                        enableHighAccuracy: false,
                        timeout: 10000,
                        maximumAge: 60000
                    };
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            console.log("Geolocation: Found coordinates", position.coords.latitude, position.coords.longitude);
                            const pos = {
                                lat: position.coords.latitude,
                                lng: position.coords.longitude
                            };
                            Shiny.setInputValue("main_map-user_location", pos, {priority: "event"});
                        },
                        (error) => {
                            console.warn("Geolocation error:", error.message);
                            // Still send something to potentially clear loading state if app depended on it
                        },
                        options
                    );
                }
            }
            
            $(document).on("shiny:connected", function(event) {
                getLocation();
            });

            $(document).on("click", "#find_me", function() {
                getLocation();
            });
        """)
    ),
    ui.nav_panel(
        "Rastreador en Vivo",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select("line", "Seleccionar Línea", choices=LINE_CHOICES, selected="1"),
                ui.input_select("route", "Filtrar por Ruta", choices={"all": "-- Todas las rutas --"}),
                ui.input_action_button("refresh", "🔄 Actualizar Datos", class_="btn-primary w-100"),
                ui.input_action_button("find_me", "📍 Mi Ubicación", class_="btn-secondary w-100 mt-2"),
                ui.hr(),
                ui.markdown("""
                ### Estado del Sistema
                """),
                ui.output_ui("stats_sidebar"),
                ui.hr(),
            ),
            ui.output_ui("error_banner"),
            ui.card(
                ui.card_header(
                    ui.toolbar(
                        ui.markdown("**Mapa de Vehículos**"),
                        ui.toolbar_spacer(),
                        ui.output_text("last_update_status"),
                    )
                ),
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
    ui.nav_spacer(),
    ui.nav_control(
        ui.div(
            ui.div("En Bici ya hubieras llegado", class_="fading-phrase"),
            class_="fading-phrase-container"
        )
    ),
    ui.nav_control(
        ui.div(
            ui.div(
                ui.span("🚲", class_="retro-bike"),
                class_="bike-mover"
            ),
            class_="navbar-bike-container"
        )
    ),
    ui.nav_control(
        ui.div(
            ui.div(
                ui.span("🚌", class_="retro-bus"),
                class_="bus-mover"
            ),
            class_="navbar-bus-container"
        )
    ),
    ui.nav_control(ui.input_dark_mode(id="color_mode")),
    title="Metrobús CDMX - Live Tracker",
    fillable=True,
    theme=theme,
)

# --- Server Logic ---
def server(input, output, session):
    # Reactive value to store the latest raw vehicle data
    vehicles_data = reactive.Value([])
    last_fetch_time = reactive.Value(None)
    fetch_error = reactive.Value(None)
    is_loading = reactive.Value(False)

    @reactive.Effect
    @reactive.event(input.line)
    def _update_routes():
        line_num = input.line()
        if line_num in metadata["lines"]:
            routes = metadata["lines"][line_num]["routes"]
            choices = {"all": "-- Todas las rutas --"}
            for r in sorted(routes, key=lambda x: x["name"]):
                choices[str(r["route_id"])] = r["name"]
            ui.update_select("route", choices=choices, selected="all")

    async def fetch_live_data():
        usuario = os.environ.get("USUARIO")
        password = os.environ.get("PASSWORD")

        if not usuario or not password:
            fetch_error.set("Error: Credenciales no configuradas (USUARIO/PASSWORD)")
            return []

        try:
            # Run blocking requests in a thread to avoid freezing the event loop
            def do_fetch():
                # 1. Authenticate to get S3 URLs
                payload = {"usuario": usuario, "senha": password}
                resp = requests.post(AUTH_URL, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                url_rt = data.get("urlRealTime")
                if not url_rt:
                    return "error_url", []

                # 2. Fetch GTFS-RT Protobuf
                rt_resp = requests.get(url_rt, timeout=15)
                rt_resp.raise_for_status()
                return None, rt_resp.content

            error_type, content = await asyncio.to_thread(do_fetch)
            
            if error_type == "error_url":
                fetch_error.set("Error: No se recibió URL de tiempo real de la API.")
                return []

            # 3. Parse Protobuf
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(content)

            parsed_vehicles = []
            for entity in feed.entity:
                if entity.HasField('vehicle'):
                    v = entity.vehicle
                    vehicle_id = v.vehicle.id if v.vehicle.HasField('id') else "N/A"
                    route_id = v.trip.route_id if v.trip.HasField('route_id') else "N/A"
                    
                    # Basic mapping to our internal format
                    parsed_vehicles.append({
                        "vehicle_id": vehicle_id,
                        "route_id": str(route_id),
                        "route_name": ROUTE_ID_TO_NAME.get(str(route_id), f"Ruta {route_id}"),
                        "latitude": v.position.latitude,
                        "longitude": v.position.longitude,
                        "timestamp": v.timestamp if v.HasField('timestamp') else int(time.time()),
                        "line": ROUTE_TO_LINE.get(str(route_id), "Unknown")
                    })
            
            fetch_error.set(None)
            last_fetch_time.set(datetime.now().strftime("%H:%M:%S"))
            return parsed_vehicles

        except Exception as e:
            fetch_error.set(f"Error de conexión: {str(e)}")
            return []

    @reactive.Effect
    @reactive.event(input.refresh, ignore_none=False)
    async def _handle_refresh():
        is_loading.set(True)
        try:
            with ui.Progress(min=1, max=10) as p:
                p.set(message="Autenticando y descargando datos...", value=3)
                data = await fetch_live_data()
                vehicles_data.set(data)
                p.set(message="Datos actualizados", value=10)
        finally:
            is_loading.set(False)

    @reactive.Calc
    def filtered_data():
        df = pd.DataFrame(vehicles_data())
        if df.empty:
            return df
        
        # Filter by line
        df = df[df["line"] == input.line()]
        
        # Filter by route
        if input.route() != "all":
            df = df[df["route_id"] == input.route()]
            
        return df

    @render.ui
    def stats_sidebar():
        df = filtered_data()
        count = len(df)
        return ui.div(
            ui.value_box(
                "Vehículos",
                count,
                theme="primary",
            ),
        )

    @render.ui
    def error_banner():
        err = fetch_error()
        if err:
            return ui.div(
                ui.markdown(f"**⚠️ {err}**"),
                class_="alert alert-danger m-3",
                role="alert"
            )
        return None

    @render.text
    def last_update_status():
        t = last_fetch_time()
        if t:
            return f"Actualizado: {t}"
        return "Pendiente de actualizar"

    # Initialize Modules
    map_server("main_map", filtered_data, input.line, metadata, is_loading)
    table_server("main_table", filtered_data)

app = App(app_ui, server)
