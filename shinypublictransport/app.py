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
from dotenv import load_dotenv

# Load environment variables if .env exists (for local testing)
load_dotenv()

# --- Configuration & Data Loading ---
BASE_DIR = Path(__file__).parent.parent
METADATA_PATH = BASE_DIR / "data" / "routes_metadata.json"
AUTH_URL = "https://metrobus-gtfs.sinopticoplus.com/gtfs-api/partnerValidation"

# Load metadata once
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

LINES = sorted(metadata["lines"].keys(), key=lambda x: int(x))
LINE_CHOICES = {line: f"Línea {line}" for line in LINES}

# Build route mapping for filtering
ROUTE_TO_LINE = {}
for line_num, line_data in metadata["lines"].items():
    for route in line_data["routes"]:
        ROUTE_TO_LINE[str(route["route_id"])] = line_num

# --- UI Definition ---
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("line", "Seleccionar Línea", choices=LINE_CHOICES, selected="1"),
        ui.input_select("route", "Filtrar por Ruta", choices={"all": "-- Todas las rutas --"}),
        ui.input_action_button("refresh", "🔄 Actualizar Datos", class_="btn-primary w-100"),
        ui.hr(),
        ui.markdown("""
        ### Acerca de
        Esta aplicación usa datos **en tiempo real** del Metrobús CDMX.
        
        Requiere credenciales configuradas en el servidor (`USUARIO` y `PASSWORD`).
        """),
    ),
    ui.output_ui("error_banner"),
    ui.layout_column_wrap(
        ui.card(
            ui.card_header(
                ui.toolbar(
                    ui.markdown("**Mapa de Vehículos**"),
                    ui.toolbar_spacer(),
                    ui.output_text("last_update_status"),
                )
            ),
            output_widget("map"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Lista de Vehículos"),
            ui.output_data_frame("vehicle_table"),
            full_screen=True,
        ),
        width=1,
    ),
    title="Metrobús CDMX - Live Tracker",
    fillable=True,
)

# --- Server Logic ---
def server(input, output, session):
    # Reactive value to store the latest raw vehicle data
    vehicles_data = reactive.Value([])
    last_fetch_time = reactive.Value(None)
    fetch_error = reactive.Value(None)

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
        with ui.Progress(min=1, max=10) as p:
            p.set(message="Autenticando y descargando datos...", value=3)
            data = await fetch_live_data()
            vehicles_data.set(data)
            p.set(message="Datos actualizados", value=10)

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

    @render_widget
    def map():
        m = L.Map(center=(19.4326, -99.1332), zoom=11, scroll_wheel_zoom=True)
        df = filtered_data()
        
        if not df.empty:
            # Get line color from metadata
            line_color = metadata["lines"].get(input.line(), {}).get("color", "#ff0000")
            
            markers = []
            for _, row in df.iterrows():
                marker = L.CircleMarker(
                    location=(row["latitude"], row["longitude"]),
                    radius=5,
                    color="white",
                    fill_color=line_color,
                    fill_opacity=0.8,
                    weight=2,
                    popup=L.HTML(value=f"<b>Vehículo:</b> {row['vehicle_id']}<br><b>Ruta:</b> {row['route_id']}")
                )
                markers.append(marker)
            
            if markers:
                marker_group = L.LayerGroup(layers=markers)
                m.add_layer(marker_group)
                
                # Fit bounds to markers
                lats = df["latitude"].tolist()
                lons = df["longitude"].tolist()
                m.fit_bounds([(min(lats), min(lons)), (max(lats), max(lons))])
        
        return m

    @render.data_frame
    def vehicle_table():
        df = filtered_data()
        if df.empty:
            return render.DataTable(pd.DataFrame(columns=["ID", "Ruta", "Lat", "Lon", "Hora"]))
        
        # Format for display
        display_df = df[["vehicle_id", "route_id", "latitude", "longitude", "timestamp"]].copy()
        display_df["timestamp"] = pd.to_datetime(display_df["timestamp"], unit='s').dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City').dt.strftime('%H:%M:%S')
        display_df.columns = ["Vehículo", "Ruta", "Latitud", "Longitud", "Hora"]
        
        return render.DataTable(display_df)

app = App(app_ui, server)
