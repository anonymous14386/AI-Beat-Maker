#!/bin/bash

# This script manages the AI Sample Sequencer application.
# It can start, stop, and restart the required services.

# --- Configuration ---
PYTHON_SERVER_COMMAND="python3 -m http.server"
OLLAMA_SERVICE_NAME="ollama"
WEB_APP_URL="http://localhost:8000"

# --- Functions ---

# Function to start the application
start_app() {
    echo "🚀 Starting AI Sample Sequencer..."

    # 1. Start Ollama Service
    echo "Checking Ollama service..."
    if ! systemctl is-active --quiet $OLLAMA_SERVICE_NAME; then
        echo "🔥 Starting Ollama system service..."
        sudo systemctl start $OLLAMA_SERVICE_NAME
        if [ $? -ne 0 ]; then
            echo "❌ Error: Failed to start Ollama service. Please check your installation."
            exit 1
        fi
        sleep 2 # Give it a moment to initialize
        echo "✅ Ollama service started."
    else
        echo "✅ Ollama service is already running."
    fi

    # 2. Start Python Web Server
    echo "Checking for existing web server..."
    if pgrep -f "$PYTHON_SERVER_COMMAND" > /dev/null; then
        echo "✅ Python web server is already running."
    else
        echo "🔥 Starting Python web server in the background..."
        nohup $PYTHON_SERVER_COMMAND > webserver.log 2>&1 &
        sleep 1
        echo "✅ Web server started."
    fi

    echo -e "\n🎉 Setup complete! 🎉"
    echo "You can now access the app at:"
    echo -e "\n\t\033[1;32m$WEB_APP_URL\033[0m\n"
}

# Function to stop the application
stop_app() {
    echo "🛑 Stopping AI Sample Sequencer..."

    # 1. Stop Ollama Service
    echo "Stopping Ollama system service..."
    sudo systemctl stop $OLLAMA_SERVICE_NAME
    echo "✅ Ollama service stopped."

    # 2. Stop Python Web Server
    echo "Stopping Python web server..."
    pkill -f "$PYTHON_SERVER_COMMAND"
    echo "✅ Web server stopped."

    echo -e "\nAll services have been stopped."
}


# --- Main Logic ---
# Check for command-line argument (start, stop, restart)
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        sleep 1
        start_app
        ;;
    *)
        echo "Usage: ./manage_app.sh {start|stop|restart}"
        exit 1
        ;;
esac
