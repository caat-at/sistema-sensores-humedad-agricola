# Pasos para Subir a GitHub - Ejecución Inmediata

## Resumen

Ya tienes preparados:
- DEPLOY_GITHUB.md (guía completa)
- README.md actualizado (nueva arquitectura completa)
- .gitignore mejorado (excluye archivos sensibles y temporales)
- .env.example (plantilla de configuración)

## Opción A: Subir Todo (Recomendado - Más Simple)

Esta opción sube todo el proyecto incluyendo algunos documentos de desarrollo que pueden ser útiles como historial.

```bash
# 1. Agregar todos los archivos nuevos y modificados
git add .

# 2. Ver qué se va a commitear
git status

# 3. Crear commit descriptivo
git commit -m "feat: Sistema completo de sensores con API REST + Dashboard + Blockchain

✨ Características principales:
- API REST con FastAPI (endpoints sensors y readings)
- Dashboard interactivo con 3 pestañas (Bootstrap 5 + Chart.js)
- Integración dual: Blockchain Cardano + PostgreSQL
- Smart contract OpShin (Plutus V2) con validaciones
- Cliente PyCardano para transacciones
- Sistema de deduplicación de sensores
- Tabla detallada con fecha de instalación
- Filtro de lecturas por sensor
- Gráficos de humedad y temperatura

📁 Estructura:
- api/ - API REST con FastAPI
- contracts/ - Smart contract OpShin
- database/ - Esquema PostgreSQL
- frontend/ - Dashboard web
- pycardano-client/ - Cliente blockchain
- scripts/ - Utilidades y tests

🔧 Tech Stack:
FastAPI, PyCardano, OpShin, PostgreSQL, Bootstrap 5, Chart.js

📚 Documentación completa en README.md y DEPLOY_GITHUB.md"

# 4. Verificar que el commit se creó correctamente
git log -1 --oneline

# 5. Subir a GitHub
git push -u origin main
```

## Opción B: Subir Solo Archivos Esenciales (Más Limpio)

Esta opción excluye documentos temporales de desarrollo y sube solo lo necesario.

```bash
# 1. Agregar archivos esenciales del proyecto
git add api/
git add contracts/
git add database/
git add frontend/
git add pycardano-client/
git add scripts/

# 2. Agregar documentación principal
git add README.md
git add DEPLOY_GITHUB.md
git add .gitignore
git add .env.example

# 3. Agregar solo algunos documentos útiles (opcional)
git add MIGRACION_OPSHIN.md        # Explica migración de Aiken a OpShin
git add INTEGRACION_POSTGRESQL_COMPLETA.md  # Setup de PostgreSQL

# 4. Remover archivos obsoletos de Aiken
git rm -r docs/
git rm -r lib/
git rm -r validators/
git rm -r tests/
git rm -r humidity-sensor/
git rm aiken.toml
git rm plutus.json
git rm contract-compiled.json.json
git rm payment.vkey
git rm Flujo.png
git rm Flujo1.png

# 5. Ver qué se va a commitear
git status

# 6. Crear commit
git commit -m "feat: Sistema completo de sensores con API REST + Dashboard + Blockchain

✨ Características principales:
- API REST con FastAPI (endpoints sensors y readings)
- Dashboard interactivo con 3 pestañas (Bootstrap 5 + Chart.js)
- Integración dual: Blockchain Cardano + PostgreSQL
- Smart contract OpShin (Plutus V2) con validaciones
- Cliente PyCardano para transacciones
- Sistema de deduplicación de sensores
- Tabla detallada con fecha de instalación
- Filtro de lecturas por sensor
- Gráficos de humedad y temperatura

📁 Estructura:
- api/ - API REST con FastAPI
- contracts/ - Smart contract OpShin
- database/ - Esquema PostgreSQL
- frontend/ - Dashboard web
- pycardano-client/ - Cliente blockchain
- scripts/ - Utilidades y tests

🔧 Tech Stack:
FastAPI, PyCardano, OpShin, PostgreSQL, Bootstrap 5, Chart.js

📚 Documentación completa en README.md y DEPLOY_GITHUB.md

🧹 Limpieza:
- Removidos archivos obsoletos de Aiken
- Removida documentación temporal de desarrollo
- .gitignore mejorado para seguridad"

# 7. Verificar commit
git log -1 --stat

# 8. Subir a GitHub
git push -u origin main
```

