import os
import json
import time
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from google.transit import gtfs_realtime_pb2
from shiny import App, ui, render, reactive, session
from shinywidgets import output_widget, render_widget
import ipyleaflet as L
from ipywidgets import HTML
from dotenv import load_dotenv

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
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            console.log("Geolocation: Found coordinates", position.coords.latitude, position.coords.longitude);
                            const pos = {
                                lat: position.coords.latitude,
                                lng: position.coords.longitude
                            };
                            Shiny.setInputValue("user_location", pos, {priority: "event"});
                        },
                        (error) => {
                            console.error("Geolocation error:", error);
                        }
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
                ui.div(
                    ui.output_ui("map_loader"),
                    output_widget("map"),
                    class_="map-container"
                ),
                full_screen=True,
            ),
            ui.accordion(
                ui.accordion_panel(
                    "Lista de Vehículos",
                    ui.output_data_frame("vehicle_table"),
                ),
                id="acc_vehicles",
                open=False,
            ),
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

    # Persistent Map and Layer Group
    m = L.Map(center=(19.4326, -99.1332), zoom=11, scroll_wheel_zoom=True)
    marker_group = L.LayerGroup()
    user_layer = L.LayerGroup()
    m.add_layer(marker_group)
    m.add_layer(user_layer)

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

    @reactive.Effect
    @reactive.event(input.user_location)
    def _handle_user_location():
        loc = input.user_location()
        if not loc:
            return
            
        lat = loc["lat"]
        lng = loc["lng"]
        print(f"DEBUG: Handling user location -> Lat: {lat}, Lng: {lng}")
        
        # Clear old user marker
        user_layer.clear_layers()
        
        # Purple circle marker for user
        user_icon = L.DivIcon(
            html='<div style="background-color: #9b59b6; border-radius: 50%; width: 20px; height: 20px; border: 3px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.6);"></div>',
            icon_size=(20, 20),
            icon_anchor=(10, 10)
        )
        
        user_marker = L.Marker(
            location=(lat, lng),
            icon=user_icon,
            draggable=False,
            popup=HTML(value="<b>Tu ubicación</b>")
        )
        
        user_layer.layers = (user_marker,)
        
        # Center map on user
        m.center = (lat, lng)
        m.zoom = 15

    async def fetch_live_data():
        usuario = os.environ.get("USUARIO")
        password = os.environ.get("PASSWORD")

        if not usuario or not password:
            fetch_error.set("Error: Credenciales no configuradas (USUARIO/PASSWORD)")
            return []

        try:
            # 1. Authenticate to get S3 URLs
            payload = {"usuario": usuario, "senha": password}
            resp = requests.post(AUTH_URL, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            url_rt = data.get("urlRealTime")
            if not url_rt:
                fetch_error.set("Error: No se recibió URL de tiempo real de la API.")
                return []

            # 2. Fetch GTFS-RT Protobuf
            rt_resp = requests.get(url_rt, timeout=10)
            rt_resp.raise_for_status()

            # 3. Parse Protobuf
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(rt_resp.content)

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
    def map_loader():
        if is_loading():
            return ui.div(
                ui.div(class_="spinner-retro"),
                ui.div("Cargando datos...", style="margin-top: 10px; font-family: 'Quantico', sans-serif;"),
                class_="map-loader-overlay"
            )
        return None

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

    @reactive.Effect
    def _update_map_markers():
        # Clear existing markers
        marker_group.clear_layers()
        
        df = filtered_data()
        if not df.empty:
            # Get line color from metadata
            line_color = metadata["lines"].get(input.line(), {}).get("color", "#ff0000")
            
            new_markers = []
            for _, row in df.iterrows():
                icon = L.DivIcon(
                    html=f'<div style="background-color: {line_color}; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5); font-size: 16px;">🚌</div>',
                    icon_size=(30, 30),
                    icon_anchor=(15, 15)
                )
                
                marker = L.Marker(
                    location=(row["latitude"], row["longitude"]),
                    icon=icon,
                    draggable=False,
                    popup=HTML(value=f"<b>Vehículo:</b> {row['vehicle_id']}<br><b>Ruta:</b> {row['route_name']}")
                )
                new_markers.append(marker)
            
            if new_markers:
                marker_group.layers = tuple(new_markers)
                
                # Fit bounds only if markers exist and no user location is set
                if not input.user_location():
                    lats = df["latitude"].tolist()
                    lons = df["longitude"].tolist()
                    m.fit_bounds([(min(lats), min(lons)), (max(lats), max(lons))])

    @render_widget
    def map():
        return m

    @render.data_frame
    def vehicle_table():
        df = filtered_data()
        if df.empty:
            return render.DataTable(pd.DataFrame(columns=["ID", "Ruta", "Lat", "Lon", "Hora"]))
        
        # Format for display
        display_df = df[["vehicle_id", "route_name", "latitude", "longitude", "timestamp"]].copy()
        display_df["timestamp"] = pd.to_datetime(display_df["timestamp"], unit='s').dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City').dt.strftime('%H:%M:%S')
        display_df.columns = ["Vehículo", "Ruta", "Latitud", "Longitud", "Hora"]
        
        return render.DataTable(display_df)

app = App(app_ui, server)
