#!/bin/bash
# Script to run FastAPI with Uvicorn

uvicorn main:app --reload --host 0.0.0.0 --port 8080

