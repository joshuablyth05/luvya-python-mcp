#!/usr/bin/env python3
"""
Luvya Travel App MCP Server with FastMCP 2.0 and Supabase Integration

This server uses FastMCP 2.0 (https://github.com/jlowin/fastmcp) which provides:
- Enterprise-grade OAuth authentication for ChatGPT integration
- Automatic OAuth discovery endpoints
- Built-in JWT token verification
- Zero-configuration authentication setup

ChatGPT will automatically discover OAuth capabilities and handle the authentication flow.
"""

from typing import Any, Dict, List, Optional
import logging
import os
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from supabase import create_client, Client
from dotenv import load_dotenv
import jwt

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
# This enables enterprise-grade authentication for ChatGPT integration
jwt_verifier = JWTVerifier(
    public_key=JWT_SECRET,  # Using our JWT secret as the symmetric key
    issuer=base_url,
    audience=f"{base_url}/mcp",
    algorithm="HS256"
)

# Initialize FastMCP with authentication enabled
# FastMCP 2.0 automatically provides OAuth discovery endpoints for ChatGPT
mcp = FastMCP(
    "luvya-travel-app",
    auth=jwt_verifier
)

# OAuth code storage (in production, use a database)
oauth_codes: Dict[str, Dict] = {}

# User sessions (in production, use a database)
user_sessions: Dict[str, Dict] = {}

# Helper functions for OAuth 2.1 implementation
def generate_auth_token(user_id: str) -> str:
    """Generate JWT token for user authentication."""
    payload = {
        "user_id": user_id,
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow(),
        "iss": base_url,
        "aud": f"{base_url}/mcp",
        "client_id": "chatgpt-mcp-client",
        "scope": "user"
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

# OAuth 2.1 Endpoints required by ChatGPT
# These endpoints implement the OAuth 2.1 specification for MCP servers

@mcp.route("/.well-known/oauth-authorization-server", methods=["GET"])
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata endpoint (RFC8414)."""
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "registration_endpoint": f"{base_url}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"]
    }

@mcp.route("/.well-known/jwks.json", methods=["GET"])
async def jwks():
    """JSON Web Key Set endpoint."""
    return {
        "keys": [
            {
                "kty": "oct",
                "kid": "luvya-mcp-key",
                "use": "sig",
                "alg": "HS256"
            }
        ]
    }

@mcp.route("/register", methods=["POST"])
async def oauth_register():
    """Dynamic client registration endpoint (RFC7591)."""
    return {
        "client_id": "chatgpt-mcp-client",
        "client_secret": None,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "client_secret_expires_at": 0,
        "redirect_uris": ["https://chatgpt.com", "https://chat.openai.com"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": "user"
    }

@mcp.route("/authorize", methods=["GET"])
async def oauth_authorize(
    response_type: str = "code",
    client_id: str = None,
    redirect_uri: str = None,
    scope: str = "user",
    state: str = None,
    code_challenge: str = None,
    code_challenge_method: str = "S256"
):
    """OAuth 2.1 authorization endpoint with PKCE support."""
    from fastapi.responses import HTMLResponse
    
    # Validate request parameters
    if response_type != "code":
        return {"error": "invalid_response_type"}
    
    if not client_id or not redirect_uri or not code_challenge:
        return {"error": "missing_required_parameters"}
    
    if code_challenge_method != "S256":
        return {"error": "invalid_code_challenge_method"}
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store OAuth code with PKCE challenge
    oauth_codes[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "scope": scope,
        "state": state,
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
        "user_id": "demo-user"  # In production, this would be set after user login
    }
    
    # HTML authorization page
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Authorize Luvya Travel App</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .auth-container {{
                background: white;
                border-radius: 16px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                max-width: 500px;
                width: 100%;
                text-align: center;
            }}
            .logo {{
                font-size: 48px;
                margin-bottom: 20px;
            }}
            .app-name {{
                font-size: 28px;
                font-weight: 600;
                color: #333;
                margin-bottom: 10px;
            }}
            .app-description {{
                color: #666;
                margin-bottom: 30px;
                line-height: 1.5;
            }}
            .permissions {{
                background: #f8f9fa;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }}
            .permission-item {{
                display: flex;
                align-items: center;
                margin: 10px 0;
                font-size: 16px;
            }}
            .permission-icon {{
                width: 20px;
                height: 20px;
                margin-right: 12px;
                color: #28a745;
            }}
            .buttons {{
                display: flex;
                gap: 15px;
                margin-top: 30px;
            }}
            .btn {{
                flex: 1;
                padding: 14px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .btn-allow {{
                background: #007bff;
                color: white;
            }}
            .btn-allow:hover {{
                background: #0056b3;
                transform: translateY(-1px);
            }}
            .btn-deny {{
                background: #6c757d;
                color: white;
            }}
            .btn-deny:hover {{
                background: #545b62;
                transform: translateY(-1px);
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">🗺️</div>
            <div class="app-name">Luvya Travel App</div>
            <div class="app-description">
                ChatGPT wants to access your Luvya Travel account to help you manage your trips, events, and notifications.
            </div>
            
            <div class="permissions">
                <h3 style="margin-top: 0; color: #333;">Permissions Requested:</h3>
                <div class="permission-item">
                    <span class="permission-icon">📖</span>
                    <span>Read your travel data (trips, events, notifications)</span>
                </div>
                <div class="permission-item">
                    <span class="permission-icon">✏️</span>
                    <span>Create and manage your trips and events</span>
                </div>
                <div class="permission-item">
                    <span class="permission-icon">👤</span>
                    <span>Access your user profile information</span>
                </div>
            </div>
            
            <div class="buttons">
                <button class="btn btn-deny" onclick="denyAccess()">Deny</button>
                <button class="btn btn-allow" onclick="allowAccess()">Allow</button>
            </div>
        </div>
        
        <script>
            function allowAccess() {{
                const redirectUrl = new URL("{redirect_uri}");
                redirectUrl.searchParams.set("code", "{auth_code}");
                redirectUrl.searchParams.set("state", "{state or ''}");
                window.location.href = redirectUrl.toString();
            }}
            
            function denyAccess() {{
                const redirectUrl = new URL("{redirect_uri}");
                redirectUrl.searchParams.set("error", "access_denied");
                redirectUrl.searchParams.set("state", "{state or ''}");
                window.location.href = redirectUrl.toString();
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@mcp.route("/token", methods=["POST"])
async def oauth_token(
    grant_type: str = "authorization_code",
    code: str = None,
    client_id: str = None,
    client_secret: str = None,
    redirect_uri: str = None,
    code_verifier: str = None
):
    """OAuth 2.1 token endpoint with PKCE validation."""
    if grant_type != "authorization_code":
        return {"error": "unsupported_grant_type"}
    
    if not code or not code_verifier:
        return {"error": "missing_required_parameters"}
    
    # Get stored OAuth code
    if code not in oauth_codes:
        return {"error": "invalid_grant"}
    
    stored_code = oauth_codes[code]
    
    # Check expiration
    if stored_code["expires_at"] < datetime.utcnow():
        del oauth_codes[code]
        return {"error": "expired_code"}
    
    # Validate redirect URI
    if stored_code["redirect_uri"] != redirect_uri:
        return {"error": "invalid_redirect_uri"}
    
    # Validate PKCE code verifier
    expected_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    if expected_challenge != stored_code["code_challenge"]:
        return {"error": "invalid_code_verifier"}
    
    # Generate access token
    user_id = stored_code.get("user_id", "demo-user")
    access_token = generate_auth_token(user_id)
    
    # Clean up used code
    del oauth_codes[code]
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": stored_code["scope"]
    }

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
