-- Crear usuario y base de datos

CREATE USER sensor_app WITH PASSWORD 'change_this_password';
CREATE DATABASE sensor_system OWNER sensor_app;

-- Conectar a la base de datos
\c sensor_system

-- Ejecutar schema
\i database/schema.sql

-- Verificar tablas creadas
\dt

-- Otorgar permisos
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sensor_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sensor_app;
