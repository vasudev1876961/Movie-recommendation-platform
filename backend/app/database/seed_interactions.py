# backend/app/database/seed_interactions.py
import os
import sys
import logging

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sqlalchemy.orm import Session
from backend.app.database.database import engine, SessionLocal
from backend.app.models.user import User, WatchlistItem
from backend.app.models.movie import Movie
from backend.app.models.rating import Rating
from backend.app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_interactions")

SAMPLE_USERS = [
    {
        "username": "demo_user",
        "email": "demo@movierec.ai",
        "password": "password123",
        "profile_type": "Hybrid Explorer"
    },
    {
        "username": "scifi_geek",
        "email": "scifi@movierec.ai",
        "password": "password123",
        "profile_type": "Sci-Fi & Mind-Bending"
    },
    {
        "username": "action_addict",
        "email": "action@movierec.ai",
        "password": "password123",
        "profile_type": "Action & Epic Sagas"
    },
    {
        "username": "cinephile_critic",
        "email": "critic@movierec.ai",
        "password": "password123",
        "profile_type": "Masterpieces & Drama"
    },
    {
        "username": "animation_lover",
        "email": "animation@movierec.ai",
        "password": "password123",
        "profile_type": "Animation & Family"
    },
    {
        "username": "dark_thriller_fan",
        "email": "thriller@movierec.ai",
        "password": "password123",
        "profile_type": "Dark & Psychological"
    }
]

def seed_users_and_interactions():
    db: Session = SessionLocal()
    try:
        logger.info("Seeding archetypal user profiles and interaction matrix...")
        
        # 1. Create or retrieve users
        user_map = {}
        for u_data in SAMPLE_USERS:
            user = db.query(User).filter(User.username == u_data["username"]).first()
            if not user:
                user = User(
                    username=u_data["username"],
                    email=u_data["email"],
                    hashed_password=get_password_hash(u_data["password"])
                )
                db.add(user)
                db.flush()
                logger.info(f"Created user profile: {user.username} (ID: {user.id})")
            user_map[u_data["username"]] = user

        # 2. Query movie catalogue
        all_movies = db.query(Movie).all()
        movie_by_title = {m.title.lower().strip(): m for m in all_movies}

        def find_movie(query: str):
            q = query.lower().strip()
            if q in movie_by_title:
                return movie_by_title[q]
            for title, m in movie_by_title.items():
                if q in title:
                    return m
            return None

        # 3. Define curated taste preferences and interaction maps
        taste_profiles = {
            "demo_user": [
                ("Inception", 9.5, "Absolute masterpiece of storytelling and concept."),
                ("The Dark Knight", 9.0, "Best superhero crime drama ever created."),
                ("Interstellar", 9.5, "Emotional and visually stunning sci-fi."),
                ("Parasite", 9.0, "Phenomenal tension and social commentary.")
            ],
            "scifi_geek": [
                ("Inception", 10.0, "Mind-bending perfection."),
                ("Interstellar", 10.0, "Unbelievable score and emotional depth."),
                ("The Matrix", 9.5, "Changed cinema forever."),
                ("Blade Runner 2049", 9.5, "Visual masterclass in cyberpunk."),
                ("Arrival", 9.0, "Brilliant take on alien linguistics."),
                ("The Prestige", 9.0, "Nolan's best puzzle."),
                ("Dune", 9.0, "Epic scale space opera."),
                ("Tenet", 8.0, "Complex temporal dynamics."),
                ("Avatar", 7.5, "Stunning visuals.")
            ],
            "action_addict": [
                ("The Dark Knight", 10.0, "Legendary action choreography."),
                ("Mad Max: Fury Road", 10.0, "Non-stop pure adrenaline."),
                ("John Wick", 9.5, "Reinvented modern gun-fu."),
                ("Gladiator", 9.5, "Are you not entertained?"),
                ("Avengers: Endgame", 9.0, "Culmination of 10 years of cinema."),
                ("Top Gun: Maverick", 9.0, "Real jet footage was unbelievable."),
                ("The Batman", 8.5, "Gritty detective action."),
                ("Spider-Man: Across the Spider-Verse", 9.0, "Action animation benchmark.")
            ],
            "cinephile_critic": [
                ("The Godfather", 10.0, "The pinnacle of cinematic storytelling."),
                ("Pulp Fiction", 9.5, "Tarantino's magnum opus."),
                ("Parasite", 9.5, "Masterful direction by Bong Joon-ho."),
                ("Whiplash", 9.5, "Insanely tight pacing and performances."),
                ("Schindler's List", 10.0, "Haunting and deeply moving."),
                ("Fight Club", 9.0, "Iconic psychological commentary."),
                ("GoodFellas", 9.5, "Scorsese at his finest."),
                ("12 Angry Men", 10.0, "Pure dialogue masterwork.")
            ],
            "animation_lover": [
                ("Spirited Away", 10.0, "Miyazaki's absolute masterwork."),
                ("Spider-Man: Into the Spider-Verse", 9.5, "Revolutionized modern animation aesthetics."),
                ("WALL-E", 9.5, "Heartwarming first act with zero dialogue."),
                ("Coco", 9.0, "Beautiful tribute to family and memory."),
                ("Up", 9.0, "The opening 10 minutes are legendary."),
                ("Princess Mononoke", 9.5, "Epic environmental fantasy."),
                ("The Lion King", 9.0, "Timeless Disney classic.")
            ],
            "dark_thriller_fan": [
                ("Se7en", 10.0, "Grim, atmospheric, and unforgettable ending."),
                ("The Silence of the Lambs", 9.5, "Hopkins and Foster are electrifying."),
                ("Zodiac", 9.0, "Fincher's obsessive procedural perfection."),
                ("Shutter Island", 9.0, "Insane psychological tension and twist."),
                ("Gone Girl", 8.5, "Cynical modern thriller."),
                ("Prisoners", 9.5, "Emotionally gut-wrenching and relentless."),
                ("Joker", 8.5, "Phenomenal character study.")
            ]
        }

        # 4. Insert Ratings into SQLite (with upsert)
        ratings_added = 0
        for username, ratings_list in taste_profiles.items():
            user = user_map.get(username)
            if not user:
                continue

            for movie_title, score, review in ratings_list:
                movie = find_movie(movie_title)
                if movie:
                    existing = db.query(Rating).filter(
                        Rating.user_id == user.id,
                        Rating.movie_id == movie.id
                    ).first()
                    if not existing:
                        db.add(Rating(
                            user_id=user.id,
                            movie_id=movie.id,
                            score=score,
                            review=review
                        ))
                        ratings_added += 1

        db.commit()
        logger.info(f"Interaction matrix successfully seeded with {ratings_added} ratings across {len(taste_profiles)} archetypes.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding interactions: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    seed_users_and_interactions()
