#!/bin/bash
# Open all project-related URLs in Google Chrome (macOS)

# Check if the main API container is running
if ! docker ps --format '{{.Names}}' | grep -q "^movie_bible_api$"; then
    echo "⚠️  System appears to be DOWN."
    echo "🚀 Starting Docker Services..."
    docker compose up -d
    
    echo "📋 Streaming logs..."
    echo "👉 Press Ctrl+C when satisfied, then RUN THIS SCRIPT AGAIN to open tabs."
    
    # We use 'logs -f' to just stream. User hits Ctrl+C to stop.
    docker compose logs -f
    exit 0
fi

echo "✅ System is UP. Opening Project Workspace..."

# GitHub Resources
open -a "Google Chrome" "https://github.com/users/SiderealMollusk/projects/9/views/2" # Project Board
sleep 0.5
open -a "Google Chrome" "https://github.com/SiderealMollusk/rag-chatbot"              # GitHub Repo

# Backend Resources
open -a "Google Chrome" "http://localhost:8080"       # Dozzle (Logs)
sleep 0.5
open -a "Google Chrome" "http://localhost:5555"       # Flower (Celery Dashboard)
sleep 0.5
open -a "Google Chrome" "http://localhost:8000/docs"  # Backend API (Swagger)
sleep 0.5

# Frontend Resources
open -a "Google Chrome" "http://localhost:3000"       # Frontend App
sleep 0.5
echo "Done."
