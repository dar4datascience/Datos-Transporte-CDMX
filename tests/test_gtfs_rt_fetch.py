"""
Tests for GTFS-RT fetching and parsing.
"""
import pytest
import responses
from scripts.fetch_gtfs_rt import GTFSRealtimeFetcher


class TestGTFSRealtimeFetcher:
    """Test GTFS-RT data fetching."""
    
    def test_fetcher_initialization(self):
        """Test fetcher can be initialized."""
        fetcher = GTFSRealtimeFetcher()
        assert fetcher.timeout == 10
        
        fetcher_custom = GTFSRealtimeFetcher(timeout=30)
        assert fetcher_custom.timeout == 30
    
    @responses.activate
    def test_fetch_vehicle_positions_success(self, sample_gtfs_rt_feed):
        """Test successful vehicle position fetch."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=sample_gtfs_rt_feed,
            status=200,
            content_type='application/octet-stream'
        )
        
        fetcher = GTFSRealtimeFetcher()
        vehicles = fetcher.fetch_vehicle_positions()
        
        assert len(vehicles) == 2
        assert vehicles[0]['vehicle_id'] == 'V001'
        assert vehicles[0]['trip_id'] == '19492_1'
        assert vehicles[0]['route_id'] == '19492'
        assert abs(vehicles[0]['latitude'] - 19.4326) < 0.0001
        assert abs(vehicles[0]['longitude'] - (-99.1332)) < 0.0001
    
    @responses.activate
    def test_fetch_vehicle_positions_network_error(self):
        """Test network error handling."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=Exception("Network error"),
            status=500
        )
        
        fetcher = GTFSRealtimeFetcher()
        with pytest.raises(Exception, match="Failed to (fetch|parse) GTFS-RT data"):
            fetcher.fetch_vehicle_positions()
    
    @responses.activate
    def test_fetch_vehicle_positions_malformed_data(self):
        """Test malformed protobuf handling."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=b"not a valid protobuf",
            status=200
        )
        
        fetcher = GTFSRealtimeFetcher()
        with pytest.raises(Exception, match="Failed to parse GTFS-RT data"):
            fetcher.fetch_vehicle_positions()
    
    @responses.activate
    def test_fetch_vehicle_positions_empty_feed(self):
        """Test empty feed handling."""
        from google.transit import gtfs_realtime_pb2
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        feed.header.timestamp = 1234567890
        
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=feed.SerializeToString(),
            status=200
        )
        
        fetcher = GTFSRealtimeFetcher()
        vehicles = fetcher.fetch_vehicle_positions()
        
        assert vehicles == []
    
    def test_vehicle_data_structure(self, sample_gtfs_rt_feed):
        """Test vehicle data has required fields."""
        responses.add(
            responses.GET,
            GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
            body=sample_gtfs_rt_feed,
            status=200
        )
        
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                GTFSRealtimeFetcher.VEHICLE_POSITION_URL,
                body=sample_gtfs_rt_feed,
                status=200
            )
            
            fetcher = GTFSRealtimeFetcher()
            vehicles = fetcher.fetch_vehicle_positions()
            
            if vehicles:
                vehicle = vehicles[0]
                required_fields = ['vehicle_id', 'trip_id', 'route_id', 'latitude', 'longitude', 'timestamp']
                for field in required_fields:
                    assert field in vehicle
                    assert vehicle[field] is not None
