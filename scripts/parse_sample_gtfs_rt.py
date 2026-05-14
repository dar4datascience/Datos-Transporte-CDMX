"""
Parse sample GTFS-RT binary file to JSON.
"""
from google.transit import gtfs_realtime_pb2
import json
import sys
from datetime import datetime

def parse_gtfs_rt_binary(input_file, output_file):
    """Parse GTFS-RT binary file and save as JSON."""
    
    with open(input_file, 'rb') as f:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(f.read())
    
    # Extract feed metadata
    feed_timestamp = feed.header.timestamp if feed.header.HasField('timestamp') else None
    
    vehicles = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            v = entity.vehicle
            
            # Extract route_id and convert to int if possible
            route_id = v.trip.route_id if v.trip.HasField('route_id') else None
            if route_id:
                try:
                    route_id = int(route_id)
                except (ValueError, TypeError):
                    pass  # Keep as string if conversion fails
            
            vehicle_data = {
                'vehicle_id': v.vehicle.id if v.vehicle.HasField('id') else None,
                'trip_id': v.trip.trip_id if v.trip.HasField('trip_id') else None,
                'route_id': route_id,
                'latitude': v.position.latitude if v.position.HasField('latitude') else None,
                'longitude': v.position.longitude if v.position.HasField('longitude') else None,
                'timestamp': v.timestamp if v.HasField('timestamp') else None,
            }
            
            if v.position.HasField('speed'):
                vehicle_data['speed'] = v.position.speed
            if v.position.HasField('bearing'):
                vehicle_data['bearing'] = v.position.bearing
            
            if vehicle_data['latitude'] and vehicle_data['longitude']:
                vehicles.append(vehicle_data)
    
    # Create output with metadata
    output = {
        'feed_timestamp': feed_timestamp,
        'feed_timestamp_iso': datetime.fromtimestamp(feed_timestamp).isoformat() if feed_timestamp else None,
        'total_vehicles': len(vehicles),
        'vehicles': vehicles
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Extracted {len(vehicles)} vehicles from GTFS-RT feed")
    print(f"📅 Feed timestamp: {output['feed_timestamp_iso']}")
    print(f"💾 Saved to: {output_file}")
    
    # Show sample
    if vehicles:
        print(f"\n📊 Sample vehicle:")
        print(json.dumps(vehicles[0], indent=2))
    
    return output

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'Metrobus_GTFS_RT.proto'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'data/sample_vehicles.json'
    
    parse_gtfs_rt_binary(input_file, output_file)
