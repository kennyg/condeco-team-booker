"""
Tests for the booking functionality.
"""

import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from team_booker.booking import (
    TeamAreaBooker, 
    TeamAreaConfig, 
    BookingResult, 
    get_tuesday_wednesday_dates
)

class TestTeamAreaConfig:
    """Tests for TeamAreaConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = TeamAreaConfig(
            location_id="LOC001",
            group_id="GRP001", 
            user_id="USR001"
        )
        
        assert config.location_id == "LOC001"
        assert config.group_id == "GRP001"
        assert config.user_id == "USR001"
        assert config.floor_id is None
        assert config.team_area_keywords == ['team', 'collaboration', 'meeting', 'huddle']
        assert config.preferred_rooms == []
    
    def test_custom_initialization(self):
        """Test custom values override defaults."""
        config = TeamAreaConfig(
            location_id="LOC001",
            group_id="GRP001",
            user_id="USR001",
            floor_id="FLR001",
            team_area_keywords=['custom', 'keywords'],
            preferred_rooms=['Room A', 'Room B']
        )
        
        assert config.floor_id == "FLR001"
        assert config.team_area_keywords == ['custom', 'keywords']
        assert config.preferred_rooms == ['Room A', 'Room B']

class TestGetTuesdayWednesdayDates:
    """Tests for date generation function."""
    
    def test_get_dates_basic(self):
        """Test basic date generation."""
        with patch('team_booker.booking.datetime') as mock_datetime:
            # Mock today as Monday, 2024-01-01
            mock_datetime.date.today.return_value = datetime.date(2024, 1, 1)
            mock_datetime.timedelta = datetime.timedelta
            
            dates = get_tuesday_wednesday_dates(weeks_ahead=2)
            
            expected_dates = [
                datetime.date(2024, 1, 2),   # Tuesday week 0
                datetime.date(2024, 1, 3),   # Wednesday week 0  
                datetime.date(2024, 1, 9),   # Tuesday week 1
                datetime.date(2024, 1, 10),  # Wednesday week 1
            ]
            
            assert dates == expected_dates
    
    def test_get_dates_future_only(self):
        """Test that only future dates are returned."""
        with patch('team_booker.booking.datetime') as mock_datetime:
            # Mock today as Wednesday, 2024-01-03
            mock_datetime.date.today.return_value = datetime.date(2024, 1, 3)
            mock_datetime.timedelta = datetime.timedelta
            
            dates = get_tuesday_wednesday_dates(weeks_ahead=2)
            
            # Should not include Tuesday 1/2 (past) or Wednesday 1/3 (today)
            expected_dates = [
                datetime.date(2024, 1, 9),   # Tuesday week 1
                datetime.date(2024, 1, 10),  # Wednesday week 1
            ]
            
            assert dates == expected_dates

class TestTeamAreaBooker:
    """Tests for TeamAreaBooker class."""
    
    @pytest.fixture
    def mock_condeco(self):
        """Create a mock Condeco instance."""
        return Mock()
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return TeamAreaConfig(
            location_id="LOC001",
            group_id="GRP001",
            user_id="USR001",
            team_area_keywords=['team', 'meeting']
        )
    
    @pytest.fixture
    def booker(self, mock_condeco, config):
        """Create a TeamAreaBooker instance."""
        return TeamAreaBooker(mock_condeco, config)
    
    def test_initialization(self, mock_condeco, config):
        """Test booker initialization."""
        booker = TeamAreaBooker(mock_condeco, config)
        
        assert booker.condeco == mock_condeco
        assert booker.config == config
        assert booker.session_token is None
    
    @patch('team_booker.booking.Condeco.decode_jwt')
    def test_set_session_token(self, mock_decode_jwt, booker):
        """Test setting session token from JWT."""
        mock_decode_jwt.return_value = {'id': 'session123'}
        
        booker.set_session_token('fake_jwt_token')
        
        assert booker.session_token == 'session123'
        mock_decode_jwt.assert_called_once_with('fake_jwt_token')
    
    @patch('team_booker.booking.Condeco.decode_jwt')
    def test_set_session_token_invalid(self, mock_decode_jwt, booker):
        """Test setting session token with invalid JWT."""
        mock_decode_jwt.side_effect = Exception("Invalid JWT")
        
        with pytest.raises(ValueError, match="Invalid access token"):
            booker.set_session_token('invalid_token')
    
    def test_find_available_team_areas_success(self, booker, mock_condeco):
        """Test successful room search."""
        booker.session_token = 'session123'
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'CallResponse': {'ResponseCode': 100},
            'SearchedRooms': [
                {
                    'RoomID': 'R001',
                    'RoomName': 'Team Room A',
                    'CanBeBooked': True
                },
                {
                    'RoomID': 'R002', 
                    'RoomName': 'Conference Room B',
                    'CanBeBooked': True
                },
                {
                    'RoomID': 'R003',
                    'RoomName': 'Team Huddle Space',
                    'CanBeBooked': False
                }
            ]
        }
        mock_condeco.searchRoomByFeatures.return_value = mock_response
        
        date = datetime.date(2024, 1, 2)
        rooms = booker.find_available_team_areas('fake_token', date)
        
        # Should return only bookable rooms with team keywords
        assert len(rooms) == 1
        assert rooms[0]['RoomName'] == 'Team Room A'
    
    def test_find_available_team_areas_preferred_rooms(self, mock_condeco):
        """Test preferred rooms take priority."""
        config = TeamAreaConfig(
            location_id="LOC001",
            group_id="GRP001",
            user_id="USR001",
            preferred_rooms=['Conference Room B']
        )
        booker = TeamAreaBooker(mock_condeco, config)
        booker.session_token = 'session123'
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'CallResponse': {'ResponseCode': 100},
            'SearchedRooms': [
                {
                    'RoomID': 'R001',
                    'RoomName': 'Team Room A', 
                    'CanBeBooked': True
                },
                {
                    'RoomID': 'R002',
                    'RoomName': 'Conference Room B',
                    'CanBeBooked': True
                }
            ]
        }
        mock_condeco.searchRoomByFeatures.return_value = mock_response
        
        date = datetime.date(2024, 1, 2)
        rooms = booker.find_available_team_areas('fake_token', date)
        
        # Should return preferred room first
        assert len(rooms) == 1
        assert rooms[0]['RoomName'] == 'Conference Room B'
    
    def test_book_room_success(self, booker, mock_condeco):
        """Test successful room booking."""
        booker.session_token = 'session123'
        
        # Mock successful booking response
        mock_response = Mock()
        mock_response.json.return_value = {
            'CallResponse': {'ResponseCode': 100},
            'CreatedBookings': [{'BookingID': 'B123'}]
        }
        mock_condeco.bookRoom.return_value = mock_response
        
        room = {
            'RoomID': 'R001',
            'RoomName': 'Team Room A'
        }
        date = datetime.date(2024, 1, 2)
        
        result = booker.book_room('fake_token', room, date)
        
        assert result.result == BookingResult.SUCCESS
        assert result.booking_id == 'B123'
        assert result.room_name == 'Team Room A'
        assert result.date == date
    
    def test_book_room_failure(self, booker, mock_condeco):
        """Test failed room booking."""
        booker.session_token = 'session123'
        
        # Mock failed booking response
        mock_response = Mock()
        mock_response.json.return_value = {
            'CallResponse': {
                'ResponseCode': 400,
                'ResponseMessage': 'Room not available'
            }
        }
        mock_condeco.bookRoom.return_value = mock_response
        
        room = {
            'RoomID': 'R001',
            'RoomName': 'Team Room A'
        }
        date = datetime.date(2024, 1, 2)
        
        result = booker.book_room('fake_token', room, date)
        
        assert result.result == BookingResult.API_ERROR
        assert 'Room not available' in result.message
        assert result.booking_id is None
    
    @patch('team_booker.booking.TeamAreaBooker.find_available_team_areas')
    def test_book_date_no_availability(self, mock_find_rooms, booker):
        """Test booking when no rooms are available."""
        mock_find_rooms.return_value = []
        booker.session_token = 'session123'
        
        date = datetime.date(2024, 1, 2)
        result = booker.book_date('fake_token', date)
        
        assert result.result == BookingResult.NO_AVAILABILITY
        assert 'No available team areas found' in result.message
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('team_booker.booking.TeamAreaBooker.book_date')
    def test_book_multiple_dates_dry_run(self, mock_book_date, mock_sleep, booker):
        """Test dry run mode for multiple dates."""
        booker.session_token = 'session123'
        
        with patch.object(booker, 'find_available_team_areas') as mock_find:
            mock_find.return_value = [{
                'RoomID': 'R001',
                'RoomName': 'Team Room A'
            }]
            
            dates = [datetime.date(2024, 1, 2), datetime.date(2024, 1, 3)]
            results = booker.book_multiple_dates('fake_token', dates, dry_run=True)
            
            assert len(results) == 2
            for result in results:
                assert result.result == BookingResult.SUCCESS
                assert '[DRY RUN]' in result.message
            
            # Should not call actual booking in dry run
            mock_book_date.assert_not_called()