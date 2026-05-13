"""
Pytest fixtures for GTFS testing.
"""
import pytest
import json
from pathlib import Path
from google.transit import gtfs_realtime_pb2


@pytest.fixture
def sample_routes_data():
    """Sample routes.txt data."""
    return """route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_url,route_color,route_text_color,route_sort_order,continuous_pickup,continuous_drop_off
19492,1339,1,L01a01-1 indios verdes - dr. gálvez,,3,https://www.metrobus.cdmx.gob.mx/mapas-de-sistema/mapa-linea-1,D40D0D,FFFFFF,,,
19491,1339,1,L01a01-2 dr. gálvez - indios verdes,,3,https://www.metrobus.cdmx.gob.mx/mapas-de-sistema/mapa-linea-1,D40D0D,FFFFFF,,,
19563,1339,2,L02c01-1 tepalcates - tacubaya,,3,https://www.metrobus.cdmx.gob.mx/mapas-de-sistema/mapa-linea-2,8D1A96,FFFFFF,,,
19562,1339,2,L02c01-2 tacubaya - tepalcates,,3,https://www.metrobus.cdmx.gob.mx/mapas-de-sistema/mapa-linea-2,8D1A96,FFFFFF,,,
"""


@pytest.fixture
def sample_trips_data():
    """Sample trips.txt data."""
    return """route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,block_id,shape_id,wheelchair_accessible,bikes_allowed
19492,1,19492_1,DR. GÁLVEZ,,0,,,1,2
19491,1,19491_1,INDIOS VERDES,,1,,,1,2
19563,1,19563_1,TACUBAYA,,0,,,1,2
19562,1,19562_1,TEPALCATES,,1,,,1,2
"""


@pytest.fixture
def temp_gtfs_dir(tmp_path, sample_routes_data, sample_trips_data):
    """Create temporary GTFS directory with sample files."""
    gtfs_dir = tmp_path / "gtfs"
    gtfs_dir.mkdir()
    
    (gtfs_dir / "routes.txt").write_text(sample_routes_data)
    (gtfs_dir / "trips.txt").write_text(sample_trips_data)
    
    return gtfs_dir


@pytest.fixture
def sample_metadata():
    """Sample route metadata."""
    return {
        "lines": {
            "1": {
                "line_number": "1",
                "color": "#D40D0D",
                "text_color": "#FFFFFF",
                "routes": [
                    {"route_id": "19492", "name": "L01a01-1 indios verdes - dr. gálvez"},
                    {"route_id": "19491", "name": "L01a01-2 dr. gálvez - indios verdes"}
                ],
                "url": "https://www.metrobus.cdmx.gob.mx/mapas-de-sistema/mapa-linea-1"
            },
            "2": {
                "line_number": "2",
                "color": "#8D1A96",
                "text_color": "#FFFFFF",
                "routes": [
                    {"route_id": "19563", "name": "L02c01-1 tepalcates - tacubaya"},
                    {"route_id": "19562", "name": "L02c01-2 tacubaya - tepalcates"}
                ],
                "url": "https://www.metrobus.cdmx.gob.mx/mapas-de-sistema/mapa-linea-2"
            }
        },
        "trip_to_route": {
            "19492_1": "19492",
            "19491_1": "19491",
            "19563_1": "19563",
            "19562_1": "19562"
        }
    }


@pytest.fixture
def temp_metadata_file(tmp_path, sample_metadata):
    """Create temporary metadata JSON file."""
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text(json.dumps(sample_metadata, indent=2))
    return metadata_file


@pytest.fixture
def sample_vehicles():
    """Sample vehicle position data."""
    return [
        {
            'vehicle_id': 'V001',
            'trip_id': '19492_1',
            'route_id': '19492',
            'latitude': 19.4326,
            'longitude': -99.1332,
            'timestamp': 1234567890
        },
        {
            'vehicle_id': 'V002',
            'trip_id': '19491_1',
            'route_id': '19491',
            'latitude': 19.4500,
            'longitude': -99.1400,
            'timestamp': 1234567891
        },
        {
            'vehicle_id': 'V003',
            'trip_id': '19563_1',
            'route_id': '19563',
            'latitude': 19.4000,
            'longitude': -99.1500,
            'timestamp': 1234567892
        }
    ]


@pytest.fixture
def sample_gtfs_rt_feed():
    """Create sample GTFS-RT protobuf feed."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.timestamp = 1234567890
    
    entity1 = feed.entity.add()
    entity1.id = "vehicle_1"
    entity1.vehicle.vehicle.id = "V001"
    entity1.vehicle.trip.trip_id = "19492_1"
    entity1.vehicle.trip.route_id = "19492"
    entity1.vehicle.position.latitude = 19.4326
    entity1.vehicle.position.longitude = -99.1332
    entity1.vehicle.timestamp = 1234567890
    
    entity2 = feed.entity.add()
    entity2.id = "vehicle_2"
    entity2.vehicle.vehicle.id = "V002"
    entity2.vehicle.trip.trip_id = "19491_1"
    entity2.vehicle.trip.route_id = "19491"
    entity2.vehicle.position.latitude = 19.4500
    entity2.vehicle.position.longitude = -99.1400
    entity2.vehicle.timestamp = 1234567891
    
    return feed.SerializeToString()
