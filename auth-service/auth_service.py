from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
import pymysql
import config

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config['JWT_TOKEN_LOCATION'] = ['headers']
jwt = JWTManager(app)

def get_db_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        db=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE username=%s AND password_hash=%s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()

            if user:
                # Incluir user_id no 'sub' e username como claim adicional
                additional_claims = {"username": user["username"]}
                access_token = create_access_token(identity=user["id"], additional_claims=additional_claims)
                return jsonify(access_token=access_token, username=user['username']), 200
            else:
                return jsonify({"msg": "Bad username or password"}), 401
    finally:
        connection.close()

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    user_id = get_jwt_identity()  # Obtém o 'sub', que é o user_id
    jwt_claims = get_jwt()  # Obtém outras claims
    username = jwt_claims.get('username')
    return jsonify({"msg": f"You are accessing protected content, {username} (ID: {user_id})"}), 200

@app.route('/users', methods=['POST'])
def create_user():
    username = request.json.get('username')
    password = request.json.get('password')
    # role = request.json.get('role')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (username,  password_hash) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
            connection.commit()
            return jsonify({"msg": "User created successfully"}), 201
    except pymysql.MySQLError as e:
        return jsonify({"msg": str(e)}), 500
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
