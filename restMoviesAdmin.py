from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify, request, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


def validate_credentials(username, password, usersCollection):
    user = usersCollection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        return True
    return False


def login(myDB, request):
    usersCollection = myDB["users"]
    content_type = request.headers.get('Content-Type')
    print(content_type)

    if (content_type == 'application/json'):
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password or not validate_credentials(username,password, usersCollection):
            return jsonify({'mensaje': 'Invalid Credentials'}), 401
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return 'Content Type not accepted'


