"""
Tests for static GTFS processing.
"""
import pytest
import json
from scripts.process_gtfs_static import GTFSStaticProcessor


class TestGTFSStaticProcessor:
    """Test static GTFS data processing."""
    
    def test_processor_initialization(self, temp_gtfs_dir):
        """Test processor can be initialized."""
        processor = GTFSStaticProcessor(str(temp_gtfs_dir))
        assert processor.gtfs_dir == temp_gtfs_dir
        assert processor.conn is not None
    
    def test_load_routes(self, temp_gtfs_dir):
        """Test loading routes from routes.txt."""
        processor = GTFSStaticProcessor(str(temp_gtfs_dir))
        routes = processor.load_routes()
        
        assert len(routes) == 4
        assert routes[0]['line_number'] == '1'
        assert routes[0]['route_color'] == 'D40D0D'
        assert routes[2]['line_number'] == '2'
    
    def test_create_trip_route_mapping(self, temp_gtfs_dir):
        """Test creating trip_id to route_id mapping."""
        processor = GTFSStaticProcessor(str(temp_gtfs_dir))
        mapping = processor.create_trip_route_mapping()
        
        assert len(mapping) == 4
        assert mapping['19492_1'] == '19492'
        assert mapping['19491_1'] == '19491'
        assert mapping['19563_1'] == '19563'
    
    def test_get_line_metadata(self, temp_gtfs_dir):
        """Test getting line metadata."""
        processor = GTFSStaticProcessor(str(temp_gtfs_dir))
        lines = processor.get_line_metadata()
        
        assert '1' in lines
        assert '2' in lines
        assert lines['1']['color'] == '#D40D0D'
        assert lines['1']['text_color'] == '#FFFFFF'
        assert len(lines['1']['routes']) == 2
        assert len(lines['2']['routes']) == 2
    
    def test_export_metadata(self, temp_gtfs_dir, tmp_path):
        """Test exporting metadata to JSON."""
        processor = GTFSStaticProcessor(str(temp_gtfs_dir))
        output_file = tmp_path / "test_metadata.json"
        
        metadata = processor.export_metadata(str(output_file))
        
        assert output_file.exists()
        assert 'lines' in metadata
        assert 'trip_to_route' in metadata
        
        with open(output_file, 'r') as f:
            loaded_metadata = json.load(f)
        
        assert loaded_metadata == metadata
    
    def test_route_color_formatting(self, temp_gtfs_dir):
        """Test route colors are properly formatted with #."""
        processor = GTFSStaticProcessor(str(temp_gtfs_dir))
        lines = processor.get_line_metadata()
        
        for line_num, line_data in lines.items():
            assert line_data['color'].startswith('#')
            assert len(line_data['color']) == 7
    
    def test_missing_gtfs_dir(self):
        """Test handling of missing GTFS directory."""
        processor = GTFSStaticProcessor("/nonexistent/path")
        
        with pytest.raises(Exception):
            processor.load_routes()
