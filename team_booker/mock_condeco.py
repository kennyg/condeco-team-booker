"""
Mock Condeco API for testing purposes.
Simulates Condeco API responses without making real API calls.
"""

import json
import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MockCondeco:
    """Mock implementation of Condeco API for testing."""
    
    # Mock data constants
    MOCK_ROOMS = [
        {
            "RoomID": "R001",
            "RoomName": "Team Collaboration Space A",
            "CanBeBooked": True,
            "Capacity": 8,
            "Features": ["Whiteboard", "Video Conference"]
        },
        {
            "RoomID": "R002", 
            "RoomName": "Huddle Room B",
            "CanBeBooked": True,
            "Capacity": 4,
            "Features": ["TV Screen"]
        },
        {
            "RoomID": "R003",
            "RoomName": "Executive Boardroom",
            "CanBeBooked": False,  # Already booked
            "Capacity": 12,
            "Features": ["Video Conference", "Presentation Equipment"]
        },
        {
            "RoomID": "R004",
            "RoomName": "Team Workshop Space",
            "CanBeBooked": True,
            "Capacity": 10,
            "Features": ["Whiteboard", "Moveable Tables"]
        }
    ]
    
    BOOKING_TYPE = {
        'None': 0,
        'Morning': 1,
        'Evening': 2,
        'AllDay': 3
    }
    
    WORKSPACE_TYPE = {
        'None': 0,
        'Room': 1,
        'Desk': 2,
        'TeamDay': 3
    }
    
    def __init__(self, unique_key: str):
        """Initialize mock Condeco instance.
        
        Args:
            unique_key: Mock unique key
        """
        self.unique_key = unique_key
        self.bookings = {}  # Track bookings by date
        logger.info(f"Initialized MockCondeco with unique_key: {unique_key}")
    
    @staticmethod
    def decode_jwt(token: str) -> Dict[str, Any]:
        """Mock JWT decoding.
        
        Args:
            token: Mock JWT token
            
        Returns:
            Mock decoded JWT payload
        """
        logger.info("Mock: Decoding JWT token")
        # Return mock JWT payload with far future expiration
        return {
            'id': 'mock_session_12345',
            'exp': 9999999999,  # Far future timestamp
            'user_id': 'mock_user_123',
            'email': 'test@company.com'
        }
    
    def sendMagicLink(self, email: str) -> 'MockResponse':
        """Mock magic link sending.
        
        Args:
            email: Email address
            
        Returns:
            Mock response object
        """
        logger.info(f"Mock: Sending magic link to {email}")
        
        response_data = {
            "success": True,
            "message": "Magic link sent successfully",
            "email": email
        }
        
        return MockResponse(200, response_data)
    
    def loginWithMagicLink(self, validation_key: str) -> 'MockResponse':
        """Mock magic link validation.
        
        Args:
            validation_key: Validation key from email
            
        Returns:
            Mock response with JWT token
        """
        logger.info(f"Mock: Validating magic link with key: {validation_key}")
        
        # Simulate successful login
        response_data = {
            "token": "mock_jwt_token_12345",
            "user": {
                "id": "mock_user_123",
                "email": "test@company.com",
                "name": "Test User"
            }
        }
        
        return MockResponse(200, response_data)
    
    def searchRoomByFeatures(self, access_token: str, room_search_request: Dict[str, Any]) -> 'MockResponse':
        """Mock room search by features.
        
        Args:
            access_token: JWT access token
            room_search_request: Search parameters
            
        Returns:
            Mock response with available rooms
        """
        logger.info(f"Mock: Searching rooms with request: {room_search_request}")
        
        # Get date from request
        search_date = room_search_request.get('startDate', 'Unknown')
        location_id = room_search_request.get('locationID')
        
        # Filter rooms based on date and existing bookings
        available_rooms = []
        for room in self.MOCK_ROOMS:
            # Check if room is already booked for this date
            booking_key = f"{search_date}_{room['RoomID']}"
            if booking_key not in self.bookings and room['CanBeBooked']:
                available_rooms.append(room.copy())
        
        response_data = {
            'CallResponse': {
                'ResponseCode': 100,
                'ResponseMessage': 'Success'
            },
            'SearchedRooms': available_rooms
        }
        
        logger.info(f"Mock: Found {len(available_rooms)} available rooms")
        return MockResponse(200, response_data)
    
    def bookRoom(
        self, 
        access_token: str,
        session_token: str,
        user_id: str,
        location_id: str,
        group_id: str,
        floor_id: str,
        room_id: str,
        start_date: str,
        booking_type: int
    ) -> 'MockResponse':
        """Mock room booking.
        
        Args:
            access_token: JWT access token
            session_token: Session token
            user_id: User ID
            location_id: Location ID
            group_id: Group ID
            floor_id: Floor ID
            room_id: Room ID to book
            start_date: Start date string
            booking_type: Type of booking
            
        Returns:
            Mock response with booking confirmation
        """
        # Extract just the date part (before the |)
        date_part = start_date.split('|')[0] if '|' in start_date else start_date
        
        logger.info(f"Mock: Booking room {room_id} for date {date_part}")
        
        # Find the room
        room = next((r for r in self.MOCK_ROOMS if r['RoomID'] == room_id), None)
        if not room:
            response_data = {
                'CallResponse': {
                    'ResponseCode': 400,
                    'ResponseMessage': 'Room not found'
                }
            }
            return MockResponse(400, response_data)
        
        # Check if room is available
        booking_key = f"{date_part}_{room_id}"
        if booking_key in self.bookings:
            response_data = {
                'CallResponse': {
                    'ResponseCode': 400,
                    'ResponseMessage': 'Room already booked for this date'
                }
            }
            return MockResponse(400, response_data)
        
        # Create booking
        booking_id = f"BK{len(self.bookings) + 1001}"
        self.bookings[booking_key] = {
            'booking_id': booking_id,
            'room_id': room_id,
            'room_name': room['RoomName'],
            'date': date_part,
            'user_id': user_id,
            'booking_type': booking_type
        }
        
        response_data = {
            'CallResponse': {
                'ResponseCode': 100,
                'ResponseMessage': 'Booking successful'
            },
            'CreatedBookings': [
                {
                    'BookingID': booking_id,
                    'RoomID': room_id,
                    'RoomName': room['RoomName'],
                    'StartDate': date_part,
                    'BookingType': booking_type
                }
            ]
        }
        
        logger.info(f"Mock: Successfully booked room {room['RoomName']} with booking ID {booking_id}")
        return MockResponse(200, response_data)
    
    def get_bookings(self) -> Dict[str, Any]:
        """Get all current mock bookings (for testing purposes).
        
        Returns:
            Dictionary of all bookings
        """
        return self.bookings.copy()
    
    def clear_bookings(self) -> None:
        """Clear all mock bookings (for testing purposes)."""
        self.bookings.clear()
        logger.info("Mock: Cleared all bookings")

class MockResponse:
    """Mock HTTP response object."""
    
    def __init__(self, status_code: int, data: Dict[str, Any]):
        """Initialize mock response.
        
        Args:
            status_code: HTTP status code
            data: Response data
        """
        self.status_code = status_code
        self.data = data
    
    def json(self) -> Dict[str, Any]:
        """Return JSON data.
        
        Returns:
            Response data as dictionary
        """
        return self.data
    
    @property 
    def text(self) -> str:
        """Return response as text.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.data, indent=2)