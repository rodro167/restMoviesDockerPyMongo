import pymongo 
import json
from flask import Flask, jsonify, request, render_template
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from restMoviesGuest import *
from restMoviesAdmin import *
from restMoviesEditor import *
from bson import ObjectId

def connectToMongoDB():
    myClient = pymongo.MongoClient("mongodb://localhost:27017/unicode_decode_error_handler='ignore'")
    myDB = myClient["restMovies"]
    return myDB


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JWT_SECRET_KEY'] = 'setrocogirdor'  # Cambia esto a una cadena segura en un entorno de producción'''
jwt = JWTManager(app)
myDB = connectToMongoDB()


@app.route('/form/')
def showInsertForm():
    return render_template('form.html')

@app.route('/movies/', methods=['GET'])
@jwt_required()
def getMoviesPath():
    return getMovies(myDB)

@app.route('/movies/actor/<string:actor>', methods=['GET'])
@jwt_required()
def getMoviesByActorPath(actor):
    return getMoviesByActor(myDB, actor)

@app.route('/movies/actors', methods=['POST'])
@jwt_required()
def getMoviesByActorsPath():
    return getMoviesByActors(myDB, request)

@app.route('/movies/title/<string:title>', methods=['GET'])
@jwt_required()
def getMoviesByTitlePath(title):
    return getMoviesByTitle(myDB, title)

@app.route('/movies/country/<string:country>', methods=['GET'])
@jwt_required()
def getMoviesByCountryPath(country):
    return getMoviesByCountry(myDB, country)

@app.route('/movies/countries', methods=['POST'])
@jwt_required()
def getMoviesByCountriesPath():
    return getMoviesByCountries(myDB, request)


@app.route('/movies/genre/<string:genre>', methods=['GET'])
@jwt_required()
def getMoviesByGenrePath(genre):
    return getMoviesByGenre(myDB, genre)

@app.route('/movies/genres', methods=['POST'])
@jwt_required()
def getMoviesByGenresPath():
    return getMoviesByGenres(myDB, request)

    
@app.route('/movies/director/<string:director>', methods=['GET'])
@jwt_required()
def getMoviesByDirectorPath(director):
    return getMoviesByDirector(myDB, director)

@app.route('/movies/directors', methods=['POST'])
@jwt_required()
def getMoviesByDirectorsPath():
    return getMoviesByDirectors(myDB, request)


