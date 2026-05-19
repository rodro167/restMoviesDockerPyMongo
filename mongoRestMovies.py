import os
import logging
from flask import Flask, jsonify, request
import pymongo
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager, jwt_required
from prometheus_flask_exporter import PrometheusMetrics
from datetime import timedelta
from dotenv import load_dotenv

from restMoviesGuest import (
    getMovies, getMoviesByTitle, getMoviesByActor, getMoviesByActors,
    getMoviesByCountry, getMoviesByCountries, getMoviesByGenre,
    getMoviesByGenres, getMoviesByDirector, getMoviesByDirectors,
    rateMovie, commentMovie, getStars, getComments,
)
from restMoviesAdmin import login
from db_helpers import query_movies, parse_object_id, require_json

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
'''MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")'''
MONGO_DB = os.getenv("MONGO_DB", "restMovies")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-this-to-a-secure-random-string")
FLASK_PORT = int(os.getenv("FLASK_PORT", "4000"))
JWT_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))


def connect_to_mongodb():
    """Create and return the MongoDB database handle (single connection)."""
    client = pymongo.MongoClient(MONGO_URI)
    return client[MONGO_DB]


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=JWT_EXPIRES_HOURS)
jwt = JWTManager(app)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'RestMovies API', version='1.0')
db = connect_to_mongodb()


# ---------------------------------------------------------------------------
# Error handlers — consistent JSON error responses
# ---------------------------------------------------------------------------
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error.description)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Movies — READ endpoints
# ---------------------------------------------------------------------------
@app.route('/movies/', methods=['GET'])
@jwt_required()
def get_movies():
    return getMovies(db)


@app.route('/movies/actor/<string:actor>', methods=['GET'])
@jwt_required()
def get_movies_by_actor(actor):
    return getMoviesByActor(db, actor)


@app.route('/movies/actors', methods=['POST'])
@jwt_required()
def get_movies_by_actors():
    return getMoviesByActors(db)


@app.route('/movies/title/<string:title>', methods=['GET'])
@jwt_required()
def get_movies_by_title(title):
    return getMoviesByTitle(db, title)


@app.route('/movies/country/<string:country>', methods=['GET'])
@jwt_required()
def get_movies_by_country(country):
    return getMoviesByCountry(db, country)


@app.route('/movies/countries', methods=['POST'])
@jwt_required()
def get_movies_by_countries():
    return getMoviesByCountries(db)


@app.route('/movies/genre/<string:genre>', methods=['GET'])
@jwt_required()
def get_movies_by_genre(genre):
    return getMoviesByGenre(db, genre)


@app.route('/movies/genres', methods=['POST'])
@jwt_required()
def get_movies_by_genres():
    return getMoviesByGenres(db)


@app.route('/movies/director/<string:director>', methods=['GET'])
@jwt_required()
def get_movies_by_director(director):
    return getMoviesByDirector(db, director)


@app.route('/movies/directors', methods=['POST'])
@jwt_required()
def get_movies_by_directors():
    return getMoviesByDirectors(db)


@app.route('/movies/runtime/lessthan/<int:runtime>', methods=['GET'])
@jwt_required()
def get_movies_runtime_less(runtime):
    return query_movies(db, {"runtime": {"$lt": runtime}})


@app.route('/movies/runtime/morethan/<int:runtime>', methods=['GET'])
@jwt_required()
def get_movies_runtime_more(runtime):
    return query_movies(db, {"runtime": {"$gt": runtime}})


@app.route('/movies/runtime/<int:runtime>', methods=['GET'])
@jwt_required()
def get_movies_by_runtime(runtime):
    return query_movies(db, {"runtime": {"$eq": runtime}})


@app.route('/movies/year/before/<int:year>', methods=['GET'])
@jwt_required()
def get_movies_before_year(year):
    return query_movies(db, {"year": {"$lt": year}})


@app.route('/movies/year/after/<int:year>', methods=['GET'])
@jwt_required()
def get_movies_after_year(year):
    return query_movies(db, {"year": {"$gt": year}})


@app.route('/movies/year/<int:year>', methods=['GET'])
@jwt_required()
def get_movies_by_year(year):
    return query_movies(db, {"year": {"$eq": year}})


