from flask import jsonify
from flask_jwt_extended import get_jwt_identity
import re

def getMovies(myDB):
    moviesCollection = myDB["movies"]
    moviesList = moviesCollection.find()
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

def getMoviesByTitle(myDB, title):
    moviesCollection = myDB["movies"]
    regex_pattern = re.compile(f".*{re.escape(title)}.*", re.IGNORECASE)
    query = {"title": {"$regex": regex_pattern}}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

def getMoviesByActor(myDB, actor):
    moviesCollection = myDB["movies"]
    query = {"cast": actor}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

def getMoviesByActors(myDB, request):
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')
  
    if (content_type == 'application/json'):
        actors = request.json.get('actors', [])
        query = {"cast": {"$in": actors}}
        moviesList = moviesCollection.find(query)
        movies = []
        for movie in moviesList:
            movie['_id'] = str(movie['_id'])
            movies.append(movie)
        data_dict = {"movies": movies}
        return jsonify(data_dict)
    else:
        return 'Content Type not accepted'
    
def getMoviesByCountry(myDB, country):
    moviesCollection = myDB["movies"]
    query = {"countries": country}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

def getMoviesByCountries(myDB, request):
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        countries = request.json.get('countries', [])
        query = {"countries": {"$in": countries}}
        moviesList = moviesCollection.find(query)
        movies = []
        for movie in moviesList:
            movie['_id'] = str(movie['_id'])
            movies.append(movie)
        data_dict = {"movies": movies}
        return jsonify(data_dict)
    else:
        return 'Content Type not accepted'

def getMoviesByGenre(myDB, genre):
    moviesCollection = myDB["movies"]
    query = {"genres": genre}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

def getMoviesByGenres(myDB, request):
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        genres = request.json.get('genres', [])
        query = {"genres": {"$in": genres}}
        moviesList = moviesCollection.find(query)
        movies = []
        for movie in moviesList:
            movie['_id'] = str(movie['_id'])
            movies.append(movie)
        data_dict = {"movies": movies}
        return jsonify(data_dict)
    else:
        return 'Content Type not accepted'

def getMoviesByDirector(myDB, director):
    moviesCollection = myDB["movies"]
    query = {"directors": director}
    moviesList = moviesCollection.find(query)
    movies = []
    for movie in moviesList:
        movie['_id'] = str(movie['_id'])
        movies.append(movie)
    data_dict = {"movies": movies}
    return jsonify(data_dict)

def getMoviesByDirectors(myDB, request):
    moviesCollection = myDB["movies"]
    content_type = request.headers.get('Content-Type')
  
    if (content_type == 'application/json'):
        directors = request.json.get('directors', [])
        query = {"directors": {"$in": directors}}
        moviesList = moviesCollection.find(query)
        movies = []
        for movie in moviesList:
            movie['_id'] = str(movie['_id'])
            movies.append(movie)
        data_dict = {"movies": movies}
        return jsonify(data_dict)
    else:
        return 'Content Type not accepted'


    
