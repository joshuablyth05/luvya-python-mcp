from typing import Any, Dict, List, Optional
import httpx
import logging
from mcp.server.fastmcp import FastMCP
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("luvya")

# Configure logging to stderr (required for MCP)
logging.basicConfig(level=logging.INFO, stream=os.sys.stderr)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dnqvfftyzetqwryfjptk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRucXZmZnR5emV0cXdyeWZqcHRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MDk2MDcsImV4cCI6MjA3NTk4NTYwN30.SSqt0dSLXbeJ8gUz_Y8Zn9SsamQ8twe7kI2Ezz35x6g")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Data models
class Trip:
    def __init__(self, id: str, title: str, description: str, start_date: str, end_date: str, user_id: str):
        self.id = id
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id

class TripEvent:
    def __init__(self, id: str, trip_id: str, title: str, description: str, event_date: str, location: str):
        self.id = id
        self.trip_id = trip_id
        self.title = title
        self.description = description
        self.event_date = event_date
        self.location = location

class Notification:
    def __init__(self, id: str, user_id: str, title: str, message: str, is_read: bool, created_at: str):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.message = message
        self.is_read = is_read
        self.created_at = created_at

# Helper functions
async def make_supabase_request(table: str, operation: str = "select", data: Optional[Dict] = None) -> Dict[str, Any] | None:
    """Make a request to Supabase with proper error handling."""
    try:
        if operation == "select":
            response = supabase.table(table).select("*").execute()
        elif operation == "insert" and data:
            response = supabase.table(table).insert(data).execute()
        elif operation == "update" and data:
            response = supabase.table(table).update(data).execute()
        elif operation == "delete":
            response = supabase.table(table).delete().execute()
        else:
            return None
        
        return response.data if response.data else None
    except Exception as e:
        logging.error(f"Supabase request failed: {e}")
        return None

def format_trip(trip_data: Dict) -> str:
    """Format trip data into a readable string."""
    return f"""
Trip: {trip_data.get('title', 'Unknown')}
Description: {trip_data.get('description', 'No description')}
Dates: {trip_data.get('start_date', 'Unknown')} to {trip_data.get('end_date', 'Unknown')}
ID: {trip_data.get('id', 'Unknown')}
"""

def format_event(event_data: Dict) -> str:
    """Format event data into a readable string."""
    return f"""
Event: {event_data.get('title', 'Unknown')}
Description: {event_data.get('description', 'No description')}
Date: {event_data.get('event_date', 'Unknown')}
Location: {event_data.get('location', 'Unknown')}
"""

def format_notification(notification_data: Dict) -> str:
    """Format notification data into a readable string."""
    status = "Read" if notification_data.get('is_read', False) else "Unread"
    return f"""
{status}: {notification_data.get('title', 'Unknown')}
Message: {notification_data.get('message', 'No message')}
Date: {notification_data.get('created_at', 'Unknown')}
"""

# MCP Tools
@mcp.tool()
async def hello_world() -> str:
    """Say hello from the Luvya MCP server.
    
    This is a simple test tool to verify the MCP server is working correctly.
    """
    return "Hello from Luvya! Your MCP server is working perfectly! 🚀"

@mcp.tool()
async def get_trips() -> str:
    """Get all trips from the database.
    
    Returns a list of all trips with their details including title, description, and dates.
    """
    trips_data = await make_supabase_request("trips")
    
    if not trips_data:
        return "Unable to fetch trips or no trips found."
    
    if not trips_data:
        return "No trips found in the database."
    
    formatted_trips = [format_trip(trip) for trip in trips_data]
    return "\n---\n".join(formatted_trips)

@mcp.tool()
async def create_trip(title: str, description: str, start_date: str, end_date: str, user_id: str = "default-user") -> str:
    """Create a new trip in the database.
    
    Args:
        title: The title of the trip
        description: Description of the trip
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        user_id: User ID (defaults to 'default-user')
    """
    trip_data = {
        "title": title,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id
    }
    
    result = await make_supabase_request("trips", "insert", trip_data)
    
    if result:
        return f"Successfully created trip: {title}"
    else:
        return f"Failed to create trip: {title}"

@mcp.tool()
async def get_trip_events(trip_id: str) -> str:
    """Get all events for a specific trip.
    
    Args:
        trip_id: The ID of the trip to get events for
    """
    try:
        response = supabase.table("trip_events").select("*").eq("trip_id", trip_id).execute()
        events_data = response.data
        
        if not events_data:
            return f"No events found for trip {trip_id}."
        
        formatted_events = [format_event(event) for event in events_data]
        return "\n---\n".join(formatted_events)
    except Exception as e:
        logging.error(f"Error fetching trip events: {e}")
        return f"Error fetching events for trip {trip_id}."

@mcp.tool()
async def create_trip_event(trip_id: str, title: str, description: str, event_date: str, location: str) -> str:
    """Create a new event for a trip.
    
    Args:
        trip_id: The ID of the trip
        title: Title of the event
        description: Description of the event
        event_date: Date of the event in YYYY-MM-DD format
        location: Location of the event
    """
    event_data = {
        "trip_id": trip_id,
        "title": title,
        "description": description,
        "event_date": event_date,
        "location": location
    }
    
    result = await make_supabase_request("trip_events", "insert", event_data)
    
    if result:
        return f"Successfully created event: {title}"
    else:
        return f"Failed to create event: {title}"

