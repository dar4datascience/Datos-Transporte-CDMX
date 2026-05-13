"""
Filter vehicle positions by line number using DuckDB.
"""
import duckdb
import json
from typing import List, Dict, Optional


class VehicleFilter:
    """Filter and query vehicle data."""
    
    def __init__(self, metadata_file: str):
        """Load route metadata."""
        with open(metadata_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        self.trip_to_route = self.metadata['trip_to_route']
        self.lines = self.metadata['lines']
        
        self.conn = duckdb.connect(':memory:')
    
    def get_route_line_mapping(self) -> Dict[str, str]:
        """Create mapping from route_id to line_number."""
        route_to_line = {}
        for line_num, line_data in self.lines.items():
            for route in line_data['routes']:
                route_to_line[route['route_id']] = line_num
        return route_to_line
    
    def filter_by_line(self, vehicles: List[Dict], line_number: str) -> List[Dict]:
        """
        Filter vehicles by line number.
        
        Args:
            vehicles: List of vehicle dicts from GTFS-RT
            line_number: Line number to filter (1-7)
        
        Returns:
            Filtered list of vehicles with added line_number field
        """
        if not vehicles:
            return []
        
        route_to_line = self.get_route_line_mapping()
        
        filtered = []
        for vehicle in vehicles:
            trip_id = vehicle.get('trip_id')
            route_id = vehicle.get('route_id')
            
            if not route_id and trip_id:
                route_id = self.trip_to_route.get(trip_id)
            
            if route_id:
                line = route_to_line.get(route_id)
                if line == line_number:
                    vehicle_copy = vehicle.copy()
                    vehicle_copy['line_number'] = line
                    vehicle_copy['line_color'] = self.lines[line]['color']
                    filtered.append(vehicle_copy)
        
        return filtered
    
    def get_all_vehicles_with_lines(self, vehicles: List[Dict]) -> List[Dict]:
        """Add line_number and line_color to all vehicles."""
        route_to_line = self.get_route_line_mapping()
        
        enriched = []
        for vehicle in vehicles:
            trip_id = vehicle.get('trip_id')
            route_id = vehicle.get('route_id')
            
            if not route_id and trip_id:
                route_id = self.trip_to_route.get(trip_id)
            
            if route_id:
                line = route_to_line.get(route_id)
                if line:
                    vehicle_copy = vehicle.copy()
                    vehicle_copy['line_number'] = line
                    vehicle_copy['line_color'] = self.lines[line]['color']
                    enriched.append(vehicle_copy)
        
        return enriched
    
    def get_line_info(self, line_number: str) -> Optional[Dict]:
        """Get metadata for a specific line."""
        return self.lines.get(line_number)
    
    def get_all_lines(self) -> List[Dict]:
        """Get list of all lines with metadata."""
        return [
            {
                'line_number': line_num,
                'color': data['color'],
                'text_color': data['text_color'],
                'route_count': len(data['routes'])
            }
            for line_num, data in sorted(self.lines.items())
        ]


if __name__ == "__main__":
    filter_obj = VehicleFilter("data/routes_metadata.json")
    
    print("Available lines:")
    for line in filter_obj.get_all_lines():
        print(f"  Line {line['line_number']}: {line['color']} ({line['route_count']} routes)")
    
    sample_vehicles = [
        {
            'vehicle_id': 'V001',
            'trip_id': '19492_1',
            'route_id': '19492',
            'latitude': 19.4326,
            'longitude': -99.1332,
            'timestamp': 1234567890
        }
    ]
    
    print("\nTest filtering line 1:")
    filtered = filter_obj.filter_by_line(sample_vehicles, '1')
    print(f"  Found {len(filtered)} vehicles")
    if filtered:
        print(f"  Sample: {filtered[0]}")
