# 🔐 Luvya MCP Server with OAuth Authentication

## ✅ **OAuth is Now Ready!**

Your MCP server now has **full OAuth authentication** integrated with Supabase Auth. When users connect from ChatGPT, they will need to authenticate to access their personal travel data.

## 🔑 **How Authentication Works**

### **1. User Authentication Flow**
1. **User connects to ChatGPT** with your MCP server
2. **First tool call**: User must authenticate with `authenticate_user(email, password)`
3. **Server validates** credentials with Supabase Auth
4. **User session** is established with JWT token
5. **All subsequent calls** are tied to the authenticated user

### **2. User-Specific Data**
- **Trips**: Only shows trips belonging to the authenticated user
- **Events**: Only shows events for the user's trips
- **Notifications**: Only shows notifications for the authenticated user
- **Profile**: Shows the authenticated user's profile information

## 🛠️ **Updated MCP Tools**

### **Authentication Tools**
- `authenticate_user(email, password)` - **REQUIRED FIRST** - Authenticate user
- `get_user_profile()` - Get current user's profile

### **User-Specific Data Tools**
- `get_trips()` - Get trips for authenticated user only
- `create_trip(title, description, start_date, end_date)` - Create trip for authenticated user
- `get_trip_events(trip_id)` - Get events for user's trips
- `create_trip_event(trip_id, title, description, event_date, location)` - Create event for user's trip
- `get_notifications()` - Get notifications for authenticated user
- `mark_notification_read(notification_id)` - Mark user's notification as read

## 🎯 **ChatGPT Usage Flow**

### **Step 1: Connect to MCP Server**
- Connect ChatGPT to your MCP server URL
- First message: "Use my app to say hello!" (will show authentication required)

### **Step 2: Authenticate**
- User must authenticate: "Authenticate me with email: your-email@example.com and password: yourpassword"
- Server validates with Supabase Auth
- User session is established

### **Step 3: Use Authenticated Features**
- "Show me my trips" - Shows user's personal trips
- "Create a trip to Paris" - Creates trip for authenticated user
- "Show me my notifications" - Shows user's personal notifications

## 🔒 **Security Features**

- ✅ **JWT Token Authentication** - Secure user sessions
- ✅ **Supabase Auth Integration** - Enterprise-grade authentication
- ✅ **User Data Isolation** - Each user only sees their own data
- ✅ **Session Management** - Automatic user context handling
- ✅ **Password Security** - Handled by Supabase Auth

## 📱 **Enhanced Widgets**

All widgets now include:
- **Authentication UI** - Login forms in widgets
- **User-Specific Content** - Shows data only for authenticated user
- **Session Management** - Maintains user context across widget interactions

## 🚀 **Deployment with OAuth**

### **Environment Variables Required**
```
SUPABASE_URL=https://dnqvfftyzetqwryfjptk.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
JWT_SECRET=your_secure_jwt_secret_here
```

### **Supabase Setup Required**
1. **Enable Supabase Auth** in your Supabase project
2. **Create user accounts** in Supabase Auth
3. **Set up email/password authentication**

## 🧪 **Testing Authentication**

### **Test Commands in ChatGPT**
1. **"Use my app to say hello!"** - Shows authentication required
2. **"Authenticate me with email: test@example.com and password: password123"** - Authenticates user
3. **"Show me my profile"** - Shows authenticated user's profile
4. **"Show me my trips"** - Shows user's personal trips
5. **"Create a trip to Tokyo"** - Creates trip for authenticated user

## 🔧 **User Management**

### **Creating Test Users**
In Supabase Dashboard:
1. Go to **Authentication** → **Users**
2. Click **"Add user"**
3. Enter email and password
4. User can now authenticate with MCP server

### **User Data Structure**
Each user will have:
- **Personal trips** (user_id matches authenticated user)
- **Personal events** (linked to user's trips)
- **Personal notifications** (user_id matches authenticated user)

## 🎉 **Ready for Production!**

Your MCP server now provides:
- ✅ **Secure authentication** with Supabase Auth
- ✅ **User-specific data access** 
- ✅ **JWT session management**
- ✅ **Enhanced security** for production use
- ✅ **Personalized experience** for each user

**When users connect from ChatGPT, they'll need to authenticate first, then all their data will be personalized to their account!** 🚀
