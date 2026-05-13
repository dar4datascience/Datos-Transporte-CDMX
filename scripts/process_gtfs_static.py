"""
Process static GTFS data to extract route metadata using DuckDB.
"""
import duckdb
import json
from pathlib import Path
from typing import Dict, List


class GTFSStaticProcessor:
    """Process static GTFS files with DuckDB."""
    
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = Path(gtfs_dir)
        self.conn = duckdb.connect(':memory:')
        
    def load_routes(self) -> List[Dict]:
        """
        Load and parse routes.txt.
        
        Returns:
            List of route dicts with metadata.
        """
        routes_file = self.gtfs_dir / "routes.txt"
        
        query = f"""
        SELECT 
            CAST(route_id AS VARCHAR) as route_id,
            CAST(route_short_name AS VARCHAR) as line_number,
            route_long_name as line_name,
            route_color,
            route_text_color,
            route_url
        FROM read_csv_auto('{routes_file}')
        WHERE route_short_name IN ('1', '2', '3', '4', '5', '6', '7')
        ORDER BY CAST(route_short_name AS INTEGER)
        """
        
        result = self.conn.execute(query).fetchall()
        columns = ['route_id', 'line_number', 'line_name', 'route_color', 'route_text_color', 'route_url']
        
        routes = []
        for row in result:
            routes.append(dict(zip(columns, row)))
        
        return routes
    
    def create_trip_route_mapping(self) -> Dict[str, str]:
        """
        Create mapping from trip_id to route_id.
        
        Returns:
            Dict mapping trip_id -> route_id
        """
        trips_file = self.gtfs_dir / "trips.txt"
        
        query = f"""
        SELECT DISTINCT
            CAST(trip_id AS VARCHAR) as trip_id,
            CAST(route_id AS VARCHAR) as route_id
        FROM read_csv_auto('{trips_file}')
        """
        
        result = self.conn.execute(query).fetchall()
        return {trip_id: route_id for trip_id, route_id in result}
    
    def get_line_metadata(self) -> Dict[str, Dict]:
        """
        Get metadata for each line (1-7).
        
        Returns:
            Dict mapping line_number -> {color, name, routes}
        """
        routes = self.load_routes()
        
        lines = {}
        for route in routes:
            line_num = route['line_number']
            if line_num not in lines:
                lines[line_num] = {
                    'line_number': line_num,
                    'color': f"#{route['route_color']}" if route['route_color'] else "#000000",
                    'text_color': f"#{route['route_text_color']}" if route['route_text_color'] else "#FFFFFF",
                    'routes': [],
                    'url': route['route_url']
                }
            
            lines[line_num]['routes'].append({
                'route_id': route['route_id'],
                'name': route['line_name']
            })
        
        return lines
    
    def export_metadata(self, output_file: str):
        """Export processed metadata to JSON."""
        metadata = {
            'lines': self.get_line_metadata(),
            'trip_to_route': self.create_trip_route_mapping()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"Metadata exported to {output_file}")
        return metadata


if __name__ == "__main__":
    import sys
    
    gtfs_dir = sys.argv[1] if len(sys.argv) > 1 else "Metrobus_GTFS_ESTATICO"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/routes_metadata.json"
    
    processor = GTFSStaticProcessor(gtfs_dir)
    metadata = processor.export_metadata(output_file)
    
    print(f"\nProcessed {len(metadata['lines'])} lines")
    print(f"Mapped {len(metadata['trip_to_route'])} trips")
    
    print("\nLines:")
    for line_num, line_data in sorted(metadata['lines'].items()):
        print(f"  Line {line_num}: {line_data['color']} ({len(line_data['routes'])} routes)")
