# Luvya MCP Server

A Python-based Model Context Protocol (MCP) server for the Luvya travel app, integrated with Supabase.

## Features

- **MCP Tools**: Get trips, create trips, manage events, handle notifications
- **Interactive Widgets**: HTML widgets for trips, events, and notifications
- **Supabase Integration**: Direct connection to your travel app database
- **OAuth Ready**: Authentication support for ChatGPT integration

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Run the server**:
   ```bash
   python luvya_server.py
   ```

## MCP Tools Available

- `hello_world()` - Test connection
- `get_trips()` - List all trips
- `create_trip(title, description, start_date, end_date, user_id)` - Create new trip
- `get_trip_events(trip_id)` - Get events for a trip
- `create_trip_event(trip_id, title, description, event_date, location)` - Create trip event
- `get_notifications(user_id)` - Get user notifications
- `mark_notification_read(notification_id)` - Mark notification as read

## MCP Resources (Widgets)

- `trips-widget` - Interactive trips management
- `events-widget` - Trip events management
- `notifications-widget` - Notifications management

## Connect to ChatGPT

1. **Get your MCP server URL**: `http://localhost:3000/mcp` (when deployed)
2. **In ChatGPT**: Enable developer mode → Create connection → Enter MCP URL
3. **Test**: "Use my app to say hello!"

## Deployment

### Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway deploy
```

### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

### Render
1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python luvya_server.py`
4. Add environment variables

## Environment Variables

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `JWT_SECRET` - Secret for JWT signing (optional)

## Development

The server uses FastMCP which automatically generates tool definitions from Python type hints and docstrings. This makes it easy to add new tools and maintain the codebase.

## Troubleshooting

- **Server not connecting**: Check Supabase credentials in `.env`
- **Tools not working**: Verify database tables exist in Supabase
- **Widgets not loading**: Check browser console for errors

## License

MIT License
