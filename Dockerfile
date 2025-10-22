FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port (for HTTP transport)
EXPOSE 8000

# Start the MCP server
CMD ["python", "luvya_server.py"]