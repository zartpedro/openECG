import os
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Configuração da aplicação Flask
app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql://user:password@db:3306/openECG')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo da Imagem
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(50), nullable=False)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=False)
    interpretation = db.Column(db.Text, nullable=True)

# Função para enviar a imagem ao GPT Assistant
def send_to_gpt_assistant(image_data, image_filename):
    # Inicializando o cliente OpenAI
    #client = OpenAI(api_key=os.getenv("GPT_API_KEY", "chave API aqui"))
    #assistant_id = os.getenv("GPT_ASSISTANT_ID", "chave Assistant")

    # Criar o arquivo no servidor da OpenAI
    file = client.files.create(
        file=open(image_filename, "rb"),  # Modifique conforme necessário para enviar o caminho correto do arquivo
        purpose="assistants"
    )

    # Criar uma nova thread
    thread = client.beta.threads.create()

    # Enviar a mensagem para a thread com o exame ECG
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=[
            {
                "type": "image_file",
                "image_file": {
                    "file_id": file.id
                }
            },
            {
                "type": "text",
                "text": "Você pode interpretar esse exame ECG para mim?"
            }
        ]
    )

    # Executar o processamento pelo assistente
    run = client.beta.threads.runs.create(  
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Obter a resposta do assistente
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Verificar e retornar a interpretação
    for message in reversed(messages.data):
        if message.content[0].type == "text":
            return message.content[0].text.value
    return None

# Rota para processar a imagem
@app.route('/interpret', methods=['POST'])
def process_image():
    data = request.get_json()
    image_id = data.get('image_id')

    img = Image.query.get(image_id)
    if not img:
        return jsonify({'error': 'Image not found'}), 404

    # Salvar a imagem para enviar ao GPT
    image_filename = f"/app/uploads/{img.filename}"
    with open(image_filename, "wb") as f:
        f.write(img.data)

    # Enviar a imagem para o GPT Assistant
    interpretation = send_to_gpt_assistant(img.data, image_filename)
    
    if interpretation:
        img.interpretation = interpretation
        db.session.commit()
        return jsonify({'message': 'Interpretation complete', 'interpretation': interpretation}), 200
    else:
        return jsonify({'error': 'Failed to interpret image'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(host='0.0.0.0', port=5003)  # Porta 5003 conforme configurado no docker-compose
