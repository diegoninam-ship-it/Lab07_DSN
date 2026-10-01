# Lab07 — LOGIN + CRUD detrás de un balanceador de carga

Aplicación Flask de LOGIN + CRUD de `productos`, pensada para correr en varias
instancias detrás de un balanceador de carga (Nginx local o un Application
Load Balancer en AWS). La especificación completa del proyecto está en
[CONTEXT.md](CONTEXT.md).

La app es *stateless*: la sesión viaja en una cookie firmada (válida en
cualquier instancia que comparta `SECRET_KEY`) y todas las instancias leen y
escriben en la misma base PostgreSQL. Cada respuesta indica qué servidor la
atendió (cabecera `X-Servidor`, ruta `/whoami`, pie de página).

## Requisitos

- Python 3.14
- Docker (para PostgreSQL local)

## Instalación

1. Clonar el repositorio y crear el entorno virtual:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

   Si la activación falla por la política de ejecución de PowerShell:

   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process
   ```

2. Instalar las dependencias. Para desarrollar y correr las pruebas:

   ```powershell
   pip install -r requirements-dev.txt
   ```

   Para una instalación de solo ejecución (lo que usa la imagen Docker de la
   etapa 3):

   ```powershell
   pip install -r requirements.txt
   ```

3. Levantar PostgreSQL 18 en un contenedor local (puerto 5433, para no chocar
   con un PostgreSQL existente en el 5432):

   ```powershell
   docker run -d --name lab07-postgres -e POSTGRES_USER=lab07 -e POSTGRES_PASSWORD=lab07 -e POSTGRES_DB=lab07_dev -p 5433:5432 postgres:18-alpine
   docker exec lab07-postgres createdb -U lab07 lab07_test
   ```

4. Crear el archivo `.env` a partir de [.env.example](.env.example) y
   completar `SECRET_KEY` con un valor propio:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

   Los valores por defecto de `.env.example` ya apuntan a `lab07_dev` y
   `lab07_test` en `localhost:5433`, tal como los crea el paso anterior.

5. Aplicar la migración y crear el usuario de demostración:

   ```powershell
   flask db upgrade
   flask seed
   ```

   `flask seed` crea `demo@lab07.pe` / `Demo1234!` (nombre "Usuario Demo"),
   solo si no existe.

## Ejecución

Modo desarrollo:

```powershell
flask run
```

Con gunicorn (como en el contenedor Docker de la etapa 3):

```powershell
gunicorn wsgi:app
```

La app se controla por variables de entorno (ver sección 8 de
[CONTEXT.md](CONTEXT.md) para el detalle completo). Las más relevantes:

| Variable | Valores | Qué hace |
|---|---|---|
| `APP_MODE` | `web` (por defecto) o `api` | `web` sirve el login y el CRUD; `api` sirve únicamente `/api/*`, de solo lectura |
| `SERVER_ID` | texto ASCII | Identifica la instancia en `/whoami`, la cabecera `X-Servidor` y el pie de página |
| `LOAD_TEST` | `0` (por defecto) o `1` | Habilita `/carga`, usada para generar CPU en las pruebas de balanceo |
| `DETRAS_DE_PROXY` | `0` (por defecto) o `1` | Aplica `ProxyFix`; activar solo si hay un proxy delante (Nginx, ALB) |

## Pruebas

Las pruebas usan **siempre** `lab07_test`, nunca `lab07_dev`, y se niegan a
ejecutarse si `TEST_DATABASE_URL` apunta a Neon. Si ya la definiste en `.env`
(como en el paso de instalación), **no hace falta exportarla a mano**: basta
con

```powershell
pytest
```

`tests/conftest.py` busca `TEST_DATABASE_URL` primero en el entorno y, si no
está, solo esa clave en `.env` (sin tocar el resto del entorno del proceso).
Si quieres apuntar a otra base sin tocar `.env`, exporta la variable y gana
sobre lo que haya en el archivo:

```powershell
$env:TEST_DATABASE_URL = "postgresql://lab07:lab07@localhost:5433/lab07_test"
pytest
```

`pytest.ini` ya trae `--cov=app --cov-report=term-missing --cov-fail-under=90`
en `addopts`, así que basta con `pytest` a secas (no hace falta `python -m
pytest` ni repetir las opciones de cobertura a mano). El umbral del 90 % se
exige sobre la **suite completa**: si corres un solo archivo o una sola
prueba, agrega `--no-cov`, porque la cobertura de ese subconjunto no llega al
90 % y el comando terminaría en error aunque esa prueba haya pasado:

```powershell
pytest tests/unit/test_models.py --no-cov
```

Al inicio de la sesión de pruebas, `tests/conftest.py` deja el esquema de
`lab07_test` limpio y aplica la migración real (no `create_all`); entre
pruebas, trunca las tablas de datos.

## Estructura del proyecto

Ver la sección 5 de [CONTEXT.md](CONTEXT.md). En resumen: `app/` contiene la
aplicación (blueprints, modelos, formularios, plantillas), `migrations/` la
migración de base de datos, y `tests/` las pruebas unitarias y de
integración. La carpeta `infra/` (Docker, Nginx, scripts de AWS) es de la
etapa 3, manual, y no es responsabilidad del agente.

## Despliegue contra Neon (etapa 3, manual)

Pasos de aceptación que corresponden al usuario, no al agente (sección 9.8 de
CONTEXT.md):

1. Aplicar la migración a Neon: `USE_DIRECT_DB=1` + `flask db upgrade`, con
   las URLs de Neon.
2. `flask seed` contra Neon.
3. Levantar dos instancias locales apuntando a Neon (puertos distintos,
   mismo `SECRET_KEY`) y verificar que el login hecho en una se reconoce en
   la otra, y que un producto creado en una se puede editar desde la otra.
