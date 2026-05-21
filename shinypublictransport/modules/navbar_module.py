from shiny import ui

def geolocation_script():
    return ui.head_content(
        ui.tags.script("""
            function getLocation() {
                if (navigator.geolocation) {
                    const options = {
                        enableHighAccuracy: false,
                        timeout: 10000,
                        maximumAge: 60000
                    };
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            console.log("Geolocation: Found coordinates", position.coords.latitude, position.coords.longitude);
                            const pos = {
                                lat: position.coords.latitude,
                                lng: position.coords.longitude
                            };
                            Shiny.setInputValue("main_map-user_location", pos, {priority: "event"});
                        },
                        (error) => {
                            console.warn("Geolocation error:", error.message);
                        },
                        options
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
        ui.nav_control(ui.input_dark_mode(id="color_mode")),
    ]
