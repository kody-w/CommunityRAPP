#!/bin/bash
# Card Minter Daemon Manager
# Runs card_minter.py as a continuous background process

cd "$(dirname "$0")/.." || exit 1

SCRIPT_DIR="$(pwd)/scripts"
LOG_DIR="$(pwd)/logs"
PID_FILE="$LOG_DIR/card_minter.pid"

# Create logs directory if needed
mkdir -p "$LOG_DIR"

# Function to start the service
start() {
    if [ -f "$PID_FILE" ]; then
        existing_pid=$(cat "$PID_FILE")
        if kill -0 "$existing_pid" 2>/dev/null; then
            echo "❌ Card minter is already running (PID: $existing_pid)"
            return 1
        fi
    fi
    
    echo "🚀 Starting card minter..."
    nohup python3 "$SCRIPT_DIR/card_minter.py" > "$LOG_DIR/card_minter.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ Card minter started (PID: $(cat $PID_FILE))"
    echo "📝 Logs: $LOG_DIR/card_minter.log"
}

# Function to stop the service
stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Card minter is not running"
        return 1
    fi
    
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "🛑 Stopping card minter (PID: $pid)..."
        kill "$pid"
        sleep 1
        if ! kill -0 "$pid" 2>/dev/null; then
            rm "$PID_FILE"
            echo "✅ Card minter stopped"
        else
            echo "⚠️  Process did not stop gracefully, forcing..."
            kill -9 "$pid"
            rm "$PID_FILE"
            echo "✅ Card minter force stopped"
        fi
    else
        echo "❌ Card minter process not found"
        rm "$PID_FILE"
    fi
}

# Function to check status
status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Card minter is not running"
        return 1
    fi
    
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "✅ Card minter is running (PID: $pid)"
        echo "📊 Recent logs:"
        tail -5 "$LOG_DIR/card_minter.log"
        return 0
    else
        echo "❌ Card minter is not running"
        rm "$PID_FILE"
        return 1
    fi
}

# Main script
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    test)
        echo "🧪 Running single test cycle..."
        python3 "$SCRIPT_DIR/card_minter.py" --once
        ;;
    logs)
        if [ -f "$LOG_DIR/card_minter.log" ]; then
            tail -f "$LOG_DIR/card_minter.log"
        else
            echo "❌ No log file found yet"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start card minter daemon"
        echo "  stop    - Stop card minter daemon"
        echo "  restart - Restart card minter daemon"
        echo "  status  - Check daemon status"
        echo "  test    - Run a single test cycle"
        echo "  logs    - Tail the log file"
        exit 1
        ;;
esac

exit 0
