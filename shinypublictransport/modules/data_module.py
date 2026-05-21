import asyncio
import os
import time
import requests
from datetime import datetime
from google.transit import gtfs_realtime_pb2
from shiny import module, ui, reactive

@module.server
def data_server(input, output, session, route_to_line, route_id_to_name, auth_url):
    vehicles_data = reactive.Value([])
    last_fetch_time = reactive.Value(None)
    fetch_error = reactive.Value(None)
    is_loading = reactive.Value(False)
    refresh_trigger = reactive.Value(0)

    async def fetch_live_data():
        usuario = os.environ.get("USUARIO")
        password = os.environ.get("PASSWORD")

        if not usuario or not password:
            fetch_error.set("Error: Credenciales no configuradas (USUARIO/PASSWORD)")
            return []

        try:
            def do_fetch():
                payload = {"usuario": usuario, "senha": password}
                resp = requests.post(auth_url, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                
                url_rt = data.get("urlRealTime")
                if not url_rt:
                    return "error_url", []

                rt_resp = requests.get(url_rt, timeout=15)
                rt_resp.raise_for_status()
                return None, rt_resp.content

            error_type, content = await asyncio.to_thread(do_fetch)
            
            if error_type == "error_url":
                fetch_error.set("Error: No se recibió URL de tiempo real de la API.")
                return []

            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(content)

            parsed_vehicles = []
            for entity in feed.entity:
                if entity.HasField('vehicle'):
                    v = entity.vehicle
                    vehicle_id = v.vehicle.id if v.vehicle.HasField('id') else "N/A"
                    route_id = v.trip.route_id if v.trip.HasField('route_id') else "N/A"
                    
                    parsed_vehicles.append({
                        "vehicle_id": vehicle_id,
                        "route_id": str(route_id),
                        "route_name": route_id_to_name.get(str(route_id), f"Ruta {route_id}"),
                        "latitude": v.position.latitude,
                        "longitude": v.position.longitude,
                        "timestamp": v.timestamp if v.HasField('timestamp') else int(time.time()),
                        "line": route_to_line.get(str(route_id), "Unknown")
                    })
            
            fetch_error.set(None)
            last_fetch_time.set(datetime.now().strftime("%H:%M:%S"))
            return parsed_vehicles

        except Exception as e:
            fetch_error.set(f"Error de conexión: {str(e)}")
            return []

    @reactive.Effect
    @reactive.event(refresh_trigger)
    async def _handle_refresh():
        if refresh_trigger() == 0:
            return
        
        is_loading.set(True)
        try:
            with ui.Progress(min=1, max=10) as p:
                p.set(message="Autenticando y descargando datos...", value=3)
                data = await fetch_live_data()
                vehicles_data.set(data)
                p.set(message="Datos actualizados", value=10)
        finally:
            is_loading.set(False)

    def trigger_refresh():
        refresh_trigger.set(refresh_trigger() + 1)

    class DataState:
        def __init__(self):
            self.vehicles_data = vehicles_data
            self.last_fetch_time = last_fetch_time
            self.fetch_error = fetch_error
            self.is_loading = is_loading
            self.trigger_refresh = trigger_refresh

    return DataState()
