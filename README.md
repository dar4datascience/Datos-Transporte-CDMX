# Datos-Transporte-CDMX

Rastreador en tiempo real del Metrobús de la Ciudad de México usando datos GTFS-RT.

[![Tests](https://github.com/dar4datascience/Datos-Transporte-CDMX/actions/workflows/quarto-publish.yml/badge.svg)](https://github.com/dar4datascience/Datos-Transporte-CDMX/actions/workflows/quarto-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚌 Demo

- **GitHub Pages (WASM)**: [https://dar4datascience.github.io/Datos-Transporte-CDMX/](https://dar4datascience.github.io/Datos-Transporte-CDMX/) - Aplicación con Pyodide/WASM, 100% en el navegador
- **Posit Connect**: [https://dar4datascience-datos-transporte-cdmx.share.connect.posit.cloud/](https://dar4datascience-datos-transporte-cdmx.share.connect.posit.cloud/) - Aplicación Shiny Python full fledge con backend

## ✨ Características

- 📍 Mapa interactivo con ubicaciones de vehículos en tiempo real
- 🚌 Filtrado por línea (1-7)
- 📊 Tabla de datos con información detallada
- 🔄 Auto-actualización cada 30 segundos
- 🤖 Datos actualizados cada 5 minutos vía GitHub Actions
- 🌐 100% en el navegador - no requiere servidor backend
- ✅ Suite completa de tests (74% coverage)

## 🛠️ Tecnologías

- **Quarto** + **Pyodide** (Python WASM)
- **Leaflet.js** para mapas
- **DuckDB** para procesamiento de datos
- **Playwright** para fetch de datos (bypass CORS)
- **pytest** para testing
- **GitHub Pages** para hosting

## 📦 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/dar4datascience/Datos-Transporte-CDMX.git
cd Datos-Transporte-CDMX

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements-dev.txt

# Instalar Playwright browsers
playwright install chromium

# Procesar datos GTFS estáticos
python scripts/process_gtfs_static.py Metrobus_GTFS_ESTATICO data/routes_metadata.json

# Fetch live vehicle data
python scripts/fetch_organillero.py data/live_vehicles.json

# Ejecutar tests
pytest tests/ -v --cov=scripts

# Renderizar sitio Quarto
quarto render

# Servir localmente
quarto preview
```

## 📊 Datos

### GTFS Estático
Incluido en `Metrobus_GTFS_ESTATICO/`:
- `routes.txt` - Información de rutas
- `trips.txt` - Viajes programados
- `stops.txt` - Paradas
- `shapes.txt` - Geometrías de rutas

### GTFS Realtime
Feeds en tiempo real del Metrobús:
- **Ubicación de vehículos**: `https://datosabiertos.metropolitanos.mx/gtfsrt/vehicle_position.bin`
- **Actualización de viajes**: `https://datosabiertos.metropolitanos.mx/gtfsrt/trip_update.bin`
- **Alertas**: `https://datosabiertos.metropolitanos.mx/gtfsrt/alert.bin`

**Nota**: Requiere registro en [metrobus.cdmx.gob.mx](https://metrobus.cdmx.gob.mx/portal-ciudadano/datos-abiertos)

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=scripts --cov-report=html

# Tests específicos
pytest tests/test_gtfs_rt_fetch.py -v
pytest tests/test_filtering.py -v
```

## 📁 Estructura

```
Datos-Transporte-CDMX/
├── index.qmd                    # Página principal
├── about.qmd                    # Acerca de
├── _quarto.yml                  # Config Quarto
├── data/
│   ├── routes_metadata.json    # Metadatos procesados
│   ├── live_vehicles.json      # Datos en vivo (actualizado cada 5min)
│   └── sample_vehicles.json    # Datos de respaldo
├── scripts/
│   ├── fetch_organillero.py    # Fetch live data (Playwright)
│   ├── fetch_gtfs_rt.py        # Fetch GTFS-RT
│   ├── process_gtfs_static.py  # Procesar GTFS estático
│   └── filter_vehicles.py      # Filtrar vehículos
├── tests/                       # Suite de tests
│   ├── conftest.py             # Fixtures
│   ├── test_gtfs_rt_fetch.py
│   ├── test_static_processing.py
│   ├── test_filtering.py
│   └── test_integration.py
└── .github/workflows/
    ├── quarto-publish.yml      # CI/CD
    └── update-live-data.yml    # Auto-update data (every 5min)
```

## 🚀 Despliegue

El sitio se despliega automáticamente a GitHub Pages:

**Sitio web** (push a `main`):
1. Tests se ejecutan primero
2. Si pasan, se procesa GTFS estático
3. Se renderiza sitio Quarto
4. Se despliega a GitHub Pages

**Datos en vivo** (cada 5 minutos):
1. GitHub Action ejecuta `fetch_organillero.py`
2. Playwright fetch de Organillero API
3. Actualiza `data/live_vehicles.json`
4. Commit automático → trigger re-deploy

## 📝 Roadmap

- [x] Auto-refresh cada 30s
- [x] Datos en vivo vía GitHub Actions
- [ ] Clustering de marcadores
- [ ] Histórico de posiciones
- [ ] Estimación de tiempos de llegada
- [ ] Soporte para Metro CDMX

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

Los datos del Metrobús CDMX son datos abiertos del Gobierno de la Ciudad de México.

## 🙏 Agradecimientos

- [El Organillero](https://organillero.heliouz.com) por Heliouz - Proveedor de la API en tiempo real
- Gobierno de la Ciudad de México - Datos abiertos GTFS del Metrobús

## 📚 Referencias

- [GTFS Realtime Reference](https://gtfs.org/realtime/)
- [Metrobús Datos Abiertos](https://metrobus.cdmx.gob.mx/portal-ciudadano/datos-abiertos)
- [Quarto Documentation](https://quarto.org/)
- [Pyodide Documentation](https://pyodide.org/)
