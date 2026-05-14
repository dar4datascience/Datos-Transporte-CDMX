"""
Fetch real-time vehicle data from Organillero API using Playwright.
Bypasses CORS restrictions by running in browser context.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def fetch_organillero_data(output_file: str = None):
    """
    Fetch vehicle data from Organillero API using Playwright.
    
    Args:
        output_file: Path to save JSON data. If None, prints to stdout.
    
    Returns:
        dict: Vehicle data with timestamp and buses list
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to Organillero site to establish origin
        page.goto('https://organillero.heliouz.com/')
        
        # Enable console logging
        page.on('console', lambda msg: print(f"BROWSER: {msg.text}"))
        
        # Fetch data using browser's fetch API (no CORS restrictions)
        result = page.evaluate("""
            async () => {
                try {
                    console.log('Fetching from Organillero...');
                    const response = await fetch('https://organillero.heliouz.com/api/realtime');
                    console.log('Response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    const data = await response.json();
                    console.log('Data received, buses:', data.buses?.length || 0);
                    return { success: true, data: data };
                } catch (error) {
                    console.error('Fetch error:', error);
                    return { success: false, error: error.message, stack: error.stack };
                }
            }
        """)
        
        browser.close()
        
        if not result['success']:
            raise Exception(f"Failed to fetch: {result['error']}")
        
        data = result['data']
        
        # Transform to our format
        vehicles = []
        for bus in data.get('buses', []):
            vehicles.append({
                'vehicle_id': bus.get('id'),
                'route_id': int(bus.get('route', 0)),
                'latitude': bus.get('lat'),
                'longitude': bus.get('lon'),
                'bearing': bus.get('brg'),
                'speed': bus.get('spd'),
                'timestamp': data.get('ts')
            })
        
        output = {
            'feed_timestamp': data.get('ts'),
            'total_vehicles': len(vehicles),
            'vehicles': vehicles
        }
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"✅ Saved {len(vehicles)} vehicles to {output_file}")
        else:
            print(json.dumps(output, indent=2))
        
        return output


if __name__ == '__main__':
    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_organillero_data(output_file)
