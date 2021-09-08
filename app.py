import sqlite3
import datetime
import sys
import logging
from flask import Flask, request, jsonify
from flask_jwt import jwt_required, current_identity
from flask_cors import CORS, cross_origin


# compares username and password to database
def user_dict(cursor, row):
    u = {}
    for idx, col in enumerate(cursor.description):
        u[col[0]] = row[idx]
    return u


# defining user class as object
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# opening user table in db
def init_user_table():
    conn = sqlite3.connect("store.db")
    print("opened database")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created")
    conn.close()


init_user_table()


# creating records table in db
def init_records_info():
    with sqlite3.connect('store.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "artist TEXT NOT NULL,"
                     "album TEXT NOT NULL,"
                     "price INTEGER NOT NULL,"
                     "genre TEXT NOT NULL,"
                     "year INTEGER NOT NULL,"
                     "description TEXT NOT NULL,"
                     "date_added TEXT NOT NULL)")
    print("product table created successfully.")


# calling tables
init_records_info()

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.debug = True
app.config["SECRET_KEY"] = "super-secret"
CORS(app)


@app.route('/protected/')
def protected():
    return '%s' % current_identity


# adding users
@app.route('/user-section', methods=["GET", "POST", "PATCH"])
@cross_origin(origin='*')
def user_register():
    response = {}

    # display all users
    if request.method == "GET":
        with sqlite3.connect("store.db") as conn:
            # conn.row_factory = user_dict()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user")

            users = cursor.fetchall()

            response["status_code"] = 200
            response["data"] = users
            return response

    # user login
    if request.method == "PATCH":
        try:
            username = request.json["username"]
            password = request.json["password"]

            with sqlite3.connect("store.db") as conn:
                conn.row_factory = user_dict
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user WHERE username=? AND password=?", (username, password))

                user = cursor.fetchone()

            response["status_code"] = 200
            response["data"] = user
            return response
        except ValueError:
            response["status_code"] = 500
            response["data"] = "User not found"
            return response

    # registration for user
    if request.method == "POST":
        try:
            first_name = request.json["first_name"]
            last_name = request.json["last_name"]
            username = request.json["username"]
            password = request.json["password"]

            with sqlite3.connect("store.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO user("
                               "first_name,"
                               "last_name,"
                               "username,"
                               "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
                conn.commit()
                response["message"] = "new user added"
                response["status_code"] = 201
            return response
        except ValueError:
            response["message"] = "unsuccessful"
            response["status_code"] = 209
            return response


# adding products to db
@app.route('/add-records/', methods=["POST"])
def add_products():
    response = {}

    if request.method == "POST":
        artist = request.form['artist']
        album = request.form['album']
        price = request.form['price']
        genre = request.form['genre']
        year = request.form['year']
        description = request.form['description']
        date_added = datetime.datetime.now()

        with sqlite3.connect("store.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO records("
                           "artist,"
                           "album,"
                           "price,"
                           "genre,"
                           "year,"
                           "description,"
                           "date_added) VALUES(?, ?, ?, ?, ?, ?, ?)",
                           (artist, album, price, genre, year, description, date_added))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "record added"
        return response


# viewing records in db
@app.route('/view-records/', methods=["GET"])
def get_records():
    response = {}

    with sqlite3.connect("store.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records")

        records = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = records
    return response


# viewing users in db
@app.route('/view-users/', methods=["GET"])
def get_users():
    response = {}
    with sqlite3.connect("store.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")

        registered_users = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = registered_users
    return response


# to delete records in db
@app.route("/delete-record/<int:record_id>")
def delete_record(record_id):
    response = {}
    with sqlite3.connect("store.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM records WHERE id=" + str(record_id))
        conn.commit()
        response["status_code"] = 200
        response["message"] = "record deleted"
    return response


# delete users in db
@app.route("/delete-user/<int:user_id>")
@jwt_required()
def delete_user(user_id):
    response = {}
    with sqlite3.connect("store.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE id=" + str(user_id))
        conn.commit()
        response["status_code"] = 200
        response["message"] = "user deleted"
    return response


# editing records in the db
@app.route('/edit_records/<int:record_id>/', methods=["PUT"])
def edit_record(record_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('store.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("artist") is not None:
                put_data["artist"] = incoming_data.get("artist")
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE records SET artist=? WHERE id=?", (put_data["artist"], record_id))
                    conn.commit()
                    response['message'] = "Updated artist"
                    response['status_code'] = 200
            if incoming_data.get("album") is not None:
                put_data["album"] = incoming_data.get("album")
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE records SET album=? WHERE id=?", (put_data["album"], record_id))
                    conn.commit()
                    response['message'] = "Updated album"
                    response['status_code'] = 200
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE records SET price =? WHERE id=?", (put_data["price"], record_id))
                    conn.commit()
                    response['price'] = "Price adjusted"
                    response['status_code'] = 200
            if incoming_data.get("genre") is not None:
                put_data['genre'] = incoming_data.get('genre')
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE records SET genre =? WHERE id=?", (put_data["genre"], record_id))
                    conn.commit()
                    response['genre'] = "new genre updated"
                    response['status_code'] = 200
            if incoming_data.get("year") is not None:
                put_data['year'] = incoming_data.get('year')
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE records SET year =? WHERE id=?", (put_data["year"], record_id))
                    conn.commit()
                    response['description'] = "updated year"
                    response['status_code'] = 200
            if incoming_data.get("description") is not None:
                put_data['description'] = incoming_data.get('description')
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE records SET description =? WHERE id=?",
                                   (put_data["description"], record_id))
                    conn.commit()
                    response['description'] = "new description"
                    response['status_code'] = 200
    return response


# editing a user's details
@app.route('/edit_user/<int:user_id>/', methods=["PUT"])
def edit_user(user_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('store.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("first_name") is not None:
                put_data["first_name"] = incoming_data.get("first_name")
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user SET first_name=? WHERE id=?", (put_data["first_name"], user_id))
                    conn.commit()
                    response['message'] = "updated first name"
                    response['status_code'] = 200
            if incoming_data.get("last_name") is not None:
                put_data["last_name"] = incoming_data.get("last_name")
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user SET last_name=? WHERE id=?", (put_data["last_name"], user_id))
                    conn.commit()
                    response['message'] = "updated last name"
                    response['status_code'] = 200
            if incoming_data.get("username") is not None:
                put_data["username"] = incoming_data.get("username")
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user SET username=? WHERE id=?", (put_data["username"], user_id))
                    conn.commit()
                    response['message'] = "updated user name"
                    response['status_code'] = 200
            if incoming_data.get("password") is not None:
                put_data["password"] = incoming_data.get("password")
                with sqlite3.connect('store.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user SET password=? WHERE id=?", (put_data["password"], user_id))
                    conn.commit()
                    response['message'] = "updated password"
                    response['status_code'] = 200
    return response


# viewing a single record
@app.route('/get-record/<int:record_id>/', methods=["GET"])
def get_item(record_id):
    response = {}

    with sqlite3.connect("store.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records WHERE id=?" + str(record_id))

        response["status_code"] = 200
        response["description"] = "record added"
        response["data"] = cursor.fetchone()

    return jsonify(response)


# viewing a single user
@app.route('/get-user/<int:user_id>', methods=["GET"])
def get_user(user_id):
    response = {}

    with sqlite3.connect("store.db") as conn:
        # conn.row_user = user_dict()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE id=?" + str(user_id))
        user = cursor.fetchone()
    response["status_code"] = 200
    response["data"] = user
    return response


if __name__ == '__main__':
    app.debug = True
    app.run()
