import pandas as pd
from shiny import module, ui, render

@module.ui
def table_ui():
    return ui.accordion(
        ui.accordion_panel(
            "Lista de Vehículos",
            ui.output_data_frame("vehicle_table"),
        ),
        id="acc_vehicles",
        open=False,
    )

@module.server
def table_server(input, output, session, filtered_df_calc):
    @render.data_frame
    def vehicle_table():
        df = filtered_df_calc()
        print(f"DEBUG: table_module - vehicle_table() called with {len(df)} vehicles")
        if df.empty:
            print("DEBUG: table_module - DataFrame is empty, showing empty table")
            return render.DataTable(pd.DataFrame(columns=["ID", "Ruta", "Lat", "Lon", "Hora"]))
        
        # Format for display
        display_df = df[["vehicle_id", "route_name", "latitude", "longitude", "timestamp"]].copy()
        display_df["timestamp"] = pd.to_datetime(display_df["timestamp"], unit='s').dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City').dt.strftime('%H:%M:%S')
        display_df.columns = ["Vehículo", "Ruta", "Latitud", "Longitud", "Hora"]
        
        print(f"DEBUG: table_module - returning table with {len(display_df)} rows")
        return render.DataTable(display_df)
