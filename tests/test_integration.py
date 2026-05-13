"""
Integration tests for end-to-end workflow.
"""
import pytest
import responses
from scripts.fetch_gtfs_rt import GTFSRealtimeFetcher
from scripts.filter_vehicles import VehicleFilter


class TestIntegration:
    """Test end-to-end workflows."""
    
    @responses.activate
    def test_fetch_and_filter_workflow(self, sample_gtfs_rt_feed, temp_metadata_file):
        """Test complete workflow: fetch → parse → filter."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=sample_gtfs_rt_feed,
            status=200
        )
        
        fetcher = GTFSRealtimeFetcher()
        vehicles = fetcher.fetch_vehicle_positions()
        
        assert len(vehicles) > 0
        
        filter_obj = VehicleFilter(str(temp_metadata_file))
        filtered = filter_obj.filter_by_line(vehicles, '1')
        
        assert len(filtered) > 0
        assert all(v['line_number'] == '1' for v in filtered)
        assert all('latitude' in v and 'longitude' in v for v in filtered)
    
    @responses.activate
    def test_fetch_enrich_all_vehicles(self, sample_gtfs_rt_feed, temp_metadata_file):
        """Test fetching and enriching all vehicles with line info."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=sample_gtfs_rt_feed,
            status=200
        )
        
        fetcher = GTFSRealtimeFetcher()
        vehicles = fetcher.fetch_vehicle_positions()
        
        filter_obj = VehicleFilter(str(temp_metadata_file))
        enriched = filter_obj.get_all_vehicles_with_lines(vehicles)
        
        assert len(enriched) == len(vehicles)
        assert all('line_number' in v for v in enriched)
        assert all('line_color' in v for v in enriched)
    
    def test_multiple_line_filtering(self, sample_vehicles, temp_metadata_file):
        """Test filtering same vehicles for different lines."""
        filter_obj = VehicleFilter(str(temp_metadata_file))
        
        line1 = filter_obj.filter_by_line(sample_vehicles, '1')
        line2 = filter_obj.filter_by_line(sample_vehicles, '2')
        
        assert len(line1) + len(line2) == len(sample_vehicles)
        
        line1_ids = {v['vehicle_id'] for v in line1}
        line2_ids = {v['vehicle_id'] for v in line2}
        assert line1_ids.isdisjoint(line2_ids)
    
    @responses.activate
    def test_error_recovery(self, temp_metadata_file):
        """Test system handles fetch errors gracefully."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=Exception("Network error"),
            status=500
        )
        
        fetcher = GTFSRealtimeFetcher()
        
        with pytest.raises(Exception):
            fetcher.fetch_vehicle_positions()
        
        filter_obj = VehicleFilter(str(temp_metadata_file))
        lines = filter_obj.get_all_lines()
        assert len(lines) > 0
