# -*- coding: utf-8 -*-
"""
Conexión a PostgreSQL
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# DATABASE_URL desde variable de entorno o construir desde componentes
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Construir desde componentes individuales
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "sensor_system")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "carlos1981")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Agregar SSL para conexiones cloud si es necesario
if "supabase.co" in DATABASE_URL or "neon.tech" in DATABASE_URL:
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

# Crear engine con configuración optimizada para cloud
engine = create_engine(
    DATABASE_URL,
    pool_size=5,              # Número de conexiones en el pool
    max_overflow=10,          # Conexiones adicionales permitidas
    pool_pre_ping=True,       # Verifica conexión antes de usar
    pool_recycle=3600,        # Reciclar conexiones cada hora
    echo=False                # Set True para debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """
    Dependency para FastAPI
    Yield una sesión de DB que se cierra automáticamente
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Inicializar tablas (solo si no existen)
    """
    Base.metadata.create_all(bind=engine)
    print("[OK] Base de datos inicializada")

def test_connection():
    """
    Probar conexión a PostgreSQL
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("[OK] Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a PostgreSQL: {e}")
        return False
