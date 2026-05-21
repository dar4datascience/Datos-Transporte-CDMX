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
    initial_load_done = reactive.Value(False)

    async def fetch_live_data():
        print("DEBUG: fetch_live_data() called")
        usuario = os.environ.get("USUARIO")
        password = os.environ.get("PASSWORD")

        if not usuario or not password:
            print("DEBUG: Missing credentials")
            fetch_error.set("Error: Credenciales no configuradas (USUARIO/PASSWORD)")
            return []

        print(f"DEBUG: Starting fetch with credentials (usuario={usuario[:3]}...)")
        try:
            def do_fetch():
                print("DEBUG: do_fetch() - Authenticating...")
                payload = {"usuario": usuario, "senha": password}
                resp = requests.post(auth_url, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                print(f"DEBUG: do_fetch() - Auth response received")
                
                url_rt = data.get("urlRealTime")
                if not url_rt:
                    print("DEBUG: do_fetch() - No urlRealTime in response")
                    return "error_url", []

                print(f"DEBUG: do_fetch() - Fetching GTFS-RT data...")
                rt_resp = requests.get(url_rt, timeout=15)
                rt_resp.raise_for_status()
                print(f"DEBUG: do_fetch() - Got {len(rt_resp.content)} bytes")
                return None, rt_resp.content

            print("DEBUG: Calling asyncio.to_thread(do_fetch)")
            error_type, content = await asyncio.to_thread(do_fetch)
            print(f"DEBUG: asyncio.to_thread completed, error_type={error_type}")
            
            if error_type == "error_url":
                print("DEBUG: error_url - No URL received")
                fetch_error.set("Error: No se recibió URL de tiempo real de la API.")
                return []

            print("DEBUG: Parsing protobuf...")
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(content)
            print(f"DEBUG: Feed has {len(feed.entity)} entities")

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
            
            print(f"DEBUG: Parsed {len(parsed_vehicles)} vehicles")
            fetch_error.set(None)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"DEBUG: Setting last_fetch_time to '{timestamp}'")
            last_fetch_time.set(timestamp)
            return parsed_vehicles

        except Exception as e:
            print(f"DEBUG: Exception in fetch_live_data: {e}")
            fetch_error.set(f"Error de conexión: {str(e)}")
            return []

    @reactive.Effect
    @reactive.event(refresh_trigger, ignore_none=False)
    async def _handle_refresh():
        print(f"DEBUG: _handle_refresh called, refresh_trigger={refresh_trigger()}")
        if refresh_trigger() == 0:
            print("DEBUG: Skipping refresh (trigger=0)")
            return
        
        print("DEBUG: Starting data refresh...")
        is_loading.set(True)
        try:
            with ui.Progress(min=1, max=10) as p:
                p.set(message="Autenticando y descargando datos...", value=3)
                data = await fetch_live_data()
                print(f"DEBUG: fetch_live_data returned {len(data)} vehicles")
                vehicles_data.set(data)
                print(f"DEBUG: vehicles_data updated")
                p.set(message="Datos actualizados", value=10)
        finally:
            is_loading.set(False)
            print("DEBUG: Refresh complete, is_loading=False")

    def trigger_refresh():
        new_val = refresh_trigger() + 1
        print(f"DEBUG: trigger_refresh() called, setting to {new_val}")
        refresh_trigger.set(new_val)

    # Trigger initial load only once
    @reactive.Effect
    def _auto_load_on_startup():
        if not initial_load_done():
            print("DEBUG: _auto_load_on_startup() - triggering first load")
            initial_load_done.set(True)
            trigger_refresh()
        else:
            print("DEBUG: _auto_load_on_startup() - already loaded, skipping")

    class DataState:
        def __init__(self):
            self.vehicles_data = vehicles_data
            self.last_fetch_time = last_fetch_time
            self.fetch_error = fetch_error
            self.is_loading = is_loading
            self.trigger_refresh = trigger_refresh

    return DataState()
