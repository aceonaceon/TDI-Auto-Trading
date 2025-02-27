#!/bin/bash

# Make script executable with: chmod +x docker-run.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${YELLOW}TDI Auto Trading System - Docker Helper${NC}"
    echo ""
    echo "Usage: ./docker-run.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start         Start the trading system in detached mode"
    echo "  start-web     Start the web interface only"
    echo "  start-all     Start both trading system and web interface"
    echo "  stop          Stop the trading system"
    echo "  stop-web      Stop the web interface only"
    echo "  stop-all      Stop both trading system and web interface"
    echo "  restart       Restart the trading system"
    echo "  restart-web   Restart the web interface"
    echo "  restart-all   Restart both trading system and web interface"
    echo "  logs          Show trading system logs (follow mode)"
    echo "  logs-web      Show web interface logs (follow mode)"
    echo "  status        Check if the containers are running"
    echo "  backtest      Run a backtest (requires start and end dates)"
    echo "  rebuild       Rebuild the Docker image and restart"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docker-run.sh start-all"
    echo "  ./docker-run.sh logs-web"
    echo "  ./docker-run.sh backtest 2023-01-01 2023-12-31"
    echo ""
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        echo -e "${RED}Error: .env file not found!${NC}"
        echo -e "Please create a .env file from the template:"
        echo -e "cp .env.template .env"
        exit 1
    fi
}

# Check for docker-compose or docker compose
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        echo -e "${RED}Error: Neither docker-compose nor docker compose command found!${NC}"
        echo -e "Please install Docker Compose or make sure it's in your PATH."
        echo -e "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    echo -e "${GREEN}Using ${DOCKER_COMPOSE} command${NC}"
}

# Start the trading system
start_system() {
    check_env_file
    check_docker_compose
    echo -e "${GREEN}Starting TDI Auto Trading System...${NC}"
    $DOCKER_COMPOSE up -d tdi-trading
    echo -e "${GREEN}System started in background. Use './docker-run.sh logs' to view logs.${NC}"
}

# Start the web interface
start_web() {
    check_env_file
    check_docker_compose
    echo -e "${GREEN}Starting TDI Web Interface...${NC}"
    $DOCKER_COMPOSE up -d tdi-web
    echo -e "${GREEN}Web interface started in background. Use './docker-run.sh logs-web' to view logs.${NC}"
    echo -e "${GREEN}Access the web interface at http://localhost:5001${NC}"
}

# Start both trading system and web interface
start_all() {
    check_env_file
    check_docker_compose
    echo -e "${GREEN}Starting TDI Auto Trading System and Web Interface...${NC}"
    $DOCKER_COMPOSE up -d
    echo -e "${GREEN}System started in background. Use './docker-run.sh logs' or './docker-run.sh logs-web' to view logs.${NC}"
    echo -e "${GREEN}Access the web interface at http://localhost:5001${NC}"
}

# Stop the trading system
stop_system() {
    check_docker_compose
    echo -e "${YELLOW}Stopping TDI Auto Trading System...${NC}"
    $DOCKER_COMPOSE stop tdi-trading
    echo -e "${GREEN}Trading system stopped.${NC}"
}

# Stop the web interface
stop_web() {
    check_docker_compose
    echo -e "${YELLOW}Stopping TDI Web Interface...${NC}"
    $DOCKER_COMPOSE stop tdi-web
    echo -e "${GREEN}Web interface stopped.${NC}"
}

# Stop both trading system and web interface
stop_all() {
    check_docker_compose
    echo -e "${YELLOW}Stopping TDI Auto Trading System and Web Interface...${NC}"
    $DOCKER_COMPOSE down
    echo -e "${GREEN}All systems stopped.${NC}"
}

# Show trading system logs
show_logs() {
    echo -e "${GREEN}Showing trading system logs (Ctrl+C to exit)...${NC}"
    docker logs -f tdi-auto-trading
}

# Show web interface logs
show_web_logs() {
    echo -e "${GREEN}Showing web interface logs (Ctrl+C to exit)...${NC}"
    docker logs -f tdi-web-interface
}

# Check status
check_status() {
    echo -e "${YELLOW}Checking system status...${NC}"
    
    if [ "$(docker ps -q -f name=tdi-auto-trading)" ]; then
        echo -e "${GREEN}TDI Auto Trading System is running.${NC}"
    else
        echo -e "${RED}TDI Auto Trading System is not running.${NC}"
    fi
    
    if [ "$(docker ps -q -f name=tdi-web-interface)" ]; then
        echo -e "${GREEN}TDI Web Interface is running.${NC}"
        echo -e "${GREEN}Access the web interface at http://localhost:5001${NC}"
    else
        echo -e "${RED}TDI Web Interface is not running.${NC}"
    fi
}

# Run backtest
run_backtest() {
    check_env_file
    check_docker_compose
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo -e "${RED}Error: Start and end dates are required for backtest.${NC}"
        echo -e "Usage: ./docker-run.sh backtest YYYY-MM-DD YYYY-MM-DD"
        exit 1
    fi
    
    echo -e "${GREEN}Running backtest from $1 to $2...${NC}"
    $DOCKER_COMPOSE run --rm tdi-trading python main.py --backtest --start-date $1 --end-date $2
    echo -e "${GREEN}Backtest completed.${NC}"
}

# Rebuild the Docker image
rebuild_system() {
    check_env_file
    check_docker_compose
    echo -e "${YELLOW}Rebuilding TDI Auto Trading System...${NC}"
    $DOCKER_COMPOSE down
    $DOCKER_COMPOSE build --no-cache
    $DOCKER_COMPOSE up -d
    echo -e "${GREEN}System rebuilt and started.${NC}"
}

# Main script logic
case "$1" in
    start)
        start_system
        ;;
    start-web)
        start_web
        ;;
    start-all)
        start_all
        ;;
    stop)
        stop_system
        ;;
    stop-web)
        stop_web
        ;;
    stop-all)
        stop_all
        ;;
    restart)
        stop_system
        start_system
        ;;
    restart-web)
        stop_web
        start_web
        ;;
    restart-all)
        stop_all
        start_all
        ;;
    logs)
        show_logs
        ;;
    logs-web)
        show_web_logs
        ;;
    status)
        check_status
        ;;
    backtest)
        run_backtest $2 $3
        ;;
    rebuild)
        rebuild_system
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
