#!/bin/bash
docker compose up -d
cd backend
source venv/bin/activate
uvicorn app.main:app --reload