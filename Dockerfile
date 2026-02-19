# 1. Imagen base oficial de Python
FROM python:3.10-slim

# 2. Crear directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar dependencias primero (mejor para caché)
COPY requirements.txt .

# 4. Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código
COPY . .

# 6. Comando por defecto al iniciar el bot
CMD ["python", "main.py"]
