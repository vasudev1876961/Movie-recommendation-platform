# scripts/import_movies.py
import sys
import os

# Add root directory to python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from backend.app.database.seed import run_seed

if __name__ == "__main__":
    print("="*60)
    print("Movie AI Platform - SQLite Database Seeder")
    print("="*60)
    run_seed()
