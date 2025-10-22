#!/usr/bin/env python3
"""
Luvya Travel App MCP Server with HTTP endpoints for Railway deployment
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Resource,
    TextContent,
    Tool,
)
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dnqvfftyzetqwryfjptk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRucXZmZnR5emV0cXdyeWZqcHRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MDk2MDcsImV4cCI6MjA3NTk4NTYwN30.SSqt0dSLXbeJ8gUz_Y8Zn9SsamQ8twe7kI2Ezz35x6g")

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

# Initialize FastAPI app for HTTP endpoints
app = FastAPI(title="Luvya MCP Server", version="1.0.0")

# Initialize MCP server
mcp_server = Server("luvya-travel-app")

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
        logger.error(f"Supabase request failed: {e}")
        return None

# HTTP Endpoints for Railway deployment
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Luvya MCP Server", "status": "running"}

@app.get("/mcp")
async def mcp_discovery():
    """MCP discovery endpoint."""
    return {
        "name": "luvya-travel-app",
        "version": "1.0.0",
        "protocol": "mcp",
        "capabilities": {
            "tools": True,
            "resources": True
        }
    }

# MCP Tools
@mcp_server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="hello_world",
                description="Say hello to the world",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="authenticate_user",
                description="Authenticate a user with Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "User's email address"},
                        "password": {"type": "string", "description": "User's password"}
                    },
                    "required": ["email", "password"]
                }
            ),
            Tool(
                name="get_user_profile",
                description="Get user profile information from Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="get_trips",
                description="Get all trips for a user from Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="create_trip",
                description="Create a new trip in Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Trip title"},
                        "description": {"type": "string", "description": "Trip description"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                        "user_id": {"type": "string", "description": "User ID"}
                    },
                    "required": ["title", "description", "start_date", "end_date", "user_id"]
                }
            ),
            Tool(
                name="get_trip_events",
                description="Get all events for a specific trip from Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {"type": "string", "description": "Trip ID"}
                    },
                    "required": ["trip_id"]
                }
            ),
            Tool(
                name="create_trip_event",
                description="Create a new event for a trip in Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {"type": "string", "description": "Trip ID"},
                        "title": {"type": "string", "description": "Event title"},
                        "description": {"type": "string", "description": "Event description"},
                        "date": {"type": "string", "description": "Event date (YYYY-MM-DD)"},
                        "location": {"type": "string", "description": "Event location"}
                    },
                    "required": ["trip_id", "title", "description", "date", "location"]
                }
            ),
            Tool(
                name="get_notifications",
                description="Get all notifications for a user from Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="mark_notification_read",
                description="Mark a notification as read in Supabase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "notification_id": {"type": "string", "description": "Notification ID"}
                    },
                    "required": ["notification_id"]
                }
            )
        ]
    )

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "hello_world":
            return CallToolResult(
                content=[TextContent(type="text", text="Hello, world! This is the Luvya Travel App MCP server with Supabase integration!")]
            )
        
        elif name == "authenticate_user":
            email = arguments.get("email")
            password = arguments.get("password")
            
            try:
                auth_response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if auth_response.user:
                    result = {
                        "success": True,
                        "user_id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "message": "Authentication successful"
                    }
                else:
                    result = {
                        "success": False,
                        "message": "Authentication failed"
                    }
            except Exception as e:
                result = {
                    "success": False,
                    "message": f"Authentication error: {str(e)}"
                }
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "get_user_profile":
            user_id = arguments.get("user_id")
            
            try:
                response = supabase.auth.admin.get_user_by_id(user_id)
                if response.user:
                    result = {
                        "user_id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                        "email_confirmed_at": response.user.email_confirmed_at
                    }
                else:
                    result = {"error": "User not found"}
            except Exception as e:
                result = {"error": f"Failed to get user profile: {str(e)}"}
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "get_trips":
            user_id = arguments.get("user_id")
            
            try:
                response = supabase.table("trips").select("*").eq("user_id", user_id).execute()
                result = response.data if response.data else []
            except Exception as e:
                result = []
                logger.error(f"Error getting trips: {e}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "create_trip":
            title = arguments.get("title")
            description = arguments.get("description")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            user_id = arguments.get("user_id")
            
            try:
                trip_data = {
                    "title": title,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "user_id": user_id
                }
                response = supabase.table("trips").insert(trip_data).execute()
                result = response.data[0] if response.data else {"error": "Failed to create trip"}
            except Exception as e:
                result = {"error": f"Failed to create trip: {str(e)}"}
                logger.error(f"Error creating trip: {e}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "get_trip_events":
            trip_id = arguments.get("trip_id")
            
            try:
                response = supabase.table("trip_events").select("*").eq("trip_id", trip_id).execute()
                result = response.data if response.data else []
            except Exception as e:
                result = []
                logger.error(f"Error getting trip events: {e}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "create_trip_event":
            trip_id = arguments.get("trip_id")
            title = arguments.get("title")
            description = arguments.get("description")
            date = arguments.get("date")
            location = arguments.get("location")
            
            try:
                event_data = {
                    "trip_id": trip_id,
                    "title": title,
                    "description": description,
                    "date": date,
                    "location": location
                }
                response = supabase.table("trip_events").insert(event_data).execute()
                result = response.data[0] if response.data else {"error": "Failed to create trip event"}
            except Exception as e:
                result = {"error": f"Failed to create trip event: {str(e)}"}
                logger.error(f"Error creating trip event: {e}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "get_notifications":
            user_id = arguments.get("user_id")
            
            try:
                response = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
                result = response.data if response.data else []
            except Exception as e:
                result = []
                logger.error(f"Error getting notifications: {e}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        elif name == "mark_notification_read":
            notification_id = arguments.get("notification_id")
            
            try:
                response = supabase.table("notifications").update({"read": True}).eq("id", notification_id).execute()
                result = response.data[0] if response.data else {"error": "Failed to mark notification as read"}
            except Exception as e:
                result = {"error": f"Failed to mark notification as read: {str(e)}"}
                logger.error(f"Error marking notification as read: {e}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

# MCP Resources (Widgets)
@mcp_server.list_resources()
async def handle_list_resources() -> ListResourcesResult:
    """List available resources."""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="widget://trips",
                name="Trips Widget",
                description="Interactive trips management widget",
                mimeType="text/html"
            ),
            Resource(
                uri="widget://events",
                name="Events Widget", 
                description="Interactive trip events management widget",
                mimeType="text/html"
            ),
            Resource(
                uri="widget://notifications",
                name="Notifications Widget",
                description="Interactive notifications management widget", 
                mimeType="text/html"
            )
        ]
    )

@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource reads."""
    if uri == "widget://trips":
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
                <p>Trip management widget loaded successfully!</p>
            </div>
        </body>
        </html>
        """
    
    elif uri == "widget://events":
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
                <p>Events management widget loaded successfully!</p>
            </div>
        </body>
        </html>
        """
    
    elif uri == "widget://notifications":
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
                <p>Notifications widget loaded successfully!</p>
            </div>
        </body>
        </html>
        """
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def run_mcp_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="luvya-travel-app",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

def main():
    """Main entry point - run HTTP server for Railway deployment."""
    import sys
    
    logger.info("Starting Luvya MCP Server...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Environment variables: PORT={os.getenv('PORT')}, SUPABASE_URL={os.getenv('SUPABASE_URL', 'not set')}")
    
    if "--mcp" in sys.argv:
        # Run as MCP server (STDIO transport)
        logger.info("Starting in MCP mode (STDIO)")
        asyncio.run(run_mcp_server())
    else:
        # Run as HTTP server for Railway deployment
        port = int(os.getenv("PORT", 8000))
        logger.info(f"Starting HTTP server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()