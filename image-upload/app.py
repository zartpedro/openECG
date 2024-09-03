import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import jwt_required, get_jwt_identity

app = Flask(__name__)

# Configuração do banco de dados
DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'userpassword')
DB_NAME = os.getenv('DB_NAME', 'openECG')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o SQLAlchemy
db = SQLAlchemy(app)

# Modelo para Imagem
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)  # Armazena a imagem binária
    mimetype = db.Column(db.String(50), nullable=False)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=False)

# Garantir que a pasta de upload exista (não necessário se armazenar diretamente no BD)
os.makedirs('/uploads', exist_ok=True)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Starting upload...")
    if 'file' not in request.files:
        print("No file part")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        mimetype = file.mimetype
        if not mimetype:
            print("File type not allowed")
            return jsonify({'error': 'File type not allowed'}), 400
        try:
            print("Saving file to database...")
            img = Image(filename=filename, data=file.read(), mimetype=mimetype)
            db.session.add(img)
            db.session.commit()
            print("File saved successfully")
            return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 201
        except Exception as e:
            print("Error:", e)
            return jsonify({'error': str(e)}), 500
    else:
        print("File type not allowed")
        return jsonify({'error': 'File type not allowed'}), 400


@app.route('/uploads/<int:image_id>', methods=['GET'])
def get_file(image_id):
    img = Image.query.get(image_id)
    if img:
        return app.response_class(img.data, mimetype=img.mimetype)
    return jsonify({'error': 'Image not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas do banco de dados
    app.run(host='0.0.0.0', port=5001)
