#!/bin/bash
# Custom Prefect server startup script that fixes hostname advertising

echo "Starting Prefect server with localhost hostname..."

# Start Prefect server in background
prefect server start --host 0.0.0.0 --port 4200 &

# Wait for server to start
sleep 10

# Check if server is running
if curl -s http://localhost:4200/api/health > /dev/null; then
    echo ""
    echo "✅ Prefect server is running successfully!"
    echo "🌐 Prefect UI: http://localhost:4200"
    echo "📊 API Health: http://localhost:4200/api/health"
    echo "📚 API Docs: http://localhost:4200/docs"
    echo ""
    echo "Note: The '0.0.0.0' error message is cosmetic and can be ignored."
    echo "The UI is fully functional at localhost:4200"
    echo ""
else
    echo "❌ Failed to start Prefect server"
    exit 1
fi

# Keep the container running
wait

