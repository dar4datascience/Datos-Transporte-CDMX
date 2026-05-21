from shiny import module, ui, render

@module.ui
def status_ui():
    return ui.output_ui("error_banner")

@module.server
def status_server(input, output, session, fetch_error, last_fetch_time):
    print("DEBUG: status_module - status_server initialized")
    print(f"DEBUG: status_module - fetch_error type: {type(fetch_error)}")
    print(f"DEBUG: status_module - last_fetch_time type: {type(last_fetch_time)}")
    
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
        print(f"DEBUG: status_module - last_update_status() called, last_fetch_time={t}")
        if t:
            result = f"Actualizado: {t}"
            print(f"DEBUG: status_module - returning '{result}'")
            return result
        print("DEBUG: status_module - returning 'Pendiente de actualizar'")
        return "Pendiente de actualizar"

    class StatusState:
        def __init__(self):
            self.last_update_status = last_update_status

    return StatusState()
