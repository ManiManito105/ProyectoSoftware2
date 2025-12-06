import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/sistema_inventario')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'clave-secreta-muy-segura-para-jwt')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Configuración general
    DEBUG = os.getenv('DEBUG', False)