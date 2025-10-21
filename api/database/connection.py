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

# DATABASE_URL desde variable de entorno o default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sensor_app:change_this_password@localhost:5432/sensor_system"
)

# Crear engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexión antes de usar
    echo=False  # Set True para debug SQL
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