@app.route('/movies/runtime/lessthan/<int:runtime>', methods=['GET'])
@jwt_required()
def getMoviesByLessDuration(runtime):
    moviesCollection = myDB["movies"]
    query = {"runtime": { "$lt": runtime}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

@app.route('/movies/runtime/morethan/<int:runtime>', methods=['GET'])
@jwt_required()
def getMoviesByMoreDuration(runtime):
    moviesCollection = myDB["movies"]
    query = {"runtime": { "$gt": runtime}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

@app.route('/movies/runtime/<int:runtime>', methods=['GET'])
@jwt_required()
def getMoviesByDuration(runtime):
    moviesCollection = myDB["movies"]
    query = {"runtime": { "$eq": runtime}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

@app.route('/movies/year/before/<int:year>', methods=['GET'])
@jwt_required()
def getMoviesBeforeYear(year):
    moviesCollection = myDB["movies"]
    query = {"year": { "$lt": year}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

@app.route('/movies/year/after/<int:year>', methods=['GET'])
@jwt_required()
def getMoviesAfterYear(year):
    moviesCollection = myDB["movies"]
    query = {"year": { "$gt": year}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

@app.route('/movies/year/<int:year>', methods=['GET'])
@jwt_required()
def getMoviesByYear(year):
    moviesCollection = myDB["movies"]
    query = {"year": { "$eq": year}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

@app.route('/movies/create', methods=['POST'])
@jwt_required()
def createMovie():
    myDB = connectToMongoDB()
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        jsonBody = request.json
        result = moviesCollection.insert_one(jsonBody)
        if result.acknowledged:
            successfulInsertionMessage = str(result.inserted_id)
            print(successfulInsertionMessage)
            response_data = {"inserteId": successfulInsertionMessage }
        else:
            response_data = {"message": "Error al insertar el documento"}
        
        # Devuelve una respuesta en formato JSON
        return jsonify(response_data)
    else:
        return 'Content-Type not accepted'
    

@app.route('/movies/update/<string:_id>', methods=['PUT'])
@jwt_required()
def updateMovie(_id):
    myDB = connectToMongoDB()
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        
        documentId = ObjectId(_id)     
        jsonBody = request.get_json()
        filterCriteria = {'_id': documentId}
        updateOperation = {'$set': jsonBody}

        result = moviesCollection.update_one(filterCriteria, updateOperation)
        print(result.modified_count)
        print(result.raw_result)
        if result.modified_count > 0:
            successfulUpdateMessage = str(result)
            result_dict = {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id,
                "raw_result": result.raw_result,
                # Otros atributos que desees incluir
            }

            # Imprimir el resultado en formato JSON
            print(json.dumps(result_dict, indent=2))
            print(successfulUpdateMessage)
            response_data = {"updatedId": successfulUpdateMessage }
        else:
            response_data = {"message": "Error al insertar el documento"}
        
        # Devuelve una respuesta en formato JSON
        return jsonify(response_data)
    else:
        return 'Content-Type not accepted'
    
@app.route('/movies/delete/<string:_id>', methods=['DELETE'])
@jwt_required()
def deleteMovie(_id):
    myDB = connectToMongoDB()
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        
        documentId = ObjectId(_id)     
        filterCriteria = {'_id': documentId}
 
        result = moviesCollection.delete_one(filterCriteria)
        print(result.deleted_count)
        print(result.raw_result)
        if result.deleted_count > 0:
            successfulDeleteMessage = str(result)
            result_dict = {
                "modified_count": result.deleted_count,
                "raw_result": result.raw_result,
                # Otros atributos que desees incluir
            }

            # Imprimir el resultado en formato JSON
            print(json.dumps(result_dict, indent=2))
            print(successfulDeleteMessage)
            response_data = {"deletedId": successfulDeleteMessage }
        else:
            response_data = {"message": "Error al borrar el documento"}
        
        # Devuelve una respuesta en formato JSON
        return jsonify(response_data)
    else:
        return 'Content-Type not accepted'

@app.route('/users/register', methods=['POST'])
def registerUser():

    myDB = connectToMongoDB()
    usersCollection = myDB["users"]
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        jsonBody = request.json
        print(str(jsonBody))
        username = jsonBody['username']
        password = jsonBody['password']
        hashed_password = generate_password_hash(password, method='scrypt')
        print(hashed_password)
        result = usersCollection.insert_one({'username': username, 'password': hashed_password})
        if result.acknowledged:
            successfulInsertionMessage = str(result.inserted_id)
            print(successfulInsertionMessage)
            response_data = {"inserteId": successfulInsertionMessage }
        else:
            response_data = {"message": "Error al insertar el documento"}
        
        # Devuelve una respuesta en formato JSON
        return jsonify(response_data)
    else:
        return 'Content-Type not accepted'

@app.route('/users/updatePassword/<string:_id>', methods=['PUT'])
@jwt_required()
def updatePassword(_id):
    myDB = connectToMongoDB()
    usersCollection = myDB["users"]
    content_type = request.headers.get('Content-Type')
    print("HOlaaaaaaaaaaaaaaaaaaa")

    if (content_type == 'application/json'):
        
        documentId = ObjectId(_id)     
        jsonBody = request.get_json()
        filterCriteria = {'_id': documentId}

        jsonBody = request.json
        print(str(jsonBody))
        password = jsonBody['password']
        hashed_password = generate_password_hash(password, method='scrypt')
        print(hashed_password)
        jsonBody['password'] = hashed_password
        updateOperation = {'$set': jsonBody}


        result = usersCollection.update_one(filterCriteria, updateOperation)
        print(result.modified_count)
        print(result.raw_result)
        if result.modified_count > 0:
            successfulUpdateMessage = str(result)
            result_dict = {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id,
                "raw_result": result.raw_result,
                # Otros atributos que desees incluir
            }

            # Imprimir el resultado en formato JSON
            print(json.dumps(result_dict, indent=2))
            print(successfulUpdateMessage)
            response_data = {"updatedId": successfulUpdateMessage }
        else:
            response_data = {"message": "Error al insertar el documento"}
        
        # Devuelve una respuesta en formato JSON
        return jsonify(response_data)
    else:
        return 'Content-Type not accepted'


@app.route('/login', methods=['POST'])
def loginPath():
    return login(myDB, request)

@app.route('/users/delete/<string:_id>', methods=['DELETE'])
@jwt_required()
def deleteUsers(_id):
    myDB = connectToMongoDB()
    usersCollection = myDB["users"]
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        
        documentId = ObjectId(_id)     
        filterCriteria = {'_id': documentId}
 
        result = usersCollection.delete_one(filterCriteria)
        if result.deleted_count > 0:
            successfulDeleteMessage = str(result)
            result_dict = {
                "modified_count": result.deleted_count,
                "raw_result": result.raw_result,
            }
            response_data = {"deletedId": successfulDeleteMessage }
        else:
            response_data = {"message": "Error deleting user"}
        
        # Devuelve una respuesta en formato JSON
        return jsonify(response_data)
    else:
        return 'Content-Type not accepted'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