## ¿Cuál Opción Usar?

### Usa Opción A si:
- Es tu primer push y quieres tener historial completo
- Los documentos de desarrollo no te molestan
- Quieres poder consultar el proceso de desarrollo después
- Prefieres simplicidad

### Usa Opción B si:
- Quieres un repositorio limpio y profesional
- Los documentos temporales ocupan espacio innecesario
- Ya tienes toda la info en README.md y DEPLOY_GITHUB.md
- Planeas compartir el repo públicamente

## Mi Recomendación: Opción B

La Opción B es más profesional porque:
1. README.md ya tiene toda la información necesaria
2. DEPLOY_GITHUB.md tiene guía completa de deployment
3. Los archivos `RESUMEN_*.md`, `EXITO_*.md`, etc. son redundantes
4. El repositorio será más fácil de navegar
5. Menos "ruido" para otros desarrolladores

---

## Después del Push

### 1. Verificar en GitHub

Visita: `https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola`

Deberías ver:
- README.md renderizado con badges y secciones
- Estructura de carpetas clara
- .gitignore protegiendo archivos sensibles

### 2. Crear Release (Opcional)

```bash
# Crear tag para versión 1.0.0
git tag -a v1.0.0 -m "Release v1.0.0: MVP Completo

- Sistema funcional end-to-end
- API REST + Dashboard + Blockchain
- Persistencia dual (Cardano + PostgreSQL)
- 4 sensores activos en testnet
- Documentación completa"

# Subir tag a GitHub
git push origin v1.0.0
```

Luego en GitHub:
1. Ve a "Releases"
2. Click "Draft a new release"
3. Selecciona tag v1.0.0
4. Título: "v1.0.0 - MVP Completo"
5. Descripción: Copiar features del commit
6. Publish release

### 3. Actualizar README con Badges (Opcional)

En la descripción del repositorio en GitHub:
- Topics: `cardano`, `blockchain`, `iot`, `agriculture`, `fastapi`, `opshin`, `plutus`
- Website: URL de la documentación (si tienes)

---

## Verificación Final

Después del push, ejecuta:

```bash
# Ver log del último commit
git log -1 --stat

# Ver archivos en el repositorio
git ls-files

# Verificar que .env NO esté en el repo (debe estar vacío)
git ls-files | grep ".env$"
```

Si `.env` aparece en `git ls-files`, **DETENTE** y ejecuta:

```bash
git rm --cached .env
git commit -m "fix: Remover archivo .env del repositorio"
git push
```

Luego **ROTA inmediatamente** tu seed phrase y BlockFrost API key.

---

## Comandos de Emergencia

### Si cometiste un error en el commit

```bash
# Deshacer último commit (mantiene cambios)
git reset --soft HEAD~1

# Editar y volver a commitear
git add .
git commit -m "mensaje corregido"
git push -f origin main  # Solo si NO has compartido el repo
```

### Si subiste accidentalmente archivos sensibles

**NUNCA uses git reset si otros ya descargaron el repo**

1. Remover archivo del repo
```bash
git rm --cached archivo_sensible
git commit -m "fix: Remover archivo sensible"
git push
```

2. **ROTAR INMEDIATAMENTE** todas las credenciales:
   - Generar nueva seed phrase
   - Crear nuevo wallet
   - Regenerar BlockFrost API key
   - Cambiar contraseñas de base de datos

3. Considerar usar herramientas como:
   - `git-filter-repo` (para limpiar historial)
   - `BFG Repo-Cleaner` (más simple)

---

## Siguiente Paso Después de Subir

1. Compartir el repositorio
2. Documentar en LinkedIn/Twitter
3. Agregar al portfolio
4. Buscar colaboradores
5. Planear nuevas features (ver Roadmap en README.md)

---

Creado: 21 de Octubre 2025
Versión: 1.0.0
