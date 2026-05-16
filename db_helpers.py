import logging
from flask import jsonify, abort
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)


def query_movies(db, query=None, page=None, limit=20):
    """Run a query against the movies collection and return a JSON response.

    Args:
        db: The MongoDB database instance.
        query: A MongoDB query dict (default: None = all movies).
        page: Optional page number for pagination (1-based).
        limit: Number of results per page (default 20).

    Returns:
        A Flask JSON response with the matching movies.
    """
    collection = db["movies"]
    cursor = collection.find(query or {})

    if page and page > 0:
        cursor = cursor.skip((page - 1) * limit).limit(limit)

    movies = []
    for movie in cursor:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)

    return jsonify({"movies": movies})


def parse_object_id(id_string):
    """Safely parse a string into a BSON ObjectId.

    Args:
        id_string: The string to convert.

    Returns:
        A valid ObjectId.

    Raises:
        400 abort if the string is not a valid ObjectId.
    """
    try:
        return ObjectId(id_string)
    except (InvalidId, TypeError):
        logger.warning("Invalid ObjectId received: %s", id_string)
        abort(400, description=f"Invalid ID format: {id_string}")


def require_json(request):
    """Validate that the request has a JSON content type and body.

    Args:
        request: The Flask request object.

    Returns:
        The parsed JSON body.

    Raises:
        400 abort if content type is not JSON or body is missing.
    """
    if not request.is_json:
        abort(400, description="Content-Type must be application/json")
    body = request.get_json(silent=True)
    if body is None:
        abort(400, description="Request body must be valid JSON")
    return body
