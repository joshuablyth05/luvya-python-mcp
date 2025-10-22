#!/usr/bin/env python3
"""
Luvya Travel App MCP Server with FastMCP 2.0 and Supabase Integration
"""

from typing import Any, Dict, List, Optional
import logging
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging to stderr (required for MCP)
logging.basicConfig(level=logging.INFO, stream=os.sys.stderr)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dnqvfftyzetqwryfjptk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRucXZmZnR5emV0cXdyeWZqcHRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MDk2MDcsImV4cCI6MjA3NTk4NTYwN30.SSqt0dSLXbeJ8gUz_Y8Zn9SsamQ8twe7kI2Ezz35x6g")
JWT_SECRET = os.getenv("JWT_SECRET", "UOtwEuQaKcLtBOPNmWxCfbP39Zj3xa3hUFoFNWfy-i0")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastMCP server with proper OAuth configuration
base_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "https://luvya-python-mcp-production-abc123.up.railway.app")

# Configure JWT verification using FastMCP's built-in JWTVerifier
jwt_verifier = JWTVerifier(
    public_key=JWT_SECRET,  # Using our JWT secret as the symmetric key
    issuer=base_url,
    audience=f"{base_url}/mcp",
    algorithm="HS256"
)

mcp = FastMCP(
    "luvya-travel-app",
    auth=jwt_verifier
)

# Data models
class Trip:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.title = data.get("title")
        self.description = data.get("description")
        self.start_date = data.get("start_date")
        self.end_date = data.get("end_date")
        self.user_id = data.get("user_id")

class TripEvent:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.trip_id = data.get("trip_id")
        self.title = data.get("title")
        self.description = data.get("description")
        self.date = data.get("date")
        self.location = data.get("location")

class Notification:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.user_id = data.get("user_id")
        self.title = data.get("title")
        self.message = data.get("message")
        self.read = data.get("read", False)
        self.created_at = data.get("created_at")

# Helper functions for Supabase operations
async def make_supabase_request(table: str, operation: str = "select", data: Optional[Dict] = None, filters: Optional[Dict] = None) -> Dict[str, Any] | None:
    """Make a request to Supabase with proper error handling."""
    try:
        query = supabase.table(table)
        
        if operation == "select":
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.select("*").execute()
        elif operation == "insert" and data:
            response = query.insert(data).execute()
        elif operation == "update" and data and filters:
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.update(data).execute()
        elif operation == "delete" and filters:
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.delete().execute()
        else:
            return None
        
        return response.data if response.data else None
    except Exception as e:
        logging.error(f"Supabase request failed: {e}")
        return None

# MCP Tools
@mcp.tool()
async def hello_world() -> str:
    """Say hello to the world."""
    return "Hello, world! This is the Luvya Travel App MCP server with Supabase integration!"

@mcp.tool()
async def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticate a user with Supabase and return user information."""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            return {
                "success": True,
                "user_id": auth_response.user.id,
                "email": auth_response.user.email,
                "message": "Authentication successful"
            }
        else:
            return {
                "success": False,
                "message": "Authentication failed"
            }
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        return {
            "success": False,
            "message": f"Authentication error: {str(e)}"
        }

@mcp.tool()
async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile information from Supabase."""
    try:
        response = supabase.auth.admin.get_user_by_id(user_id)
        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "email_confirmed_at": response.user.email_confirmed_at
            }
        else:
            return {"error": "User not found"}
    except Exception as e:
        logging.error(f"Error getting user profile: {e}")
        return {"error": f"Failed to get user profile: {str(e)}"}

@mcp.tool()
async def get_trips(user_id: str) -> List[Dict[str, Any]]:
    """Get all trips for a user from Supabase."""
    try:
        response = supabase.table("trips").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error getting trips: {e}")
        return []

@mcp.tool()
async def create_trip(title: str, description: str, start_date: str, end_date: str, user_id: str) -> Dict[str, Any]:
    """Create a new trip in Supabase."""
    try:
        trip_data = {
            "title": title,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id
        }
        response = supabase.table("trips").insert(trip_data).execute()
        return response.data[0] if response.data else {"error": "Failed to create trip"}
    except Exception as e:
        logging.error(f"Error creating trip: {e}")
        return {"error": f"Failed to create trip: {str(e)}"}

@mcp.tool()
async def get_trip_events(trip_id: str) -> List[Dict[str, Any]]:
    """Get all events for a specific trip from Supabase."""
    try:
        response = supabase.table("trip_events").select("*").eq("trip_id", trip_id).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error getting trip events: {e}")
        return []

@mcp.tool()
async def create_trip_event(trip_id: str, title: str, description: str, date: str, location: str) -> Dict[str, Any]:
    """Create a new event for a trip in Supabase."""
    try:
        event_data = {
            "trip_id": trip_id,
            "title": title,
            "description": description,
            "date": date,
            "location": location
        }
        response = supabase.table("trip_events").insert(event_data).execute()
        return response.data[0] if response.data else {"error": "Failed to create trip event"}
    except Exception as e:
        logging.error(f"Error creating trip event: {e}")
        return {"error": f"Failed to create trip event: {str(e)}"}

@mcp.tool()
async def get_notifications(user_id: str) -> List[Dict[str, Any]]:
    """Get all notifications for a user from Supabase."""
    try:
        response = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error getting notifications: {e}")
        return []

@mcp.tool()
async def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    """Mark a notification as read in Supabase."""
    try:
        response = supabase.table("notifications").update({"read": True}).eq("id", notification_id).execute()
        return response.data[0] if response.data else {"error": "Failed to mark notification as read"}
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        return {"error": f"Failed to mark notification as read: {str(e)}"}

# MCP Resources (Widgets)
@mcp.resource("widget://trips")
async def trips_widget() -> str:
    """Trips management widget."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Luvya Trips</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .trip { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .trip h3 { margin: 0 0 10px 0; color: #333; }
            .trip p { margin: 5px 0; color: #666; }
        </style>
    </head>
    <body>
        <h1>✈️ My Trips</h1>
        <div id="trips-container">
            <p>Loading trips...</p>
        </div>
        <script>
            // Widget functionality would be implemented here
            document.getElementById('trips-container').innerHTML = '<p>Trip management widget loaded successfully!</p>';
        </script>
    </body>
    </html>
    """

@mcp.resource("widget://events")
async def events_widget() -> str:
    """Trip events management widget."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Luvya Trip Events</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .event { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .event h3 { margin: 0 0 10px 0; color: #333; }
            .event p { margin: 5px 0; color: #666; }
        </style>
    </head>
    <body>
        <h1>📅 Trip Events</h1>
        <div id="events-container">
            <p>Loading events...</p>
        </div>
        <script>
            // Widget functionality would be implemented here
            document.getElementById('events-container').innerHTML = '<p>Events management widget loaded successfully!</p>';
        </script>
    </body>
    </html>
    """

@mcp.resource("widget://notifications")
async def notifications_widget() -> str:
    """Notifications management widget."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Luvya Notifications</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .notification { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .notification h3 { margin: 0 0 10px 0; color: #333; }
            .notification p { margin: 5px 0; color: #666; }
            .unread { background-color: #f0f8ff; }
        </style>
    </head>
    <body>
        <h1>🔔 Notifications</h1>
        <div id="notifications-container">
            <p>Loading notifications...</p>
        </div>
        <script>
            // Widget functionality would be implemented here
            document.getElementById('notifications-container').innerHTML = '<p>Notifications widget loaded successfully!</p>';
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
