"""
Fetch and parse GTFS-RT vehicle positions from Metrobús CDMX.
"""
import requests
from google.transit import gtfs_realtime_pb2
from typing import List, Dict, Optional
import time


class GTFSRealtimeFetcher:
    """Fetches and parses GTFS-RT feeds."""
    
    VEHICLE_POSITION_URL = "https://datosabiertos.metropolitanos.mx/gtfsrt/vehicle_position.bin"
    TRIP_UPDATE_URL = "https://datosabiertos.metropolitanos.mx/gtfsrt/trip_update.bin"
    ALERT_URL = "https://datosabiertos.metropolitanos.mx/gtfsrt/alert.bin"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def fetch_vehicle_positions(self) -> List[Dict]:
        """
        Fetch and parse vehicle positions.
        
        Returns:
            List of dicts with vehicle data: {
                'vehicle_id': str,
                'trip_id': str,
                'route_id': str,
                'latitude': float,
                'longitude': float,
                'timestamp': int,
                'speed': float (optional),
                'bearing': float (optional)
            }
        """
        try:
            response = requests.get(self.VEHICLE_POSITION_URL, timeout=self.timeout)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            vehicles = []
            for entity in feed.entity:
                if entity.HasField('vehicle'):
                    vehicle = entity.vehicle
                    
                    vehicle_data = {
                        'vehicle_id': vehicle.vehicle.id if vehicle.vehicle.HasField('id') else None,
                        'trip_id': vehicle.trip.trip_id if vehicle.trip.HasField('trip_id') else None,
                        'route_id': vehicle.trip.route_id if vehicle.trip.HasField('route_id') else None,
                        'latitude': vehicle.position.latitude if vehicle.position.HasField('latitude') else None,
                        'longitude': vehicle.position.longitude if vehicle.position.HasField('longitude') else None,
                        'timestamp': vehicle.timestamp if vehicle.HasField('timestamp') else int(time.time()),
                    }
                    
                    if vehicle.position.HasField('speed'):
                        vehicle_data['speed'] = vehicle.position.speed
                    if vehicle.position.HasField('bearing'):
                        vehicle_data['bearing'] = vehicle.position.bearing
                    
                    if vehicle_data['latitude'] and vehicle_data['longitude']:
                        vehicles.append(vehicle_data)
            
            return vehicles
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch GTFS-RT data: {e}")
        except Exception as e:
            raise Exception(f"Failed to parse GTFS-RT data: {e}")
    
    def fetch_trip_updates(self) -> List[Dict]:
        """Fetch and parse trip updates."""
        try:
            response = requests.get(self.TRIP_UPDATE_URL, timeout=self.timeout)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            updates = []
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip_update = entity.trip_update
                    updates.append({
                        'trip_id': trip_update.trip.trip_id if trip_update.trip.HasField('trip_id') else None,
                        'route_id': trip_update.trip.route_id if trip_update.trip.HasField('route_id') else None,
                        'timestamp': trip_update.timestamp if trip_update.HasField('timestamp') else None,
                    })
            
            return updates
            
        except Exception as e:
            raise Exception(f"Failed to fetch trip updates: {e}")


if __name__ == "__main__":
    fetcher = GTFSRealtimeFetcher()
    
    print("Fetching vehicle positions...")
    vehicles = fetcher.fetch_vehicle_positions()
    print(f"Found {len(vehicles)} vehicles")
    
    if vehicles:
        print("\nSample vehicle:")
        print(vehicles[0])
