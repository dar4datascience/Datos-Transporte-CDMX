"""
Tests for vehicle filtering logic.
"""
import pytest
from scripts.filter_vehicles import VehicleFilter


class TestVehicleFilter:
    """Test vehicle filtering."""
    
    def test_filter_initialization(self, temp_metadata_file):
        """Test filter can be initialized."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        assert filter_obj.metadata is not None
        assert len(filter_obj.lines) == 2
        assert len(filter_obj.trip_to_route) == 4
    
    def test_get_route_line_mapping(self, temp_metadata_file):
        """Test route_id to line_number mapping."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        mapping = filter_obj.get_route_line_mapping()
        
        assert mapping['19492'] == '1'
        assert mapping['19491'] == '1'
        assert mapping['19563'] == '2'
        assert mapping['19562'] == '2'
    
    def test_filter_by_line(self, temp_metadata_file, sample_vehicles):
        """Test filtering vehicles by line number."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        
        line1_vehicles = filter_obj.filter_by_line(sample_vehicles, '1')
        assert len(line1_vehicles) == 2
        assert all(v['line_number'] == '1' for v in line1_vehicles)
        assert all(v['line_color'] == '#D40D0D' for v in line1_vehicles)
        
        line2_vehicles = filter_obj.filter_by_line(sample_vehicles, '2')
        assert len(line2_vehicles) == 1
        assert line2_vehicles[0]['line_number'] == '2'
        assert line2_vehicles[0]['line_color'] == '#8D1A96'
    
    def test_filter_empty_vehicles(self, temp_metadata_file):
        """Test filtering with empty vehicle list."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        result = filter_obj.filter_by_line([], '1')
        assert result == []
    
    def test_filter_nonexistent_line(self, temp_metadata_file, sample_vehicles):
        """Test filtering for line that doesn't exist."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        result = filter_obj.filter_by_line(sample_vehicles, '99')
        assert result == []
    
    def test_get_all_vehicles_with_lines(self, temp_metadata_file, sample_vehicles):
        """Test enriching all vehicles with line info."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        enriched = filter_obj.get_all_vehicles_with_lines(sample_vehicles)
        
        assert len(enriched) == 3
        assert all('line_number' in v for v in enriched)
        assert all('line_color' in v for v in enriched)
    
    def test_get_line_info(self, temp_metadata_file):
        """Test getting info for specific line."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        
        line1_info = filter_obj.get_line_info('1')
        assert line1_info is not None
        assert line1_info['color'] == '#D40D0D'
        assert len(line1_info['routes']) == 2
        
        nonexistent = filter_obj.get_line_info('99')
        assert nonexistent is None
    
    def test_get_all_lines(self, temp_metadata_file):
        """Test getting list of all lines."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        lines = filter_obj.get_all_lines()
        
        assert len(lines) == 2
        assert lines[0]['line_number'] == '1'
        assert lines[1]['line_number'] == '2'
        assert all('color' in line for line in lines)
        assert all('route_count' in line for line in lines)
    
    def test_vehicle_without_route_id(self, temp_metadata_file):
        """Test vehicle with only trip_id (no route_id)."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        
        vehicles = [{
            'vehicle_id': 'V999',
            'trip_id': '19492_1',
            'latitude': 19.4326,
            'longitude': -99.1332,
            'timestamp': 1234567890
        }]
        
        filtered = filter_obj.filter_by_line(vehicles, '1')
        assert len(filtered) == 1
        assert filtered[0]['line_number'] == '1'
    
    def test_invalid_line_selection(self, temp_metadata_file, sample_vehicles):
        """Test handling of invalid line selection."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        
        result = filter_obj.filter_by_line(sample_vehicles, '')
        assert result == []
        
        result = filter_obj.filter_by_line(sample_vehicles, None)
        assert result == []
