import re
import logging
from datetime import datetime, timezone
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from bson import ObjectId
from db_helpers import query_movies, parse_object_id, require_json

logger = logging.getLogger(__name__)


def getMovies(db):
    """Return all movies, with optional pagination via ?page=&limit= query params."""
    page = request.args.get('page', default=None, type=int)
    limit = request.args.get('limit', default=20, type=int)
    return query_movies(db, page=page, limit=limit)


def getMoviesByTitle(db, title):
    """Return movies whose title matches the search term (case-insensitive)."""
    regex_pattern = re.compile(f".*{re.escape(title)}.*", re.IGNORECASE)
    return query_movies(db, {"title": {"$regex": regex_pattern}})


def getMoviesByActor(db, actor):
    """Return movies featuring a specific actor."""
    return query_movies(db, {"cast": actor})


def getMoviesByActors(db):
    """Return movies featuring any of the provided actors."""
    body = require_json(request)
    actors = body.get('actors', [])
    return query_movies(db, {"cast": {"$in": actors}})


def getMoviesByCountry(db, country):
    """Return movies from a specific country."""
    return query_movies(db, {"countries": country})


def getMoviesByCountries(db):
    """Return movies from any of the provided countries."""
    body = require_json(request)
    countries = body.get('countries', [])
    return query_movies(db, {"countries": {"$in": countries}})


def getMoviesByGenre(db, genre):
    """Return movies of a specific genre."""
    return query_movies(db, {"genres": genre})


def getMoviesByGenres(db):
    """Return movies of any of the provided genres."""
    body = require_json(request)
    genres = body.get('genres', [])
    return query_movies(db, {"genres": {"$in": genres}})


def getMoviesByDirector(db, director):
    """Return movies by a specific director."""
    return query_movies(db, {"directors": director})


def getMoviesByDirectors(db):
    """Return movies by any of the provided directors."""
    body = require_json(request)
    directors = body.get('directors', [])
    return query_movies(db, {"directors": {"$in": directors}})


# ---------------------------------------------------------------------------
# Ratings & Comments
# ---------------------------------------------------------------------------
def rateMovie(db):
    """Rate a movie (1-10 stars). One rating per user per movie (upsert).

    Expects JSON body: {"movieId": "<id>", "stars": <1-10>}
    The logged-in user (from JWT) is recorded as the rater.
    """
    body = require_json(request)
    username = get_jwt_identity()

    movie_id_str = body.get('movieId')
    stars = body.get('stars')

    if not movie_id_str:
        return jsonify({"error": "movieId is required"}), 400

    movie_id = parse_object_id(movie_id_str)

    # Validate stars
    if stars is None or not isinstance(stars, (int, float)):
        return jsonify({"error": "stars must be a number between 1 and 10"}), 400
    stars = int(stars)
    if stars < 1 or stars > 10:
        return jsonify({"error": "stars must be between 1 and 10"}), 400

    # Verify movie exists
    if db["movies"].find_one({"_id": movie_id}) is None:
        return jsonify({"error": "Movie not found"}), 404

    ratings_collection = db["ratings"]
    now = datetime.now(timezone.utc)

    # Upsert: one rating per user per movie
    result = ratings_collection.update_one(
        {"movieId": movie_id_str, "userId": username},
        {"$set": {"stars": stars, "updatedAt": now},
         "$setOnInsert": {"createdAt": now}},
        upsert=True,
    )

    if result.upserted_id:
        logger.info("User '%s' rated movie %s with %d stars (new)", username, movie_id_str, stars)
        return jsonify({"message": "Rating created", "stars": stars}), 201
    else:
        logger.info("User '%s' updated rating for movie %s to %d stars", username, movie_id_str, stars)
        return jsonify({"message": "Rating updated", "stars": stars}), 200


def commentMovie(db):
    """Add a comment to a movie.

    Expects JSON body: {"movieId": "<id>", "comment": "<text>"}
    The logged-in user (from JWT) is recorded as the commenter.
    """
    body = require_json(request)
    username = get_jwt_identity()

    movie_id_str = body.get('movieId')
    comment = body.get('comment')

    if not movie_id_str:
        return jsonify({"error": "movieId is required"}), 400
    if not comment or not isinstance(comment, str) or not comment.strip():
        return jsonify({"error": "comment must be a non-empty string"}), 400

    movie_id = parse_object_id(movie_id_str)

    # Verify movie exists
    if db["movies"].find_one({"_id": movie_id}) is None:
        return jsonify({"error": "Movie not found"}), 404

    comments_collection = db["comments"]
    now = datetime.now(timezone.utc)

    result = comments_collection.insert_one({
        "movieId": movie_id_str,
        "userId": username,
        "comment": comment.strip(),
        "createdAt": now,
    })

    logger.info("User '%s' commented on movie %s", username, movie_id_str)
    return jsonify({
        "message": "Comment added",
        "insertedId": str(result.inserted_id),
    }), 201


def getStars(db, movie_id_str):
    """Return all individual ratings and the average for a movie.

    Response:
    {
        "movieId": "...",
        "title": "...",
        "ratings": [{"userId": "...", "stars": N}, ...],
        "averageRating": X.X,
        "totalRatings": N
    }
    """
    movie_id = parse_object_id(movie_id_str)

    movie = db["movies"].find_one({"_id": movie_id}, {"_id": 0, "title": 1})
    if movie is None:
        return jsonify({"error": "Movie not found"}), 404

    ratings_collection = db["ratings"]
    cursor = ratings_collection.find(
        {"movieId": movie_id_str},
        {"_id": 0, "userId": 1, "stars": 1},
    )

    ratings = list(cursor)
    total = len(ratings)
    average = round(sum(r["stars"] for r in ratings) / total, 2) if total > 0 else 0

    return jsonify({
        "movieId": movie_id_str,
        "title": movie.get("title"),
        "ratings": ratings,
        "averageRating": average,
        "totalRatings": total,
    }), 200


def getComments(db, movie_id_str):
    """Return all comments for a movie, ordered newest first.

    Response:
    {
        "movieId": "...",
        "title": "...",
        "comments": [{"userId": "...", "comment": "...", "createdAt": "..."}, ...],
        "totalComments": N
    }
    """
    movie_id = parse_object_id(movie_id_str)

    movie = db["movies"].find_one({"_id": movie_id}, {"_id": 0, "title": 1})
    if movie is None:
        return jsonify({"error": "Movie not found"}), 404

    comments_collection = db["comments"]
    cursor = comments_collection.find(
        {"movieId": movie_id_str},
        {"_id": 0, "userId": 1, "comment": 1, "createdAt": 1},
    ).sort("createdAt", -1)

    comments = []
    for c in cursor:
        c["createdAt"] = c["createdAt"].isoformat() if c.get("createdAt") else None
        comments.append(c)

    return jsonify({
        "movieId": movie_id_str,
        "title": movie.get("title"),
        "comments": comments,
        "totalComments": len(comments),
    }), 200
