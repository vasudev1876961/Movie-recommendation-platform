# backend/data/movies.py
import os
import json
import logging

logger = logging.getLogger("uvicorn.error")

# Dynamically load the absolute list of 100 movies from the JSON database
base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "movies.json")

movies = []
try:
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            movies = json.load(f)
        logger.info(f"[Database] Successfully loaded {len(movies)} movies from JSON file.")
    else:
        logger.error(f"[Database] movies.json not found at {json_path}")
except Exception as e:
    logger.error(f"[Database] Error reading movies.json: {e}")
