# Guía de Despliegue en GitHub

## Sistema de Monitoreo de Sensores de Humedad Agrícola con Blockchain

Esta guía te ayudará a subir la nueva versión del proyecto a GitHub paso a paso.

---

## Tabla de Contenidos

1. [Preparación del Proyecto](#1-preparación-del-proyecto)
2. [Configuración de Git](#2-configuración-de-git)
3. [Limpieza de Archivos](#3-limpieza-de-archivos)
4. [Commit de Cambios](#4-commit-de-cambios)
5. [Subida a GitHub](#5-subida-a-github)
6. [Verificación](#6-verificación)

---

## 1. Preparación del Proyecto

### Arquitectura Actual

```
sistema-sensores-humedad-agricola/
├── api/                          # API REST con FastAPI
│   ├── main.py                   # Servidor principal + Dashboard endpoint
│   ├── routers/
│   │   ├── sensors.py           # Endpoints de sensores
│   │   └── readings.py          # Endpoints de lecturas
│   ├── services/
│   │   └── blockchain_service.py # Servicio de blockchain
│   ├── models/
│   │   ├── sensor.py            # Modelos Pydantic
│   │   └── reading.py
│   └── schemas/
│       └── response.py
├── contracts/                    # Smart Contracts OpShin
│   └── opshin/
│       ├── humidity_sensor.py   # Contrato principal
│       └── build/               # Contrato compilado
├── database/                     # PostgreSQL
│   ├── schema.sql               # Esquema de base de datos
│   └── db_manager.py            # Gestor de conexiones
├── frontend/                     # Dashboard Web
│   └── dashboard/
│       └── index.html           # Dashboard interactivo con 3 pestañas
├── pycardano-client/            # Cliente blockchain
│   ├── config.py                # Configuración de red
│   ├── tx_builder.py            # Constructor de transacciones
│   ├── models.py                # Modelos de datos
│   └── utils.py                 # Utilidades
├── scripts/                      # Scripts de utilidad
│   └── test_api.py              # Tests de API
└── README.md                     # Documentación principal
```

### Características Implementadas

✅ **Backend:**
- API REST con FastAPI
- Persistencia dual: Blockchain (Cardano) + PostgreSQL
- 4 endpoints principales (GET/POST sensors, GET/POST readings)
- Servicio de blockchain con PyCardano
- Deduplicación automática de sensores

✅ **Frontend:**
- Dashboard interactivo con Bootstrap 5
- 3 pestañas: Sensores, Lecturas por Sensor, Registrar Sensor
- Gráficos con Chart.js (humedad y temperatura)
- Tabla detallada con fecha de instalación
- Filtro de lecturas por sensor

✅ **Blockchain:**
- Smart contract en OpShin (Plutus V2)
- Transacciones en Cardano Preview Testnet
- Datum con lista de sensores y lecturas
- Validaciones on-chain

✅ **Base de Datos:**
- PostgreSQL con esquema completo
- Tablas: sensors_history, readings_history
- Índices optimizados
- Triggers y funciones PL/pgSQL

---

## 2. Configuración de Git

### Verificar Estado Actual

```bash
cd c:\Proyectos\WINDOWS\PYTHON\sistema-sensores-humedad-agricola
git status
```

### Configurar Usuario (si no está configurado)

```bash
git config user.name "Tu Nombre"
git config user.email "tu-email@example.com"
```

### Verificar Rama Actual

```bash
git branch
```

Deberías estar en `main`. Si no, cámbiate:

```bash
git checkout main
```

---

## 3. Limpieza de Archivos

### Archivos a NO Subir (ya están en .gitignore)

- `.env` - Contiene claves privadas y seed phrases
- `__pycache__/` - Archivos Python compilados
- `.venv/` o `venv/` - Entorno virtual
- `.DS_Store` - Archivos de sistema macOS
- `*.pyc`, `*.pyo` - Archivos compilados
- `node_modules/` - Dependencias Node (si las hay)
- `.claude/` - Configuración local de Claude Code

### Archivos Temporales a Eliminar (Documentación Redundante)

Los siguientes archivos .md fueron creados durante el desarrollo y contienen información redundante. **Se recomienda eliminarlos antes del commit:**

```bash
# Archivos de documentación temporal del proceso de desarrollo
API_EJEMPLOS.md
API_REST_COMPLETADA.md
DECODE_DATUM_ENHANCED.md
DEDUPLICACION_SENSORES_COMPLETADA.md
DISENO_OPTIMIZADO.md
ESTADO_ACTUAL.md
EXITO_ADD_READING.md
EXITO_DEACTIVATE_SENSOR.md
EXITO_INICIALIZACION.md
EXITO_REGISTRO_SENSORES.md
EXITO_UPDATE_SENSOR.md
FRONTEND_DASHBOARD_COMPLETADO.md
GUIA_DEMO.md
GUIA_IMPLEMENTACION_OPTIMIZADA.md
IMPLEMENTACION_COMPLETA_CODIGO.md
INSTRUCCIONES_USO.md
INTEGRACION_POSTGRESQL_COMPLETA.md
INVESTIGACION_PYCARDANO_TX.md
LIMPIEZA_COMPLETADA.md
LUCID_VS_LUCID_EVOLUTION.md
MEJORAS_DECODE_DATUM.md
MIGRACION_OPSHIN.md
MVP_OPCION_B_RESUMEN.md
PASOS_INSTALACION_POSTGRES.md
PASOS_SIGUIENTES.md
PREVENCION_DUPLICADOS_SENSOR_ID.md
PROGRESO_REGISTER_SENSOR.md
QUICK_START.md
RESUMEN_BASE_DATOS_COMPLETA.md
RESUMEN_CRUD_COMPLETADO.md
RESUMEN_FINAL_API_REST.md
RESUMEN_FINAL_CRUD_100.md
RESUMEN_FINAL_MVP.md
RESUMEN_IMPLEMENTACION.md
RESUMEN_MEJORAS_DECODE.md
RESUMEN_SESION.md
RESUMEN_SESION_2025-10-14.md
RESUMEN_SESION_ACTUAL.md
RUTA_PRACTICA_MVP.md
TROUBLESHOOTING.md
TXHASH_DISPLAY_AGREGADO.md
TXHASH_EN_HISTORIAL_COMPLETADO.md
UBICACION_PROYECTO.md

# Scripts de análisis temporal
analyze_datum_content.py
cleanup_datum.py
cleanup_datum_pycardano.py
cleanup_datum_simple.py
debug_sensor_004.py

# Archivos de Aiken (proyecto original migrado a OpShin)
aiken.toml
contract-compiled.json.json
lib/agricultural/sensor_types.ak
validators/humidity_sensor.ak
tests/sensor_validation_tests.ak
humidity-sensor/plutus.json
plutus.json
payment.vkey
docs/  # Directorio completo de documentación Aiken
Flujo.png
Flujo1.png
```

**Comando para eliminar archivos temporales:**

```bash
# Eliminar documentación temporal
rm -f API_EJEMPLOS.md API_REST_COMPLETADA.md DECODE_DATUM_ENHANCED.md
rm -f DEDUPLICACION_SENSORES_COMPLETADA.md DISENO_OPTIMIZADO.md ESTADO_ACTUAL.md
rm -f EXITO_*.md FRONTEND_DASHBOARD_COMPLETADO.md GUIA_*.md
rm -f IMPLEMENTACION_COMPLETA_CODIGO.md INSTRUCCIONES_USO.md
rm -f INTEGRACION_POSTGRESQL_COMPLETA.md INVESTIGACION_PYCARDANO_TX.md
rm -f LIMPIEZA_COMPLETADA.md LUCID_VS_LUCID_EVOLUTION.md MEJORAS_DECODE_DATUM.md
rm -f MIGRACION_OPSHIN.md MVP_OPCION_B_RESUMEN.md PASOS_*.md
rm -f PREVENCION_DUPLICADOS_SENSOR_ID.md PROGRESO_REGISTER_SENSOR.md
rm -f QUICK_START.md RESUMEN_*.md RUTA_PRACTICA_MVP.md
rm -f TROUBLESHOOTING.md TXHASH_*.md UBICACION_PROYECTO.md

# Eliminar scripts de análisis temporal
rm -f analyze_datum_content.py cleanup_datum*.py debug_sensor_004.py

# Eliminar archivos Aiken antiguos
rm -f aiken.toml contract-compiled.json.json payment.vkey plutus.json
rm -f Flujo.png Flujo1.png
rm -rf lib/ validators/ tests/ humidity-sensor/ docs/
```

### Archivos Importantes a CONSERVAR

```
README.md                      # Documentación principal
DEPLOY_GITHUB.md              # Esta guía
.gitignore                    # Exclusiones de git
.env.example                  # Plantilla de variables de entorno (sin claves reales)
```

---

## 4. Commit de Cambios

### Ver Archivos Modificados

```bash
git status
```

### Agregar Archivos al Staging

**Opción A: Agregar todo (recomendado después de limpiar)**

```bash
git add .
```

**Opción B: Agregar selectivamente**

```bash
# Agregar API
git add api/

# Agregar Contratos
git add contracts/

# Agregar Base de Datos
git add database/

# Agregar Frontend
git add frontend/

# Agregar Cliente PyCardano
git add pycardano-client/

# Agregar Scripts
git add scripts/

# Agregar Documentación
git add README.md DEPLOY_GITHUB.md

# Agregar configuración
git add .gitignore .env.example requirements.txt
```

### Revisar Archivos Staged

```bash
git status
```

Deberías ver algo como:

```
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   .gitignore
        new file:   DEPLOY_GITHUB.md
        modified:   README.md
        new file:   api/main.py
        new file:   api/routers/sensors.py
        new file:   api/routers/readings.py
        new file:   api/services/blockchain_service.py
        new file:   frontend/dashboard/index.html
        ...
```

### Crear Commit

```bash
git commit -m "feat: Sistema completo de sensores con API REST + Dashboard + Blockchain

- Implementado API REST con FastAPI (endpoints sensors y readings)
- Agregado dashboard interactivo con 3 pestañas (Bootstrap 5 + Chart.js)
- Integración dual: Blockchain Cardano + PostgreSQL
- Smart contract en OpShin (Plutus V2) con validaciones
- Cliente PyCardano para transacciones
- Sistema de deduplicación de sensores
- Tabla detallada con fecha de instalación
- Filtro de lecturas por sensor
- Gráficos de humedad y temperatura

Funcionalidades:
✅ Registro de sensores on-chain
✅ Adición de lecturas de humedad/temperatura
✅ Consulta de sensores y lecturas vía API
✅ Visualización interactiva en dashboard
✅ Persistencia dual (blockchain + base de datos)

Tech Stack: FastAPI, PyCardano, OpShin, PostgreSQL, Bootstrap 5, Chart.js"
```

---

## 5. Subida a GitHub

### Verificar Repositorio Remoto

```bash
git remote -v
```

Deberías ver:

```
origin  https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola.git (fetch)
origin  https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola.git (push)
```

### Si NO tienes repositorio remoto configurado

**Opción A: Repositorio ya existe en GitHub**

```bash
git remote add origin https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola.git
```

**Opción B: Crear nuevo repositorio**

1. Ve a GitHub: https://github.com/new
2. Nombre: `sistema-sensores-humedad-agricola`
3. Descripción: `Sistema de monitoreo de sensores de humedad agrícola con blockchain Cardano`
4. Público/Privado: según prefieras
5. NO inicialices con README (ya tienes uno)
6. Click "Create repository"

Luego:

```bash
git remote add origin https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola.git
git branch -M main
```

### Push a GitHub

```bash
git push -u origin main
```

Si te pide autenticación:
- **Usuario**: Tu username de GitHub
- **Contraseña**: Personal Access Token (NO tu password de GitHub)

**Cómo crear un Personal Access Token:**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Nombre: `sistema-sensores-token`
4. Scopes: Marcar `repo` (acceso completo a repositorios)
5. Generate token
6. COPIAR el token (no podrás verlo después)
7. Usar ese token como contraseña en git push

### Si usas SSH en lugar de HTTPS

```bash
git remote set-url origin git@github.com:TU-USUARIO/sistema-sensores-humedad-agricola.git
git push -u origin main
```

---

## 6. Verificación

### Verificar Push Exitoso

```bash
git log --oneline -5
```

Deberías ver tu commit más reciente.

### Verificar en GitHub

1. Ve a: `https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola`
2. Verifica que todos los archivos estén presentes
3. Revisa que el README.md se vea correctamente
4. Comprueba que NO se hayan subido archivos sensibles (.env, __pycache__, etc.)

### Estructura Final en GitHub

```
sistema-sensores-humedad-agricola/
├── .gitignore
├── README.md
├── DEPLOY_GITHUB.md
├── requirements.txt
├── .env.example
├── api/
├── contracts/
├── database/
├── frontend/
├── pycardano-client/
└── scripts/
```

---

## Comandos Completos - Resumen Ejecutivo

```bash
# 1. Limpiar archivos temporales
rm -f API_*.md EXITO_*.md RESUMEN_*.md GUIA_*.md
rm -f cleanup_datum*.py analyze_datum_content.py debug_sensor_004.py
rm -f aiken.toml plutus.json Flujo.png Flujo1.png
rm -rf lib/ validators/ tests/ humidity-sensor/ docs/

# 2. Verificar estado
git status

# 3. Agregar archivos
git add .

# 4. Crear commit
git commit -m "feat: Sistema completo de sensores con API REST + Dashboard + Blockchain

- Implementado API REST con FastAPI
- Dashboard interactivo con 3 pestañas
- Integración Blockchain Cardano + PostgreSQL
- Smart contract OpShin + Cliente PyCardano"

# 5. Push a GitHub
git push -u origin main
```

---

## Solución de Problemas

### Error: "failed to push some refs"

```bash
# Alguien hizo cambios en GitHub que no tienes localmente
git pull --rebase origin main
git push -u origin main
```

### Error: "remote: Permission denied"

- Verifica tu Personal Access Token
- Asegúrate de tener permisos de escritura en el repositorio

### Error: "Updates were rejected because the tip of your current branch is behind"

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Archivos Sensibles Accidentalmente Commiteados

```bash
# NUNCA hagas esto si ya hiciste push (otros pueden haber descargado)
git rm --cached .env
git commit -m "fix: Remover archivo .env sensible"
git push

# Si ya hiciste push y contiene claves privadas:
# 1. ROTAR todas las claves inmediatamente
# 2. Crear nuevo wallet
# 3. Considerar usar git-filter-repo o BFG Repo-Cleaner para limpiar historial
```

---

## Siguientes Pasos Después de Subir

1. **Actualizar README.md en GitHub** con badges:
   - ![Python](https://img.shields.io/badge/python-3.11-blue)
   - ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
   - ![Cardano](https://img.shields.io/badge/Cardano-Preview-orange)

2. **Crear Releases:**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0: MVP Completo"
   git push origin v1.0.0
   ```

3. **Agregar GitHub Actions** (opcional):
   - CI/CD para tests automáticos
   - Linting con flake8/black
   - Deploy automático

4. **Documentación adicional:**
   - Wiki en GitHub con guías detalladas
   - GitHub Pages para documentación del API
   - Diagramas de arquitectura (usar Mermaid en README.md)

---

## Recursos Adicionales

- **GitHub Docs**: https://docs.github.com/
- **Git Cheat Sheet**: https://training.github.com/downloads/github-git-cheat-sheet/
- **Personal Access Tokens**: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- **Markdown Guide**: https://www.markdownguide.org/

---

## Notas Finales

- **NUNCA** subas archivos `.env` con claves privadas o seed phrases
- **SIEMPRE** usa `.gitignore` para excluir archivos sensibles
- **REVISA** el contenido antes de hacer push
- **DOCUMENTA** tus cambios en commits descriptivos
- **MANTÉN** actualizado el README.md

---

Creado: 21 de Octubre 2025
Versión: 1.0.0
