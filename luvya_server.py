from typing import Any, Dict, List, Optional
import httpx
import logging
import jwt
import secrets
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

# Initialize FastAPI app for HTTP endpoints
app = FastAPI(title="Luvya MCP Server", version="1.0.0")

# Initialize FastMCP server
mcp = FastMCP("luvya")

# Configure logging to stderr (required for MCP)
logging.basicConfig(level=logging.INFO, stream=os.sys.stderr)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dnqvfftyzetqwryfjptk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRucXZmZnR5emV0cXdyeWZqcHRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MDk2MDcsImV4cCI6MjA3NTk4NTYwN30.SSqt0dSLXbeJ8gUz_Y8Zn9SsamQ8twe7kI2Ezz35x6g")
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key-here")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Current user context (will be set during authentication)
current_user_id: Optional[str] = None

# Helper functions for authentication
def generate_auth_token(user_id: str) -> str:
    """Generate JWT token for user authentication."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_auth_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def set_current_user(user_id: str):
    """Set the current user context."""
    global current_user_id
    current_user_id = user_id

def get_current_user() -> Optional[str]:
    """Get the current user ID."""
    return current_user_id

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

# FastAPI HTTP Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Luvya MCP Server", "status": "running"}

@app.get("/mcp")
async def mcp_discovery():
    """MCP discovery endpoint."""
    return {
        "name": "luvya",
        "version": "1.0.0",
        "protocol": "mcp",
        "capabilities": {
            "tools": True,
            "resources": True
        },
        "oauth": {
            "authorization_endpoint": "/oauth/authorize",
            "token_endpoint": "/oauth/token",
            "scopes": ["read", "write"]
        }
    }

# OAuth 2.1 Endpoints for ChatGPT MCP Connector
@app.get("/oauth/authorize")
async def oauth_authorize(
    response_type: str = "code",
    client_id: str = "chatgpt-mcp",
    redirect_uri: str = None,
    scope: str = "read write",
    state: str = None
):
    """OAuth 2.1 authorization endpoint."""
    # For MCP, we'll return a simple authorization page
    return {
        "authorization_url": f"/oauth/authorize?response_type={response_type}&client_id={client_id}&scope={scope}",
        "client_id": client_id,
        "scopes": scope.split(" "),
        "state": state
    }

@app.post("/oauth/token")
async def oauth_token(
    grant_type: str = "authorization_code",
    code: str = None,
    client_id: str = "chatgpt-mcp",
    client_secret: str = None,
    redirect_uri: str = None
):
    """OAuth 2.1 token endpoint."""
    # Generate a simple access token for MCP
    access_token = generate_auth_token("mcp-user")
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "read write"
    }

@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """OAuth 2.1 metadata endpoint."""
    base_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "https://luvya-python-mcp-production-abc123.up.railway.app")
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "scopes_supported": ["read", "write"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"]
    }

# MCP Tools
@mcp.tool()
async def hello_world() -> str:
    """Say hello from the Luvya MCP server.
    
    This is a simple test tool to verify the MCP server is working correctly.
    """
    user_id = get_current_user()
    if user_id:
        return f"Hello from Luvya! Welcome back, user {user_id}! 🚀"
    else:
        return "Hello from Luvya! Please authenticate to access your travel data. 🚀"

@mcp.tool()
async def authenticate_user(email: str, password: str) -> str:
    """Authenticate user with email and password.
    
    Args:
        email: User's email address
        password: User's password
    """
    try:
        # Use Supabase Auth to authenticate user
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            user_id = auth_response.user.id
            set_current_user(user_id)
            token = generate_auth_token(user_id)
            
            return f"Authentication successful! Welcome, {email}. User ID: {user_id}"
        else:
            return "Authentication failed. Please check your email and password."
            
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        return "Authentication failed. Please try again."

@mcp.tool()
async def get_user_profile() -> str:
    """Get current user's profile information."""
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to view your profile."
    
    try:
        # Get user data from Supabase
        response = supabase.auth.get_user()
        
        if response.user:
            user = response.user
            return f"""
User Profile:
Email: {user.email}
User ID: {user.id}
Created: {user.created_at}
Last Sign In: {user.last_sign_in_at}
"""
        else:
            return "Unable to retrieve user profile."
            
    except Exception as e:
        logging.error(f"Error getting user profile: {e}")
        return "Error retrieving user profile."

