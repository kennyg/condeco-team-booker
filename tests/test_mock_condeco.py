"""
Tests for the mock Condeco API functionality.
"""

import pytest
import datetime
from team_booker.mock_condeco import MockCondeco, MockResponse

class TestMockCondeco:
    """Tests for MockCondeco class."""
    
    @pytest.fixture
    def mock_condeco(self):
        """Create a MockCondeco instance."""
        return MockCondeco("test.condecosoftware.com")
    
    def test_initialization(self, mock_condeco):
        """Test MockCondeco initialization."""
        assert mock_condeco.unique_key == "test.condecosoftware.com"
        assert mock_condeco.bookings == {}
    
    def test_decode_jwt(self):
        """Test JWT decoding."""
        result = MockCondeco.decode_jwt("fake_token")
        
        assert result['id'] == 'mock_session_12345'
        assert result['exp'] == 9999999999
        assert result['user_id'] == 'mock_user_123'
        assert result['email'] == 'test@company.com'
    
    def test_send_magic_link(self, mock_condeco):
        """Test magic link sending."""
        response = mock_condeco.sendMagicLink("test@example.com")
        
        assert isinstance(response, MockResponse)
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] is True
        assert data['email'] == "test@example.com"
    
    def test_login_with_magic_link(self, mock_condeco):
        """Test magic link validation."""
        response = mock_condeco.loginWithMagicLink("validation123")
        
        assert isinstance(response, MockResponse)
        assert response.status_code == 200
        
        data = response.json()
        assert 'token' in data
        assert data['user']['email'] == 'test@company.com'
    
    def test_search_room_by_features(self, mock_condeco):
        """Test room search functionality."""
        search_request = {
            'accessToken': 'mock_session',
            'locationID': 'LOC001',
            'groupID': 'GRP001',
            'startDate': '01/02/2024',
            'userID': 'USR001'
        }
        
        response = mock_condeco.searchRoomByFeatures('mock_token', search_request)
        
        assert isinstance(response, MockResponse)
        assert response.status_code == 200
        
        data = response.json()
        assert data['CallResponse']['ResponseCode'] == 100
        assert 'SearchedRooms' in data
        
        # Should return available rooms
        rooms = data['SearchedRooms']
        assert len(rooms) > 0
        
        # Check that all returned rooms are bookable
        for room in rooms:
            assert room['CanBeBooked'] is True
    
    def test_book_room_success(self, mock_condeco):
        """Test successful room booking."""
        response = mock_condeco.bookRoom(
            access_token='mock_token',
            session_token='mock_session',
            user_id='USR001',
            location_id='LOC001',
            group_id='GRP001',
            floor_id='FLR001',
            room_id='R001',
            start_date='01/02/2024|3',
            booking_type=3
        )
        
        assert isinstance(response, MockResponse)
        assert response.status_code == 200
        
        data = response.json()
        assert data['CallResponse']['ResponseCode'] == 100
        assert 'CreatedBookings' in data
        
        booking = data['CreatedBookings'][0]
        assert booking['RoomID'] == 'R001'
        assert 'BookingID' in booking
        
        # Check that booking was stored
        assert len(mock_condeco.bookings) == 1
    
    def test_book_room_already_booked(self, mock_condeco):
        """Test booking a room that's already booked."""
        # First booking
        mock_condeco.bookRoom(
            access_token='mock_token',
            session_token='mock_session',
            user_id='USR001',
            location_id='LOC001',
            group_id='GRP001',
            floor_id='FLR001',
            room_id='R001',
            start_date='01/02/2024|3',
            booking_type=3
        )
        
        # Try to book same room again
        response = mock_condeco.bookRoom(
            access_token='mock_token',
            session_token='mock_session',
            user_id='USR002',
            location_id='LOC001',
            group_id='GRP001',
            floor_id='FLR001',
            room_id='R001',
            start_date='01/02/2024|3',
            booking_type=3
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['CallResponse']['ResponseCode'] == 400
        assert 'already booked' in data['CallResponse']['ResponseMessage']
    
    def test_book_nonexistent_room(self, mock_condeco):
        """Test booking a room that doesn't exist."""
        response = mock_condeco.bookRoom(
            access_token='mock_token',
            session_token='mock_session',
            user_id='USR001',
            location_id='LOC001',
            group_id='GRP001',
            floor_id='FLR001',
            room_id='NONEXISTENT',
            start_date='01/02/2024|3',
            booking_type=3
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['CallResponse']['ResponseCode'] == 400
        assert 'not found' in data['CallResponse']['ResponseMessage']
    
    def test_search_after_booking(self, mock_condeco):
        """Test that booked rooms don't appear in subsequent searches."""
        # Book a room
        mock_condeco.bookRoom(
            access_token='mock_token',
            session_token='mock_session',
            user_id='USR001',
            location_id='LOC001',
            group_id='GRP001',
            floor_id='FLR001',
            room_id='R001',
            start_date='01/02/2024|3',
            booking_type=3
        )
        
        # Search for rooms on same date
        search_request = {
            'startDate': '01/02/2024',
            'locationID': 'LOC001'
        }
        
        response = mock_condeco.searchRoomByFeatures('mock_token', search_request)
        data = response.json()
        rooms = data['SearchedRooms']
        
        # R001 should not be in results (already booked)
        room_ids = [room['RoomID'] for room in rooms]
        assert 'R001' not in room_ids
    
    def test_get_and_clear_bookings(self, mock_condeco):
        """Test booking management methods."""
        # Make a booking
        mock_condeco.bookRoom(
            access_token='mock_token',
            session_token='mock_session',
            user_id='USR001',
            location_id='LOC001',
            group_id='GRP001',
            floor_id='FLR001',
            room_id='R001',
            start_date='01/02/2024|3',
            booking_type=3
        )
        
        # Get bookings
        bookings = mock_condeco.get_bookings()
        assert len(bookings) == 1
        assert '01/02/2024_R001' in bookings
        
        # Clear bookings
        mock_condeco.clear_bookings()
        assert len(mock_condeco.get_bookings()) == 0

class TestMockResponse:
    """Tests for MockResponse class."""
    
    def test_mock_response_creation(self):
        """Test MockResponse creation and methods."""
        data = {"test": "data", "number": 123}
        response = MockResponse(200, data)
        
        assert response.status_code == 200
        assert response.json() == data
        assert '"test": "data"' in response.text
        assert '"number": 123' in response.text