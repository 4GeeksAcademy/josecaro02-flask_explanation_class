"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user/<int:user_id>', methods=['GET'])
def handle_hello(user_id):
    users = User.query.all()
    single_user = User.query.get(user_id)
    filter_users = User.query.filter_by(is_active = True)
    # print(type(filter_users))
    # print(filter_users)
    filter_users_serialized = list(map(lambda x : x.serialize(), filter_users))
    print(filter_users_serialized)
    if single_user is None:
        # return jsonify({"msg": f"El usuario con el id {user_id} no existe"}), 400
        raise APIException(f"No existe el id {user_id}", status_code=400)
    # print(single_user)
    # print(single_user.serialize())
    users_serialized = list(map(lambda x : x.serialize(), users))
    # print(users_serialized)
    # print(users)
    response_body = {
        "msg": "Hello, this is your GET /user response ",
        "users": users_serialized,
        "user_id": user_id,
        "user_info": single_user.serialize()
    }

    return jsonify(response_body), 200

@app.route('/user', methods=['POST'])
def post_user():
    body = request.get_json(silent=True)
    if body is None:
        raise APIException("Debes enviar informacion en el body", status_code=400)
    if "email" not in body:
        raise APIException("Debes enviar el campo email", status_code=400)
    if "password" not in body:
        raise APIException("Debes enviar tu contraseña", status_code=400)
    new_user = User(email = body['email'], password = body['password'], is_active = True)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "Completado", "new_user_info": new_user.serialize()})


@app.route("/planets", methods=["GET"])
def get_planets():
    planets = Planet.query.all()
    planets_serialized = list(map(lambda x: x.serialize(), planets))
    return jsonify({"msg": 'Completed', "planets": planets_serialized})

@app.route("/planets", methods=['PUT'])
def modify_planet():
    body = request.get_json(silent=True)
    if body is None:
        raise APIException("Debes enviar informacion en el body", status_code=400)
    if "id" not in body:
        raise APIException("Debes enviar el id del planeta a modificar", status_code=400)
    if "name" not in body:
        raise APIException("Debes enviar el nuevo nombre del planeta", status_code=400)
    single_planet = Planet.query.get(body['id'])
    single_planet.name = body['name']
    db.session.commit()
    return jsonify({"msg": "Completed"})

@app.route("/planets/<int:planet_id>", methods=['DELETE'])
def delete_planet(planet_id):
    single_planet = Planet.query.get(planet_id)
    if single_planet is None:
        raise APIException("El planeta no existe", status_code=400)
    db.session.delete(single_planet)
    db.session.commit()

    return jsonify({"msg": "Completed"})

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