@mcp.tool()
async def get_notifications(user_id: str = "default-user") -> str:
    """Get all notifications for a user.
    
    Args:
        user_id: The ID of the user (defaults to 'default-user')
    """
    try:
        response = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        notifications_data = response.data
        
        if not notifications_data:
            return f"No notifications found for user {user_id}."
        
        formatted_notifications = [format_notification(notification) for notification in notifications_data]
        return "\n---\n".join(formatted_notifications)
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        return f"Error fetching notifications for user {user_id}."

@mcp.tool()
async def mark_notification_read(notification_id: str) -> str:
    """Mark a notification as read.
    
    Args:
        notification_id: The ID of the notification to mark as read
    """
    try:
        response = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        
        if response.data:
            return f"Successfully marked notification {notification_id} as read."
        else:
            return f"Failed to mark notification {notification_id} as read."
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        return f"Error marking notification {notification_id} as read."

# MCP Resources (Widgets)
@mcp.resource("widget://trips")
async def trips_widget() -> str:
    """Interactive trips management widget."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Luvya Trips</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }
        .trip-card { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
        .trip-title { font-size: 18px; font-weight: bold; color: #007bff; margin-bottom: 8px; }
        .trip-dates { color: #6c757d; font-size: 14px; margin-bottom: 8px; }
        .trip-description { color: #495057; line-height: 1.5; }
        .btn { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #0056b3; }
        .loading { text-align: center; color: #6c757d; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🗺️ My Trips</h1>
        <div id="trips-container">
            <div class="loading">Loading trips...</div>
        </div>
    </div>
    
    <script>
        async function loadTrips() {
            try {
                const response = await fetch('/api/trips');
                const trips = await response.json();
                
                const container = document.getElementById('trips-container');
                if (trips.length === 0) {
                    container.innerHTML = '<p>No trips found. Create your first trip!</p>';
                    return;
                }
                
                container.innerHTML = trips.map(trip => `
                    <div class="trip-card">
                        <div class="trip-title">${trip.title}</div>
                        <div class="trip-dates">${trip.start_date} to ${trip.end_date}</div>
                        <div class="trip-description">${trip.description}</div>
                    </div>
                `).join('');
            } catch (error) {
                document.getElementById('trips-container').innerHTML = 
                    '<div class="error">Error loading trips: ' + error.message + '</div>';
            }
        }
        
        loadTrips();
    </script>
</body>
</html>
"""

@mcp.resource("widget://events")
async def events_widget() -> str:
    """Interactive trip events management widget."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Luvya Trip Events</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { color: #333; border-bottom: 2px solid #28a745; padding-bottom: 10px; margin-bottom: 20px; }
        .event-card { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
        .event-title { font-size: 18px; font-weight: bold; color: #28a745; margin-bottom: 8px; }
        .event-date { color: #6c757d; font-size: 14px; margin-bottom: 8px; }
        .event-location { color: #6c757d; font-size: 14px; margin-bottom: 8px; }
        .event-description { color: #495057; line-height: 1.5; }
        .loading { text-align: center; color: #6c757d; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">📅 Trip Events</h1>
        <div id="events-container">
            <div class="loading">Loading events...</div>
        </div>
    </div>
    
    <script>
        async function loadEvents() {
            try {
                // For demo purposes, we'll show a message
                document.getElementById('events-container').innerHTML = 
                    '<p>Select a trip to view its events, or create new events for your trips!</p>';
            } catch (error) {
                document.getElementById('events-container').innerHTML = 
                    '<div class="error">Error loading events: ' + error.message + '</div>';
            }
        }
        
        loadEvents();
    </script>
</body>
</html>
"""

@mcp.resource("widget://notifications")
async def notifications_widget() -> str:
    """Interactive notifications management widget."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Luvya Notifications</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { color: #333; border-bottom: 2px solid #ffc107; padding-bottom: 10px; margin-bottom: 20px; }
        .notification-card { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
        .notification-title { font-size: 18px; font-weight: bold; color: #ffc107; margin-bottom: 8px; }
        .notification-date { color: #6c757d; font-size: 14px; margin-bottom: 8px; }
        .notification-message { color: #495057; line-height: 1.5; }
        .unread { border-left: 4px solid #ffc107; }
        .read { border-left: 4px solid #6c757d; opacity: 0.7; }
        .loading { text-align: center; color: #6c757d; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🔔 Notifications</h1>
        <div id="notifications-container">
            <div class="loading">Loading notifications...</div>
        </div>
    </div>
    
    <script>
        async function loadNotifications() {
            try {
                // For demo purposes, we'll show a message
                document.getElementById('notifications-container').innerHTML = 
                    '<p>Your notifications will appear here. Stay updated with your trip activities!</p>';
            } catch (error) {
                document.getElementById('notifications-container').innerHTML = 
                    '<div class="error">Error loading notifications: ' + error.message + '</div>';
            }
        }
        
        loadNotifications();
    </script>
</body>
</html>
"""

def main():
    """Initialize and run the MCP server."""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
