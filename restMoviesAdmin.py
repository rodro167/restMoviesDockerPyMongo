import logging
from werkzeug.security import check_password_hash
from flask import jsonify
from flask_jwt_extended import create_access_token
from db_helpers import require_json

logger = logging.getLogger(__name__)


def validate_credentials(username, password, users_collection):
    """Check if the username/password pair is valid."""
    user = users_collection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        return True
    return False


def login(db, request):
    """Authenticate a user and return a JWT access token."""
    body = require_json(request)
    username = body.get('username', None)
    password = body.get('password', None)

    users_collection = db["users"]

    if not username or not password or not validate_credentials(username, password, users_collection):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=username)
    logger.info("User '%s' logged in successfully", username)
    return jsonify(access_token=access_token), 200
