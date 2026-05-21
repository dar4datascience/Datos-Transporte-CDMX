from shiny import module, ui, render, reactive

@module.ui
def sidebar_ui(line_choices):
    return ui.sidebar(
        ui.input_select("line", "Seleccionar Línea", choices=line_choices, selected="1"),
        ui.input_select("route", "Filtrar por Ruta", choices={"all": "-- Todas las rutas --"}),
        ui.input_action_button("refresh", "🔄 Actualizar Datos", class_="btn-primary w-100"),
        ui.input_action_button("find_me", "📍 Mi Ubicación", class_="btn-secondary w-100 mt-2"),
        ui.hr(),
        ui.markdown("""
        ### Estado del Sistema
        """),
        ui.output_ui("stats_sidebar"),
        ui.hr(),
    )

@module.server
def sidebar_server(input, output, session, filtered_df_calc, metadata, on_refresh_callback):
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
    @reactive.event(input.refresh)
    def _handle_refresh_click():
        on_refresh_callback()

    @render.ui
    def stats_sidebar():
        df = filtered_df_calc()
        count = len(df)
        return ui.div(
            ui.value_box(
                "Vehículos",
                count,
                theme="primary",
            ),
        )

    class SidebarState:
        def __init__(self):
            self.selected_line = input.line
            self.selected_route = input.route

    return SidebarState()