@mcp.tool()
async def get_trips() -> str:
    """Get all trips for the current user."""
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to view your trips."
    
    trips_data = await make_supabase_request("trips", "select", filters={"user_id": user_id})
    
    if not trips_data:
        return "No trips found for your account."
    
    formatted_trips = [format_trip(trip) for trip in trips_data]
    return "\n---\n".join(formatted_trips)

@mcp.tool()
async def create_trip(title: str, description: str, start_date: str, end_date: str) -> str:
    """Create a new trip for the current user.
    
    Args:
        title: The title of the trip
        description: Description of the trip
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to create trips."
    
    trip_data = {
        "title": title,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id
    }
    
    result = await make_supabase_request("trips", "insert", data=trip_data)
    
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
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to view trip events."
    
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
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to create trip events."
    
    event_data = {
        "trip_id": trip_id,
        "title": title,
        "description": description,
        "event_date": event_date,
        "location": location
    }
    
    result = await make_supabase_request("trip_events", "insert", data=event_data)
    
    if result:
        return f"Successfully created event: {title}"
    else:
        return f"Failed to create event: {title}"

@mcp.tool()
async def get_notifications() -> str:
    """Get all notifications for the current user."""
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to view your notifications."
    
    try:
        response = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        notifications_data = response.data
        
        if not notifications_data:
            return f"No notifications found for your account."
        
        formatted_notifications = [format_notification(notification) for notification in notifications_data]
        return "\n---\n".join(formatted_notifications)
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        return "Error fetching notifications."

@mcp.tool()
async def mark_notification_read(notification_id: str) -> str:
    """Mark a notification as read.
    
    Args:
        notification_id: The ID of the notification to mark as read
    """
    user_id = get_current_user()
    
    if not user_id:
        return "Please authenticate first to manage notifications."
    
    try:
        response = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
        
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
        .auth-section { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        .btn { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #0056b3; }
        .loading { text-align: center; color: #6c757d; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🗺️ My Trips</h1>
        
        <div class="auth-section">
            <h3>Authentication Required</h3>
            <p>Please authenticate to view your trips:</p>
            <input type="email" id="email" placeholder="Email" style="padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <input type="password" id="password" placeholder="Password" style="padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <button class="btn" onclick="authenticate()">Login</button>
        </div>
        
        <div id="trips-container">
            <div class="loading">Please authenticate to view your trips...</div>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        async function authenticate() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                alert('Please enter both email and password');
                return;
            }
            
            try {
                // In a real implementation, you would call your authentication endpoint
                // For now, we'll simulate authentication
                currentUser = { email: email, id: 'user_' + Date.now() };
                
                document.querySelector('.auth-section').innerHTML = 
                    '<div class="success">✅ Authenticated as: ' + email + '</div>';
                
                await loadTrips();
            } catch (error) {
                alert('Authentication failed: ' + error.message);
            }
        }
        
        async function loadTrips() {
            if (!currentUser) {
                document.getElementById('trips-container').innerHTML = 
                    '<div class="error">Please authenticate first</div>';
                return;
            }
            
            try {
                // Simulate loading trips
                document.getElementById('trips-container').innerHTML = 
                    '<div class="trip-card"><div class="trip-title">Sample Trip</div><div class="trip-dates">2024-01-01 to 2024-01-07</div><div class="trip-description">A wonderful vacation trip!</div></div>';
            } catch (error) {
                document.getElementById('trips-container').innerHTML = 
                    '<div class="error">Error loading trips: ' + error.message + '</div>';
            }
        }
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
            <div class="loading">Please authenticate to view trip events...</div>
        </div>
    </div>
    
    <script>
        // Events widget will show events after authentication
        document.getElementById('events-container').innerHTML = 
            '<p>Select a trip to view its events, or create new events for your trips!</p>';
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
            <div class="loading">Please authenticate to view your notifications...</div>
        </div>
    </div>
    
    <script>
        // Notifications widget will show notifications after authentication
        document.getElementById('notifications-container').innerHTML = 
            '<p>Your notifications will appear here after authentication. Stay updated with your trip activities!</p>';
    </script>
</body>
</html>
"""

def main():
    """Run the server - either as HTTP server or MCP server based on environment."""
    import sys
    
    if "--mcp" in sys.argv:
        # Run as MCP server (STDIO transport)
        mcp.run(transport='stdio')
    else:
        # Run as HTTP server
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()