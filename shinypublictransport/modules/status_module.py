from shiny import module, ui, render

@module.ui
def status_ui():
    return ui.div(
        ui.output_ui("error_banner"),
        ui.div(
            ui.output_text("last_update_status", inline=True),
            class_="text-muted small mb-2"
        )
    )

@module.server
def status_server(input, output, session, fetch_error, last_fetch_time):
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

    class StatusState:
        def __init__(self):
            self.last_update_status = last_update_status

    return StatusState()
