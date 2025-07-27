"""
Core booking functionality for Condeco team areas.
Handles searching and booking team spaces with comprehensive error handling.
"""

import sys
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Dynamic import of Condeco module with multiple fallback paths
def _import_condeco():
    """Import the Condeco module with multiple fallback paths."""
    potential_paths = [
        # Relative to the package installation
        Path(__file__).parent.parent / 'Hybrid-Worker' / 'Python' / 'src',
        # Current working directory
        Path.cwd() / 'Hybrid-Worker' / 'Python' / 'src',
        # Parent directories (for development)
        Path.cwd().parent / 'Hybrid-Worker' / 'Python' / 'src',
        Path.cwd().parent.parent / 'Hybrid-Worker' / 'Python' / 'src'
    ]
    
    for path in potential_paths:
        if path.exists():
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
            try:
                from hybrid_worker.condeco import Condeco
                return Condeco
            except ImportError:
                continue
    
    # If all else fails, check if it's already available in the environment
    try:
        from hybrid_worker.condeco import Condeco
        return Condeco
    except ImportError:
        pass
    
    raise ImportError(
        "Cannot import Condeco module. Please ensure Hybrid-Worker is cloned "
        "in the project directory or current working directory."
    )

# Import Condeco at module level but only when actually needed
Condeco = None

logger = logging.getLogger(__name__)

class BookingResult(Enum):
    """Booking operation results."""
    SUCCESS = "success"
    NO_AVAILABILITY = "no_availability"
    AUTH_ERROR = "auth_error"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class BookingAttempt:
    """Represents a booking attempt result."""
    date: datetime.date
    result: BookingResult
    message: str
    booking_id: Optional[str] = None
    room_name: Optional[str] = None
    room_id: Optional[str] = None

@dataclass
class TeamAreaConfig:
    """Configuration for team area booking."""
    location_id: str
    group_id: str
    user_id: str
    floor_id: Optional[str] = None
    team_area_keywords: List[str] = None
    preferred_rooms: List[str] = None
    
    def __post_init__(self):
        if self.team_area_keywords is None:
            self.team_area_keywords = ['team', 'collaboration', 'meeting', 'huddle']
        if self.preferred_rooms is None:
            self.preferred_rooms = []

