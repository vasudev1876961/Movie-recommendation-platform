# backend/app/models/movie.py
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.app.database.database import Base

# Many-to-Many Link Table for Movie and Genre
movie_genre = Table(
    "movie_genre",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)
)

# Many-to-Many Link Table for Movie and Director
movie_director = Table(
    "movie_director",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", Integer, ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True)
)

class MovieCast(Base):
    __tablename__ = "movie_cast"

    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    cast_member_id = Column(Integer, ForeignKey("cast_members.id", ondelete="CASCADE"), primary_key=True)
    cast_order = Column(Integer, default=0)
    character = Column(String, default="")

    movie = relationship("Movie", back_populates="cast_associations")
    cast_member = relationship("CastMember", back_populates="movie_associations")

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String, index=True, nullable=False)
    overview = Column(Text, default="")
    release_date = Column(String, default="")
    runtime = Column(Integer, default=0)
    rating = Column(Float, default=0.0) # vote_average
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0)
    original_language = Column(String, default="en")
    poster_path = Column(String, default="")
    backdrop_path = Column(String, default="")
    homepage = Column(String, default="")
    tagline = Column(String, default="")
    keywords = Column(Text, default="")
    mood = Column(String, default="")

    genres = relationship("Genre", secondary=movie_genre, back_populates="movies", lazy="joined")
    directors = relationship("Director", secondary=movie_director, back_populates="movies", lazy="joined")
    cast_associations = relationship(
        "MovieCast",
        back_populates="movie",
        cascade="all, delete-orphan",
        order_by="MovieCast.cast_order",
        lazy="joined"
    )

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    movies = relationship("Movie", secondary=movie_genre, back_populates="genres")

class Director(Base):
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    movies = relationship("Movie", secondary=movie_director, back_populates="directors")

class CastMember(Base):
    __tablename__ = "cast_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    movie_associations = relationship("MovieCast", back_populates="cast_member")
