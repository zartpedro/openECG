# Use a imagem Python 3.9 slim como base
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copie o arquivo requirements.txt para o contêiner
COPY requirements.txt .

# Instala as dependências necessárias
RUN pip install --no-cache-dir -r requirements.txt

# Copie o conteúdo da pasta atual para o contêiner
COPY . .

# Exponha a porta 5003
EXPOSE 5003

# Comando para iniciar o app
CMD ["python", "app.py"]