class TeamAreaBooker:
    """Handles team area booking operations."""
    
    def __init__(self, condeco, config: TeamAreaConfig):
        """Initialize the booker.
        
        Args:
            condeco: Configured Condeco instance
            config: Team area booking configuration
        """
        self.condeco = condeco
        self.config = config
        self.session_token = None
    
    def set_session_token(self, access_token: str) -> None:
        """Set session token from JWT.
        
        Args:
            access_token: JWT access token
        """
        try:
            # Check if we're using MockCondeco
            if hasattr(self.condeco, '__class__') and 'Mock' in self.condeco.__class__.__name__:
                # Use mock JWT decoding
                decoded_jwt = self.condeco.__class__.decode_jwt(access_token)
            else:
                # Use real Condeco JWT decoding
                global Condeco
                if Condeco is None:
                    Condeco = _import_condeco()
                decoded_jwt = Condeco.decode_jwt(access_token)
            
            self.session_token = decoded_jwt['id']
        except Exception as e:
            logger.error(f"Error decoding JWT: {e}")
            raise ValueError("Invalid access token")
    
    def find_available_team_areas(
        self, 
        access_token: str, 
        date: datetime.date
    ) -> List[Dict[str, Any]]:
        """Find available team areas for a specific date.
        
        Args:
            access_token: JWT access token
            date: Date to search for availability
            
        Returns:
            List of available room dictionaries
        """
        date_string = date.strftime('%d/%m/%Y')
        
        # Get booking constants (handle mock vs real Condeco)
        if hasattr(self.condeco, 'BOOKING_TYPE'):
            # Mock Condeco or real Condeco instance
            BOOKING_TYPE = self.condeco.BOOKING_TYPE
            WORKSPACE_TYPE = self.condeco.WORKSPACE_TYPE
        else:
            # Real Condeco class constants
            global Condeco
            if Condeco is None:
                Condeco = _import_condeco()
            BOOKING_TYPE = Condeco.BOOKING_TYPE
            WORKSPACE_TYPE = Condeco.WORKSPACE_TYPE
        
        # Search for available rooms
        room_search_request = {
            'accessToken': self.session_token,
            'locationID': self.config.location_id,
            'groupID': self.config.group_id,
            'floorID': self.config.floor_id,
            'bookingType': BOOKING_TYPE['AllDay'],
            'startDate': date_string,
            'userID': self.config.user_id,
            'wsTypeID': WORKSPACE_TYPE['Room']
        }
        
        try:
            response = self.condeco.searchRoomByFeatures(
                access_token=access_token,
                room_search_request=room_search_request
            )
            
            response_json = response.json()
            
            if response_json['CallResponse']['ResponseCode'] != 100:
                logger.error(f"Room search failed: {response_json['CallResponse']['ResponseMessage']}")
                return []
            
            available_rooms = []
            searched_rooms = response_json.get('SearchedRooms', [])
            
            # Filter by preferred rooms first
            if self.config.preferred_rooms:
                for room in searched_rooms:
                    if (room.get('CanBeBooked', False) and 
                        room.get('RoomName', '').lower() in [p.lower() for p in self.config.preferred_rooms]):
                        available_rooms.append(room)
            
            # If no preferred rooms available, look for keyword matches
            if not available_rooms:
                for room in searched_rooms:
                    if room.get('CanBeBooked', False):
                        room_name = room.get('RoomName', '').lower()
                        if any(keyword in room_name for keyword in self.config.team_area_keywords):
                            available_rooms.append(room)
            
            # If still no matches, return any available rooms
            if not available_rooms:
                available_rooms = [room for room in searched_rooms if room.get('CanBeBooked', False)]
            
            logger.info(f"Found {len(available_rooms)} available rooms for {date}")
            return available_rooms
            
        except Exception as e:
            logger.error(f"Error searching for rooms: {e}")
            return []
    
    def book_room(
        self, 
        access_token: str, 
        room: Dict[str, Any], 
        date: datetime.date
    ) -> BookingAttempt:
        """Book a specific room for a date.
        
        Args:
            access_token: JWT access token
            room: Room dictionary from search results
            date: Date to book
            
        Returns:
            BookingAttempt with result details
        """
        date_string = date.strftime('%d/%m/%Y')
        room_name = room.get('RoomName', 'Unknown')
        room_id = room.get('RoomID')
        
        try:
            logger.info(f"Attempting to book '{room_name}' (#{room_id}) for {date}")
            
            # Get booking constants
            if hasattr(self.condeco, 'BOOKING_TYPE'):
                BOOKING_TYPE = self.condeco.BOOKING_TYPE
            else:
                global Condeco
                if Condeco is None:
                    Condeco = _import_condeco()
                BOOKING_TYPE = Condeco.BOOKING_TYPE
            
            response = self.condeco.bookRoom(
                access_token=access_token,
                session_token=self.session_token,
                user_id=self.config.user_id,
                location_id=self.config.location_id,
                group_id=self.config.group_id,
                floor_id=self.config.floor_id,
                room_id=room_id,
                start_date=date_string,
                booking_type=BOOKING_TYPE['AllDay']
            )
            
            response_json = response.json()
            
            if response_json['CallResponse']['ResponseCode'] == 100:
                booking_id = None
                if response_json.get("CreatedBookings"):
                    booking_id = response_json["CreatedBookings"][0]["BookingID"]
                
                return BookingAttempt(
                    date=date,
                    result=BookingResult.SUCCESS,
                    message=f"Successfully booked {room_name}",
                    booking_id=booking_id,
                    room_name=room_name,
                    room_id=room_id
                )
            else:
                error_msg = response_json["CallResponse"]["ResponseMessage"]
                logger.error(f"Booking failed: {error_msg}")
                
                return BookingAttempt(
                    date=date,
                    result=BookingResult.API_ERROR,
                    message=f"Booking failed: {error_msg}",
                    room_name=room_name,
                    room_id=room_id
                )
                
        except Exception as e:
            logger.error(f"Error booking room: {e}")
            return BookingAttempt(
                date=date,
                result=BookingResult.UNKNOWN_ERROR,
                message=f"Error booking room: {str(e)}",
                room_name=room_name,
                room_id=room_id
            )
    
    def book_date(self, access_token: str, date: datetime.date) -> BookingAttempt:
        """Book a team area for a specific date.
        
        Args:
            access_token: JWT access token
            date: Date to book
            
        Returns:
            BookingAttempt with result details
        """
        if not self.session_token:
            self.set_session_token(access_token)
        
        # Find available rooms
        available_rooms = self.find_available_team_areas(access_token, date)
        
        if not available_rooms:
            return BookingAttempt(
                date=date,
                result=BookingResult.NO_AVAILABILITY,
                message="No available team areas found"
            )
        
        # Try to book the first available room
        return self.book_room(access_token, available_rooms[0], date)
    
    def book_multiple_dates(
        self, 
        access_token: str, 
        dates: List[datetime.date],
        dry_run: bool = False
    ) -> List[BookingAttempt]:
        """Book team areas for multiple dates.
        
        Args:
            access_token: JWT access token
            dates: List of dates to book
            dry_run: If True, only simulate booking without actually booking
            
        Returns:
            List of BookingAttempt results
        """
        results = []
        
        if not self.session_token:
            self.set_session_token(access_token)
        
        for date in dates:
            logger.info(f"Processing booking for {date} (dry_run={dry_run})")
            
            if dry_run:
                # In dry run mode, just check availability
                available_rooms = self.find_available_team_areas(access_token, date)
                
                if available_rooms:
                    room = available_rooms[0]
                    result = BookingAttempt(
                        date=date,
                        result=BookingResult.SUCCESS,
                        message=f"[DRY RUN] Would book '{room.get('RoomName', 'Unknown')}'",
                        room_name=room.get('RoomName'),
                        room_id=room.get('RoomID')
                    )
                else:
                    result = BookingAttempt(
                        date=date,
                        result=BookingResult.NO_AVAILABILITY,
                        message="[DRY RUN] No available team areas found"
                    )
            else:
                # Actually book
                result = self.book_date(access_token, date)
            
            results.append(result)
            
            # Small delay between requests
            import time
            time.sleep(1)
        
        return results

def get_tuesday_wednesday_dates(weeks_ahead: int = 4) -> List[datetime.date]:
    """Get upcoming Tuesday and Wednesday dates.
    
    Args:
        weeks_ahead: Number of weeks to look ahead
        
    Returns:
        List of Tuesday and Wednesday dates
    """
    dates = []
    today = datetime.date.today()
    
    for week in range(weeks_ahead):
        # Calculate start of week (Monday)
        start_of_week = today + datetime.timedelta(days=-today.weekday(), weeks=week)
        
        # Tuesday (day 1) and Wednesday (day 2)
        tuesday = start_of_week + datetime.timedelta(days=1)
        wednesday = start_of_week + datetime.timedelta(days=2)
        
        # Only add future dates
        if tuesday > today:
            dates.append(tuesday)
        if wednesday > today:
            dates.append(wednesday)
    
    return sorted(dates)