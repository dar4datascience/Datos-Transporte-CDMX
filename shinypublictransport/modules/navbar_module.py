from shiny import ui

def geolocation_script():
    return ui.head_content(
        ui.tags.script("""
            function getLocation() {
                if (navigator.geolocation) {
                    const options = {
                        enableHighAccuracy: false,
                        timeout: 30000,
                        maximumAge: 60000
                    };
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            console.log("Geolocation: Found coordinates", position.coords.latitude, position.coords.longitude);
                            const pos = {
                                lat: position.coords.latitude,
                                lng: position.coords.longitude,
                                timestamp: Date.now()
                            };
                            Shiny.setInputValue("main_map-user_location", pos, {priority: "event"});
                        },
                        (error) => {
                            console.warn("Geolocation error:", error.message);
                            let errorMsg = "No se pudo obtener tu ubicación.";
                            if (error.code === 1) {
                                errorMsg = "Permiso de ubicación denegado. Habilita la ubicación en tu navegador.";
                            } else if (error.code === 2) {
                                errorMsg = "Ubicación no disponible.";
                            } else if (error.code === 3) {
                                errorMsg = "Tiempo de espera agotado al obtener ubicación.";
                            }
                            alert(errorMsg);
                        },
                        options
                    );
                }
            }
            
            $(document).on("shiny:connected", function(event) {
                setTimeout(() => getLocation(), 0);
            });

            $(document).on("click", "#sidebar-find_me", function() {
                console.log("DEBUG: Find Me button clicked");
                getLocation();
            });
        """)
    )

def create_navbar_decorations():
    return [
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
        ui.nav_control(
            ui.div(
                ui.output_text("status_last_update_status", inline=True),
                style="display: flex; align-items: center; padding: 0 1rem; color: white; font-size: 0.875rem;"
            )
        ),
        ui.nav_control(ui.input_dark_mode(id="color_mode")),
    ]
