import json
import ipyleaflet as L
from shiny import module, ui, render, reactive
from shinywidgets import output_widget, render_widget
from ipywidgets import HTML

@module.ui
def map_ui():
    return ui.div(
        ui.output_ui("map_loader"),
        output_widget("map"),
        class_="map-container",
        style="height: 600px; width: 100%; position: relative;"
    )

@module.server
def map_server(input, output, session, filtered_df_calc, line_input, metadata, is_loading_val):
    # Persistent Map and Layer Groups
    m = L.Map(center=(19.4326, -99.1332), zoom=11, scroll_wheel_zoom=True)
    m.layout.height = '600px'
    marker_group = L.LayerGroup()
    user_layer = L.LayerGroup()
    m.add_layer(marker_group)
    m.add_layer(user_layer)

    @render.ui
    def map_loader():
        if is_loading_val():
            return ui.div(
                ui.div(class_="spinner-retro"),
                ui.div("Cargando datos...", style="margin-top: 10px; font-family: 'Quantico', sans-serif;"),
                class_="map-loader-overlay"
            )
        return None

    @render_widget
    def map():
        return m

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
        
        # Solid person icon marker for user with Iris color
        user_icon = L.DivIcon(
            html='''<div style="color: #5D3FD3; filter: drop-shadow(0 0 4px rgba(0,0,0,0.5));">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6"/>
                </svg>
            </div>''',
            icon_size=(32, 32),
            icon_anchor=(16, 32)
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

    @reactive.Effect
    def _update_map_markers():
        # Clear existing markers
        marker_group.clear_layers()
        
        df = filtered_df_calc()
        if not df.empty:
            # Get line color from metadata
            current_line = line_input()
            line_color = metadata["lines"].get(current_line, {}).get("color", "#ff0000")
            
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