# ---------------------------------------------------------------------------
# Movies — Ratings & Comments
# ---------------------------------------------------------------------------
@app.route('/movies/rate', methods=['POST'])
@jwt_required()
def rate_movie():
    return rateMovie(db)


@app.route('/movies/comment', methods=['POST'])
@jwt_required()
def comment_movie():
    return commentMovie(db)


@app.route('/movies/<string:movie_id>/stars', methods=['GET'])
@jwt_required()
def get_stars(movie_id):
    return getStars(db, movie_id)


@app.route('/movies/<string:movie_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(movie_id):
    return getComments(db, movie_id)


# ---------------------------------------------------------------------------
# Movies — WRITE endpoints  (RESTful paths)
# ---------------------------------------------------------------------------
@app.route('/movies/', methods=['POST'])
@app.route('/movies/create', methods=['POST'])   # legacy alias
@jwt_required()
def create_movie():
    json_body = require_json(request)
    collection = db["movies"]

    result = collection.insert_one(json_body)
    if result.acknowledged:
        logger.info("Movie inserted with id: %s", result.inserted_id)
        return jsonify({"insertedId": str(result.inserted_id)}), 201
    else:
        return jsonify({"error": "Failed to insert the movie"}), 500


@app.route('/movies/<string:_id>', methods=['PUT'])
@app.route('/movies/update/<string:_id>', methods=['PUT'])   # legacy alias
@jwt_required()
def update_movie(_id):
    document_id = parse_object_id(_id)
    json_body = require_json(request)
    collection = db["movies"]

    result = collection.update_one({'_id': document_id}, {'$set': json_body})

    if result.matched_count == 0:
        return jsonify({"error": "Movie not found"}), 404

    logger.info("Movie %s updated (modified: %d)", _id, result.modified_count)
    return jsonify({
        "matchedCount": result.matched_count,
        "modifiedCount": result.modified_count,
    }), 200


@app.route('/movies/<string:_id>', methods=['DELETE'])
@app.route('/movies/delete/<string:_id>', methods=['DELETE'])   # legacy alias
@jwt_required()
def delete_movie(_id):
    document_id = parse_object_id(_id)
    collection = db["movies"]

    result = collection.delete_one({'_id': document_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Movie not found"}), 404

    logger.info("Movie %s deleted", _id)
    return jsonify({"deletedCount": result.deleted_count}), 200


# ---------------------------------------------------------------------------
# Users — Auth & management
# ---------------------------------------------------------------------------
@app.route('/login', methods=['POST'])
def login_path():
    return login(db, request)


@app.route('/users/register', methods=['POST'])
def register_user():
    json_body = require_json(request)
    users_collection = db["users"]

    username = json_body.get('username')
    password = json_body.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if user already exists
    if users_collection.find_one({'username': username}):
        return jsonify({"error": "Username already exists"}), 409

    hashed_password = generate_password_hash(password, method='scrypt')
    result = users_collection.insert_one({'username': username, 'password': hashed_password})

    if result.acknowledged:
        logger.info("User '%s' registered", username)
        return jsonify({"insertedId": str(result.inserted_id)}), 201
    else:
        return jsonify({"error": "Failed to register user"}), 500


@app.route('/users/<string:_id>/password', methods=['PUT'])
@jwt_required()
def update_password(_id):
    document_id = parse_object_id(_id)
    json_body = require_json(request)
    users_collection = db["users"]

    password = json_body.get('password')
    if not password:
        return jsonify({"error": "Password is required"}), 400

    hashed_password = generate_password_hash(password, method='scrypt')
    result = users_collection.update_one(
        {'_id': document_id},
        {'$set': {'password': hashed_password}},
    )

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    logger.info("Password updated for user %s", _id)
    return jsonify({"modifiedCount": result.modified_count}), 200


@app.route('/users/<string:_id>', methods=['DELETE'])
@jwt_required()
def delete_user(_id):
    document_id = parse_object_id(_id)
    users_collection = db["users"]

    result = users_collection.delete_one({'_id': document_id})

    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404

    logger.info("User %s deleted", _id)
    return jsonify({"deletedCount": result.deleted_count}), 200


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT)
