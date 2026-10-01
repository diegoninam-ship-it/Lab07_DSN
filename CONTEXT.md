# CONTEXT.md — Lab07: App LOGIN + CRUD detrás de un balanceador de carga

> ## Instrucciones para el agente (léelas antes que nada)
>
> 1. Este archivo es la **especificación completa y la fuente de verdad** del proyecto. Léelo entero antes de cualquier tarea y vuelve a él cuando pierdas contexto.
> 2. Tu alcance es **solo la etapa 2 (Desarrollo)**: código de la app, pruebas, `README.md`, `.env.example` y la actualización de este archivo. Las reglas completas están en la **sección 10**.
> 3. **Prohibido** crear o modificar cualquier cosa dentro de `infra/`, conectarte a Neon o ejecutar operaciones destructivas fuera de las bases locales `lab07_dev` y `lab07_test`.
> 4. Trabaja por **fases (F1–F9)**. Al terminar cada una: pruebas, commit, push, reporte, y **espera la confirmación del usuario** antes de seguir.
> 5. Si la especificación es ambigua, o crees que una decisión debería cambiar, **detente y pregunta**. Puedes proponer cambios; no aplicarlos sin aprobación.
> 6. Al cerrar cada fase, actualiza la **sección 3 (Estado actual)** y agrega una entrada en la **sección 14 (Changelog)**. No modifiques las secciones de decisiones sin aprobación explícita.

---

## 1. Resumen

| Campo | Valor |
|---|---|
| Laboratorio | GLAB-S07 — curso *Desarrollo de Soluciones en la Nube*, Tecsup |
| Requerimiento | Aplicación **LOGIN + CRUD** servida detrás de un **balanceador de carga**, en dos topologías: local (Nginx + 3 backends) y AWS (Application Load Balancer + EC2 en 2 zonas) |
| Alcance del laboratorio | Parte A + Parte B + los 5 ejercicios de la guía `Laboratorio_Balanceador_de_Carga.md` |
| Entidad del CRUD | `productos` |
| Repositorio | https://github.com/diegoninam-ship-it/Lab07_DSN.git (público, rama `main`) |
| Autor | Diego Nina |

### Principios que guían todo el diseño

- **La app es *stateless*.** Ningún dato de sesión vive en la memoria de un servidor: la sesión viaja en una cookie firmada, válida en cualquier instancia que comparta `SECRET_KEY`.
- **El estado es compartido.** Todas las instancias leen y escriben en la misma base PostgreSQL.
- **El balanceo es visible.** Cada respuesta revela qué servidor la atendió (pie de página, cabecera `X-Servidor`, `/whoami`), y cada producto registra qué servidor lo creó y cuál lo editó por última vez.
- **La app es contenerizable.** Configuración solo por variables de entorno, logs a la salida estándar, nada escrito en disco, arranque con gunicorn.

---

## 2. Etapas y responsables

| # | Etapa | Responsable | Estado |
|---|---|---|---|
| 1 | Planificación | Usuario + asistente | ✅ Cerrada |
| 2 | Desarrollo (código y pruebas) | **Agente de IA**, guiado por este archivo | ✅ Cerrada |
| 3 | Infraestructura y balanceo de carga (Docker, Nginx, AWS) | **Usuario, de forma manual** | ⏳ Pendiente |

La etapa 3 se hace a mano con fines de aprendizaje DevOps. La sección 11 es solo una **referencia** para esa etapa y está **fuera del alcance del agente**.

---

## 3. Estado actual

**Última actualización:** 2026-09-30

- **Etapa 2 (Desarrollo) cerrada.** Las fases F1–F9 están completas; el agente entrega el código, las pruebas, el `README.md` y el `.env.example`. Sigue la **etapa 3 (Infraestructura y balanceo de carga)**, manual, a cargo del usuario (sección 11).
- Planificación cerrada (segunda iteración): estructura, stack, modelo, contrato, configuración, pruebas, infraestructura de referencia y reglas del agente.
- El repositorio ya no contiene código del intento anterior (estructura plana, sin pruebas): todo fue reestructurado fase a fase según esta especificación.
- **F1 cerrada:** entorno local listo (ver changelog).
- **F2 cerrada:** `config.py`, `extensions.py`, `create_app()`, `wsgi.py` y rutas públicas (`/health`, `/whoami`, `/carga`) reescritos según esta especificación (ver changelog).
- **F3 cerrada:** modelos `Usuario` y `Producto`, migración inicial única y `flask seed` (ver changelog).
- **F4 cerrada:** autenticación (`/login`, `/logout`, `login_required`, `usuario_de_sesion`) (ver changelog).
- **F5 cerrada:** CRUD web de productos (ver changelog).
- **F6 cerrada:** API de solo lectura (ver changelog).
- **F7 cerrada:** cabecera `X-Servidor`, páginas de error propias, CSS externo y pie de página (ver changelog).
- **F8 cerrada:** bloque multi-instancia, migración sincronizada y cobertura 99.70 % — criterio de "terminado" del agente (9.7) cumplido (ver changelog).
- **F9 cerrada:** `README.md`, `.env.example` y cierre de este archivo (ver changelog). **Esta es la última fase del agente.**

### Prerrequisitos antes de lanzar el agente

| # | Prerrequisito | Estado |
|---|---|---|
| 1 | Reiniciar la base de Neon (`DROP TABLE IF EXISTS productos, usuarios, alembic_version CASCADE;`) | ✅ Hecho (2026-09-30) |
| 2 | Docker Desktop encendido | ✅ Hecho (2026-09-30) |
| 3 | Este `CONTEXT.md` en la raíz del repo, con commit y push | ✅ Hecho (2026-09-30) |

**Siguiente paso:** ninguno para el agente. El trabajo de la etapa 2 está completo; sigue la etapa 3 (infraestructura y balanceo de carga), manual, a cargo del usuario — ver la sección 9.8 (aceptación manual contra Neon) y la sección 11 (referencia de infraestructura).

---

## 4. Stack y versiones

| Componente | Paquete | Versión |
|---|---|---|
| Lenguaje | Python | **3.14** (máquina del usuario: 3.14.7) |
| Framework | Flask (incluye Werkzeug 3.1.9) | 3.1.3 |
| ORM | SQLAlchemy / Flask-SQLAlchemy | 2.1.1 / 3.1.1 |
| Migraciones | Flask-Migrate (Alembic 1.20.0) | 4.1.0 |
| Formularios y CSRF | Flask-WTF (WTForms 3.2.2) | 1.3.0 |
| Driver PostgreSQL | `psycopg[binary]` | 3.3.6 |
| Servidor WSGI | gunicorn | 26.2.0 |
| Variables de entorno | python-dotenv | 1.2.3 |
| Pruebas | pytest / pytest-cov | 9.1.1 / 7.1.0 |
| Base de datos | PostgreSQL | **18** (Neon en producción; `postgres:18-alpine` en local) |

Verificado el 2026-09-30: `psycopg-binary` y `SQLAlchemy` publican paquetes precompilados para Python 3.14 en Windows, Linux glibc y Linux musl.

### Reglas del stack

- **Versiones fijadas con `==`.** `requirements.txt` contiene las dependencias de ejecución **y sus dependencias indirectas**, generado con `pip freeze` desde un entorno limpio que solo tenga las dependencias de ejecución.
- `requirements-dev.txt` empieza con `-r requirements.txt` y agrega solo `pytest` y `pytest-cov` fijados.
- **No agregar dependencias** fuera de esta tabla sin aprobación.
- **Contraseñas con `werkzeug.security`**. No usar `passlib` ni `bcrypt`.
- **No usar el validador `Email()`** de WTForms (exige `email-validator`, no incluido).

---

## 5. Estructura del repositorio

```
Lab07_DSN/
├── CONTEXT.md
├── README.md
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt            # ejecución (va a la imagen Docker)
├── requirements-dev.txt        # pruebas (NO va a la imagen)
├── wsgi.py                     # load_dotenv() + app = create_app()  → gunicorn wsgi:app
├── app/
│   ├── __init__.py             # create_app(config_overrides=None)
│   ├── config.py               # construcción y validación de la configuración
│   ├── extensions.py           # db, migrate, csrf
│   ├── models.py               # Usuario, Producto
│   ├── forms.py                # LoginForm, ProductoForm
│   ├── cli.py                  # flask seed
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── publico.py          # /health, /whoami, /carga
│   │   ├── auth.py             # /login, /logout, login_required, usuario_de_sesion
│   │   ├── productos.py        # CRUD web
│   │   └── api.py              # /api/*
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── errores/            # 400.html (CSRF), 404.html, 500.html
│   │   └── productos/          # lista.html, form.html
│   └── static/
│       └── css/app.css
├── migrations/                 # UNA sola migración inicial, generada por el agente
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
└── infra/                      # ⛔ RESERVADA — etapa 3, manual. El agente NO la crea ni la modifica
    ├── docker/                 # Dockerfile y Dockerfile.dockerignore
    ├── compose/                # docker-compose de la Parte A
    ├── nginx/                  # balanceador.conf
    └── aws/                    # scripts de User Data y notas
```

- Todo lo que está **fuera** de `infra/` es del agente; todo lo de **dentro** es del usuario.
- El `Dockerfile` se construirá con la raíz como contexto: `docker build -f infra/docker/Dockerfile .` (BuildKit lee `Dockerfile.dockerignore` junto al `Dockerfile`).
- `.gitignore` debe incluir: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `instance/`, `.pytest_cache/`, `.coverage`, `htmlcov/`.

---

## 6. Modelo de datos

### `usuarios`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | Integer | PK |
| `nombre` | String(100) | no nulo |
| `correo` | String(120) | no nulo, único, indexado. **Se guarda siempre en minúsculas y sin espacios** |
| `password_hash` | String(255) | no nulo (`generate_password_hash`) |
| `creado_en` | DateTime(timezone=True) | `server_default=now()` |

Métodos: `set_password(password)` y `check_password(password)`. El hash nunca se manipula fuera de ellos.

### `productos`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | Integer | PK |
| `nombre` | String(120) | no nulo · `CHECK (length(trim(nombre)) > 0)` → `ck_productos_nombre_no_vacio` |
| `precio` | Numeric(10, 2) | no nulo · `CHECK (precio >= 0)` → `ck_productos_precio_no_negativo` |
| `stock` | Integer | no nulo, por defecto 0 · `CHECK (stock >= 0)` → `ck_productos_stock_no_negativo` |
| `servidor_origen` | String(100) | no nulo. `SERVER_ID` que **creó** el registro. **Nunca cambia** |
| `servidor_actualizacion` | String(100) | nulo. `SERVER_ID` de la **última edición** |
| `creado_en` | DateTime(timezone=True) | `server_default=now()` |
| `actualizado_en` | DateTime(timezone=True) | `server_default=now()`, `onupdate=now()` |

- Las fechas las asigna PostgreSQL, no Python (evita desfases entre relojes de distintas instancias).
- `to_dict()` de `Producto` devuelve el esquema JSON de la sección 7.4.

### Migraciones

- El agente **borra** la carpeta `migrations/` del intento anterior y genera **una única migración inicial** que incluya las tres `CheckConstraint` con los nombres de la tabla anterior.
- La migración se genera contra `lab07_dev` (local), **nunca contra Neon**.
- Ningún contenedor ni instancia ejecuta migraciones al arrancar.

### Usuario semilla

`flask seed` crea `demo@lab07.pe` / `Demo1234!` (nombre "Usuario Demo") **solo si no existe**. Es idempotente y **no borra nada**.

---

## 7. Rutas y contrato

### 7.1 Rutas públicas (en ambos modos)

| Método y ruta | Respuesta | Notas |
|---|---|---|
| `GET /health` | `200`, texto `ok` | **No consulta la base.** Debe responder aunque la base sea inalcanzable |
| `GET /whoami` | `200`, `text/plain; charset=utf-8`, cuerpo = `SERVER_ID` | Para los `curl` de los ejercicios |
| `GET /carga` | `200`, texto `carga completada en <SERVER_ID>` si `LOAD_TEST=1`; si no, `404` | `CARGA_ITERACIONES` rondas de `hashlib.sha256` encadenado. No toca la base |

### 7.2 Modo `web` (`APP_MODE=web`)

| Método y ruta | Acceso | Comportamiento | Códigos |
|---|---|---|---|
| `GET /login` | Público | Formulario. Con sesión activa, redirige a `/` | 200, 302 |
| `POST /login` | Público + CSRF | Éxito: `session.clear()`, guarda **solo** `session["usuario_id"]`, redirige a `next` (solo si es seguro) o a `/`. Fallo: mismo formulario, mensaje único "Correo o contraseña incorrectos." | 302, 200, 400 |
| `POST /logout` | CSRF | `session.clear()` y redirige a `/login`. `GET` no permitido | 302, 400, 405 |
| `GET /` | Sesión | Lista de productos, `id` descendente | 200 |
| `GET/POST /productos/nuevo` | Sesión + CSRF | Crea con `servidor_origen = SERVER_ID`. Flash: "Producto creado (atendido por <SERVER_ID>)." | 200, 302, 400 |
| `GET/POST /productos/<id>/editar` | Sesión + CSRF | Precarga valores. Al guardar: `servidor_actualizacion = SERVER_ID`; **no toca** `servidor_origen`. Flash: "Producto actualizado." | 200, 302, 400, 404 |
| `POST /productos/<id>/eliminar` | Sesión + CSRF | Borra y redirige a `/`. Flash: "Producto eliminado." `GET` no permitido | 302, 400, 404, 405 |

- Sin sesión, toda ruta protegida responde `302` a `/login?next=<ruta>`.
- `<id>` usa el conversor `int(max=2147483647)`: un id mayor responde `404` sin llegar a la base.
- **`next` seguro:** solo rutas que empiecen con `/`, que no empiecen con `//` y que no contengan `\`.
- **Usuario inexistente:** si la cookie apunta a un `usuario_id` que ya no existe, se limpia la sesión y se trata como no autenticado.
- El login normaliza el correo (`strip().lower()`) antes de buscar.
- El formulario de eliminar usa un `confirm()` con **texto fijo**, nunca con el nombre del producto.

### 7.3 Modo `api` (`APP_MODE=api`), prefijo `/api`

| Método y ruta | Acceso | Respuesta |
|---|---|---|
| `GET /api/test` | Público | `200`, texto `API SERVER · <SERVER_ID>` |
| `GET /api/health` | Público | `200`, texto `ok` |
| `GET /api/productos?limite=&pagina=` | Sesión | `200` JSON: `servidor`, `total`, `pagina`, `limite`, `productos` (id descendente). Sin sesión: `401` `{"error": "No autenticado"}` |
| `GET /api/productos/<id>` | Sesión | `200` con el producto · `404` `{"error": "Producto no encontrado"}` |

- `limite`: por defecto 50, acotado a [1, 200]. `pagina`: por defecto 1, acotada a [1, 1 000 000]. Un valor no numérico usa el valor por defecto.
- La API es **solo lectura**. No tiene ruta de login: usa la cookie emitida por la app web (mismo dominio, mismo `SECRET_KEY`).
- En modo `api` **no existen** `/login`, `/logout`, `/` ni `/productos/...` (responden 404).

### 7.4 Esquema JSON de un producto

```json
{
  "id": 7,
  "nombre": "Teclado",
  "precio": "12.00",
  "stock": 5,
  "servidor_origen": "Backend 2 - 8082",
  "servidor_actualizacion": "Backend 1 - 8081",
  "creado_en": "2026-09-30T17:24:06+00:00",
  "actualizado_en": "2026-09-30T17:31:40+00:00"
}
```

`precio` siempre como texto con 2 decimales; fechas en ISO 8601 **con zona horaria**; `servidor_actualizacion` puede ser `null`.

### 7.5 Comportamientos transversales

- **Cabecera `X-Servidor: <SERVER_ID>` en todas las respuestas**, incluidas `302`, `400`, `404`, `405`, `500` y JSON (vía `after_request` y los manejadores de error).
- **Errores bajo `/api/`** (404, 405, 500) en JSON `{"error": "..."}`. Fuera de `/api/`, páginas HTML propias.
- **Páginas de error propias** (400 de CSRF, 404, 500) con el pie "Atendido por". **Nunca mostrar un traceback.** La de CSRF explica que el formulario expiró y que basta con recargar.
- **Pie de página** en todas las páginas HTML: "Atendido por: <SERVER_ID>".
- **CSRF entre instancias:** Flask-WTF guarda el token en la cookie de sesión; un formulario generado por una instancia debe aceptarse en otra con el mismo `SECRET_KEY`.
- **Plantillas:** autoescape activo; prohibido `|safe` sobre datos del usuario. CSS en `static/css/app.css`.

---

## 8. Configuración

### 8.1 Regla general

- Toda la configuración entra por **variables de entorno**. La app **se niega a arrancar** (excepción con mensaje claro) si algo obligatorio falta o es inválido.
- **La configuración se construye dentro de `create_app()`, en el momento de la llamada, no al importar módulos.** `create_app(config_overrides=None)` acepta un diccionario que tiene prioridad sobre el entorno. Esto es **obligatorio** para las pruebas: permite crear en el mismo proceso varias apps con distinto `SERVER_ID`, `SECRET_KEY` o base.
- `load_dotenv()` se llama **solo en `wsgi.py`** (y el comando `flask` carga `.env` por sí mismo). `create_app()` no lo llama, para que las pruebas nunca lean el `.env` de desarrollo.
- La app **no depende** de que exista un `.env`.

### 8.2 Variables

| Variable | Obligatoria | Por defecto | Validación |
|---|---|---|---|
| `SECRET_KEY` | Sí | — | ≥ 32 caracteres |
| `DATABASE_URL` | Sí | — | Empieza con `postgresql://` o `postgresql+psycopg://`; se **normaliza** a `postgresql+psycopg://` |
| `DATABASE_URL_DIRECT` | Solo si `USE_DIRECT_DB=1` | — | Misma validación y normalización |
| `USE_DIRECT_DB` | No | `0` | `0` o `1`. Con `1`, la app usa `DATABASE_URL_DIRECT` (solo para migraciones contra Neon) |
| `SERVER_ID` | No | nombre del host (`socket.gethostname()`) | Solo ASCII imprimible, 1–100 caracteres |
| `APP_MODE` | No | `web` | `web` o `api` |
| `LOAD_TEST` | No | `0` | `0` o `1` |
| `CARGA_ITERACIONES` | No | `200000` | Entero entre 1 000 y 5 000 000 |
| `SESSION_COOKIE_SECURE` | No | `0` | `0` o `1` |
| `DETRAS_DE_PROXY` | No | `0` | `0` o `1`. Con `1`, aplica `ProxyFix(x_for=1, x_proto=1)` |
| `FLASK_APP` | Solo local | `wsgi` | — |
| `TEST_DATABASE_URL` | Solo pruebas | — | Ver sección 9 |

### 8.3 Valores fijos de configuración

- `SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_size": 3, "max_overflow": 2, "pool_recycle": 300, "connect_args": {"connect_timeout": 10}}`. Sin este límite, un intento de conexión con la base inalcanzable depende del timeout del sistema operativo (varios intentos, uno por familia de dirección); 10 s da margen para que Neon reactive su cómputo tras inactividad, sin dejar un worker de gunicorn bloqueado indefinidamente.
- `SQLALCHEMY_TRACK_MODIFICATIONS = False`
- `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"`
- `WTF_I18N_ENABLED = False` y formularios con `Meta.locales = ["es"]` (mensajes en español)
- Logs **solo a la salida estándar**; ningún archivo de log. Nunca `debug=True`.

### 8.4 `.env` de desarrollo del agente

El agente **no necesita ni debe usar** las URLs de Neon.

```env
FLASK_APP=wsgi
SECRET_KEY=<generado con: python -c "import secrets; print(secrets.token_urlsafe(50))">
DATABASE_URL=postgresql://lab07:lab07@localhost:5433/lab07_dev
DATABASE_URL_DIRECT=postgresql://lab07:lab07@localhost:5433/lab07_dev
TEST_DATABASE_URL=postgresql://lab07:lab07@localhost:5433/lab07_test
SERVER_ID=Local-dev
APP_MODE=web
LOAD_TEST=0
```

`.env.example` documenta estas variables con valores de ejemplo y un comentario con el formato de URL de Neon (con `-pooler` y `?sslmode=require`) para producción.

### 8.5 Origen de las variables por entorno

| Entorno | Origen | Responsable |
|---|---|---|
| Desarrollo local | `.env` | Agente |
| Contenedores Parte A | Compose (`environment` / `env_file`) | Usuario, etapa 3 |
| EC2 en AWS | SSM Parameter Store → `docker run -e` | Usuario, etapa 3 |

---

## 9. Pruebas

### 9.1 Bases de datos

| Base | Dónde | Uso | Quién |
|---|---|---|---|
| `lab07_dev` | PostgreSQL 18 local en Docker | Correr la app en desarrollo y generar la migración | Agente |
| `lab07_test` | Mismo contenedor | Pruebas automatizadas | Agente |
| Neon (`lab07`) | Nube | Producción | **Solo el usuario** |

Contenedor local (sin volumen, desechable; puerto 5433 para no chocar con un PostgreSQL existente):

```powershell
docker run -d --name lab07-postgres -e POSTGRES_USER=lab07 -e POSTGRES_PASSWORD=lab07 -e POSTGRES_DB=lab07_dev -p 5433:5432 postgres:18-alpine
docker exec lab07-postgres createdb -U lab07 lab07_test
```

Nota: desde PostgreSQL 18 la imagen oficial cambió la ruta de datos; no copiar configuraciones de volumen de versiones anteriores.

### 9.2 Salvaguardas en `conftest.py`

- Las pruebas usan **solo** `TEST_DATABASE_URL`, nunca `DATABASE_URL`. `resolver_test_database_url()` la busca en este orden: (1) variable de entorno; (2) si falta, solo esa clave leída del `.env` del proyecto con `dotenv_values()` —sin `load_dotenv()` y sin tocar `os.environ`, para no contaminar las pruebas de configuración—; (3) si no aparece en ninguna de las dos, la sesión se detiene con un mensaje claro. **Exportar `TEST_DATABASE_URL` a mano es opcional** si ya está en `.env`.
- Si el valor resuelto (venga de donde venga) contiene `neon.tech`, **se niegan a ejecutarse**.
- Al inicio de la sesión de pruebas: esquema limpio y **migración aplicada** (no `create_all`), para probar la migración real.
- Entre pruebas: `TRUNCATE ... RESTART IDENTITY CASCADE` de las tablas de datos.
- Las apps de prueba se crean con `create_app(config_overrides=...)`.

### 9.3 Pruebas unitarias (sin base)

- **Configuración:** `SECRET_KEY` corto, faltante; `SERVER_ID` no ASCII, vacío o > 100; `APP_MODE` inválido; normalización de URL; `CARGA_ITERACIONES` fuera de rango; valores inválidos de variables `0/1`. Cada caso impide el arranque.
- **Formularios:** precio negativo, > 2 decimales, `NaN`, `Infinity`, `-Infinity`, coma decimal, texto, vacío, > 99 999 999,99; stock negativo, decimal, texto, > 1 000 000; nombre vacío o solo espacios; aceptación de `0` en precio y stock. Cada entrada inválida produce **un solo** mensaje, en español.
- **Utilidades:** hash y verificación de contraseña; `to_dict()`; filtro de `next` (incluye `//externo.com`, `/\\externo.com`, `https://externo.com`).

### 9.4 Pruebas de integración (cliente de pruebas + PostgreSQL)

- **Públicas:** `/health`, `/whoami` y `/carga` (con `LOAD_TEST` 0 y 1) responden `200` con la base inalcanzable — **tanto sin sesión como con una cookie de sesión válida**, ya que ninguna ruta pública debe consultar la base nunca, haya o no sesión activa (D5). En modo `api`, `/api/test` y `/api/health` se prueban con la misma condición (base inalcanzable + sesión válida).
- **Autenticación:** login correcto e incorrecto con el mismo mensaje; correo con mayúsculas o espacios; `next` seguro e inseguro; logout solo `POST`; CSRF obligatorio; la sesión guarda solo `usuario_id`; cookie de usuario borrado queda invalidada.
- **CRUD:** `servidor_origen` y `servidor_actualizacion` correctos; 404 con id inexistente y con id > 2³¹−1; HTML escapado en la lista; `confirm()` sin datos del producto; eliminar por `GET` → 405; **restricciones `CHECK` aplicadas por la base** (insertando directo con SQLAlchemy y esperando `IntegrityError`).
- **API:** 401 sin sesión y con cookie inválida; forma exacta del JSON; paginación y sus límites (incluye `pagina` gigante sin error 500); 404/405 en JSON; rutas web inexistentes en modo `api`.
- **`X-Servidor`** presente en respuestas `200`, `302`, `400`, `404`, `405`, `500` y JSON.
- **Error 500:** una ruta de prueba que lanza una excepción devuelve la página 500 propia, **sin traceback**.
- **Seed:** idempotente; correo guardado en minúsculas.

### 9.5 Bloque multi-instancia (el más importante)

Dos apps en el mismo proceso, con distinto `SERVER_ID`, mismo `SECRET_KEY` y misma base:

| Prueba | Resultado esperado |
|---|---|
| Login en A, cookie usada en B | Acceso concedido |
| Formulario generado por A, enviado a B | CSRF aceptado |
| Cookie de una instancia `web` en una `api` | Acceso concedido |
| Crear en A, editar en B | `servidor_origen` = A, `servidor_actualizacion` = B |
| **Control negativo:** `SECRET_KEY` distinto | Cookie **rechazada** |

### 9.6 Migraciones sincronizadas

Una prueba aplica la migración sobre una base vacía y compara el esquema con los modelos (`alembic.autogenerate.compare_metadata`). Cualquier diferencia hace fallar la prueba.

### 9.7 Criterio de "terminado" del agente

1. `pytest` pasa con **cero fallos y cero pruebas omitidas**.
2. Cobertura **≥ 90 %** del paquete `app/`: `pytest.ini` trae `pythonpath = .` (para que `pytest` a secas encuentre el paquete `app`, sin depender de `python -m pytest`) y `addopts = --cov=app --cov-report=term-missing --cov-fail-under=90`, así que basta con `pytest`. El umbral aplica a la **suite completa**; para correr una sola prueba o un solo archivo hay que agregar `--no-cov` (si no, `pytest` puede mostrar "4 passed" y aun así terminar con código de salida distinto de cero, porque la cobertura de ese subconjunto no llega al 90 %).
3. Una **única migración inicial** que coincide con los modelos.
4. Ninguna prueba depende de la hora, del orden de ejecución ni de pausas con `sleep`.

### 9.8 Aceptación manual (usuario, después del agente)

1. Aplicar la migración a Neon: `USE_DIRECT_DB=1` + `flask db upgrade`, con las URLs de Neon.
2. `flask seed` contra Neon.
3. Dos instancias locales contra Neon (puertos distintos, mismo `SECRET_KEY`): login en una, uso en la otra, crear en una y editar en la otra.

Valida lo único que el agente no puede cubrir: la conexión con *pooler* y SSL de Neon.

---

## 10. Reglas de trabajo del agente

### 10.1 Alcance

- Solo la etapa 2: código, pruebas, `README.md`, `.env.example`, `pytest.ini`, `.gitignore` y la actualización de este archivo.
- **Prohibido crear o modificar cualquier cosa dentro de `infra/`.**
- No inventar funcionalidades fuera del contrato de la sección 7 (nada de registro de usuarios, roles ni endpoints adicionales).

### 10.2 Seguridad de los datos

- **Nunca conectarse a Neon.** Solo `lab07_dev` y `lab07_test` en `localhost:5433`.
- Nunca escribir secretos en el código, logs ni commits. Nunca `debug=True`.
- Todo acceso a datos pasa por el ORM; nunca SQL armado concatenando texto.
- Nunca `|safe` sobre datos del usuario.

### 10.3 Cuándo detenerse y preguntar

- Si la especificación es ambigua o una decisión parece incorrecta.
- Si una prueba solo pasa relajando un requisito (bajar cobertura, omitir pruebas, ampliar límites).
- Si hace falta una dependencia fuera de la sección 4.

### 10.4 Fases y puntos de control

| Fase | Contenido |
|---|---|
| F1 | Entorno: venv con Python 3.14, `requirements*.txt` fijados, contenedor PostgreSQL, `.env`, `.gitignore` |
| F2 | `config.py`, `extensions.py`, `create_app()`, `wsgi.py`, rutas públicas |
| F3 | Modelos, borrado de `migrations/` anterior, migración inicial única, `flask seed` |
| F4 | Autenticación |
| F5 | CRUD web |
| F6 | API |
| F7 | Cabecera `X-Servidor`, páginas de error, CSS, pie de página |
| F8 | Pruebas multi-instancia, prueba de migraciones sincronizadas, cobertura ≥ 90 % |
| F9 | `README.md` (instalación, ejecución, pruebas), `.env.example`, cierre de este archivo |

Cada fase incluye sus propias pruebas; F8 completa las transversales.

**Protocolo al cerrar cada fase:**

1. Ejecutar `pytest` completo (desde F2).
2. Verificar que no haya decoradores pegados: `Select-String -Path app\*.py,app\blueprints\*.py -Pattern "\)@"` debe devolver cero líneas.
3. Commit en **Conventional Commits** (`feat:`, `fix:`, `test:`, `docs:`, `chore:`) y push. Sin `--force`, sin reescribir el historial.
4. Actualizar las secciones 3 y 14.
5. Reportar: qué se hizo, resultado de las pruebas, cualquier desviación.
6. **Esperar la confirmación del usuario** antes de la fase siguiente.

### 10.5 Entorno del usuario

- Windows con PowerShell. Python 3.14.7 (`python` y `py` apuntan a la misma instalación).
- Crear el entorno: `python -m venv venv` y `venv\Scripts\activate`. Si la activación falla por la política de ejecución: `Set-ExecutionPolicy Bypass -Scope Process`.
- Docker 29 y Docker Compose v5 disponibles.

### 10.6 Trampas conocidas (vividas en el intento anterior)

| Trampa | Regla |
|---|---|
| SQLAlchemy 2.1 cambió su driver por defecto para `postgresql://` | Normalizar a `postgresql+psycopg://` en la configuración |
| Decoradores pegados en una línea (`)@login_required`) | Verificación del protocolo 10.4 |
| Placeholders `<...>` olvidados en el `.env` | La validación de arranque lo detecta |
| `DataRequired` rechaza el valor `0` | `InputRequired` en campos numéricos |
| `Decimal` acepta `NaN` e `Infinity` | Validador de número finito que corta la cadena con `StopValidation` |
| Doble mensaje de error en campos numéricos con texto | Si `campo.data is None` tras la conversión, `StopValidation()` sin mensaje |
| Mensajes de WTForms en inglés | `WTF_I18N_ENABLED = False` + `locales = ["es"]` |
| Id enorme en la URL provoca un error 500 | Conversor `int(max=2147483647)` |
| `Decimal` no se serializa a JSON | `precio` como texto en `to_dict()` |
| Modelos no importados → migración vacía | Importar `app.models` en `create_app()` |
| Configuración leída al importar el módulo | Construirla en `create_app()` (sección 8.1) |
| `Email()` exige `email-validator` | No usarlo |
| `APP_MODE` mal escrito deja una instancia "sana" sin rutas | Validación estricta al arrancar |

---

## 11. Infraestructura — referencia para la etapa 3 (⛔ fuera del alcance del agente)

### 11.1 Parte A — local, en el PC del usuario con Docker Compose

```
Navegador / curl / ab
      │  http://localhost  (8080 si el 80 está ocupado)
      ▼
Docker Compose
  nginx:alpine :80 ── upstream (RR / least_conn / ip_hash / weight / max_fails)
      ├─► backend1  (127.0.0.1:8081)  SERVER_ID="Backend 1 - 8081"
      ├─► backend2  (127.0.0.1:8082)  SERVER_ID="Backend 2 - 8082"
      └─► backend3  (127.0.0.1:8083)  SERVER_ID="Backend 3 - 8083"
      (misma imagen, DETRAS_DE_PROXY=1)
                 │
                 ▼
        Neon · lab07 · PostgreSQL 18
```

- Ejercicio 2: `docker compose stop backend2` / `docker compose start backend2`.
- Ejercicio 3: `ab` desde la imagen oficial `httpd`, contra `/whoami` (y directo contra un backend). Compite por CPU con los backends: dejarlo explícito en el análisis.

### 11.2 Parte B — AWS (`us-east-2`)

```
Internet → ALB alb-lab-web (sg-alb-lab: 80 desde Internet) · Listener HTTP:80
   ├─ prioridad 10: /api/* → tg-lab-api (:8000, /health) → api-server   (APP_MODE=api)
   └─ por defecto          → tg-lab-web (:8000, /health) → web-server-1 (us-east-2a)
                                                         → web-server-2 (us-east-2b)
                                                         → asg-lab-web  (Ejercicio 5)
VPC vpc-lab-lb 10.0.0.0/16 · 2 subredes públicas · IGW · sin NAT Gateway · sin VPC endpoints
EC2 Amazon Linux 2023, x86_64 (t2.micro / t3.micro según Free tier):
  · sg-web-lab: 8000 desde sg-alb-lab y la IP del usuario · 22 desde la IP del usuario
  · rol IAM con lectura de SSM limitada a /lab07/*
  · User Data: instalar Docker → leer SSM (/lab07/SECRET_KEY, /lab07/DATABASE_URL)
               → token IMDSv2 (Instance ID y zona → SERVER_ID)
               → docker run -p 8000:8000 --restart unless-stopped <usuario>/lab07:<versión>
```

### 11.3 Decisiones para la etapa 3

| # | Decisión |
|---|---|
| 1 | Imagen construida en el PC del usuario y publicada en Docker Hub con **etiqueta de versión** (p. ej. `v1.0.0`), nunca `latest` |
| 2 | Instancias x86_64, no ARM |
| 3 | Permiso IAM de SSM limitado a `/lab07/*` |
| 4 | `DETRAS_DE_PROXY=1` en todo contenedor detrás de Nginx o del ALB |
| 5 | `LOAD_TEST=1` solo en la plantilla de lanzamiento del Ejercicio 5; se retira al terminar |
| 6 | Migración a Neon aplicada por el usuario antes de la etapa 3 (sección 9.8) |
| 7 | Target Groups: puerto 8000, health check `/health`, umbrales 2/2, intervalo 30 s |
| 8 | Auto Scaling: health check tipo ELB, gracia ≥ 300 s, monitoreo detallado, target tracking CPU 50 %, capacidad 2/2/4 |
| 9 | Retirar `web-server-1` y `web-server-2` de `tg-lab-web` antes del Ejercicio 5 |
| 10 | Cookie sin `Secure` mientras el ALB exponga solo HTTP (limitación documentada) |

**Abiertas para la etapa 3:** imagen base (`python:3.14-slim` o `python:3.14-alpine`) y número de workers de gunicorn por contenedor.

### 11.4 Nombres de recursos AWS

`vpc-lab-lb` · `sg-alb-lab` · `sg-web-lab` · `web-server-1` · `web-server-2` · `api-server` · `tg-lab-web` · `tg-lab-api` · `alb-lab-web` · `lt-lab-web` · `asg-lab-web` · rol IAM de EC2 para SSM *(nombre a definir)*

---

## 12. Registro de decisiones

| # | Decisión | Motivo |
|---|---|---|
| D1 | Flask + plantillas Jinja, sin frontend separado | Menos piezas; despliegue en contenedor directo |
| D2 | Flask-SQLAlchemy + Flask-Migrate | ORM y consultas parametrizadas por defecto |
| D3 | Sesión en cookie firmada | Válida en cualquier instancia con el mismo `SECRET_KEY` |
| D4 | Base compartida en Neon (producción) | Todas las instancias ven los mismos datos |
| D5 | `/health` sin base | Una caída de Neon no marca todos los targets como no saludables |
| D6 | `/whoami` y cabecera `X-Servidor` | Balanceo verificable con `curl`, incluso en redirecciones y errores |
| D7 | `/carga` solo con `LOAD_TEST=1` e iteraciones configurables | Generar CPU para el Auto Scaling sin dejar una puerta permanente a DoS |
| D8 | API de solo lectura; `/api/test` y `/api/health` públicos | El `curl` del Ejercicio 4 funciona sin credenciales; datos protegidos |
| D9 | `servidor_origen` inmutable + `servidor_actualizacion` | Evidencia de escrituras de distintos servidores sobre el mismo registro |
| D10 | Infraestructura con Docker; archivos en `infra/`, escritos por el usuario | Arranque reproducible del Auto Scaling y aprendizaje DevOps |
| D11 | Pruebas contra PostgreSQL 18 local, nunca contra Neon | Mismo motor que producción, aislado y desechable |
| D12 | Configuración construida en `create_app()` con overrides | Pruebas multi-instancia en un solo proceso |
| D13 | `SERVER_ID` ASCII | Las cabeceras HTTP no admiten caracteres fuera de ASCII |
| D14 | `DETRAS_DE_PROXY` desactivado por defecto | Confiar en `X-Forwarded-*` sin proxy permitiría falsificarlas |
| D15 | Secretos en SSM Parameter Store en AWS | En User Data quedarían visibles en la plantilla de lanzamiento |

---

## 13. Checklist del laboratorio

- [x] Etapa 2: criterio de terminado del agente (9.7)
- [ ] Aceptación manual contra Neon (9.8)
- [ ] Parte A: Nginx + 3 backends (Round Robin)
- [ ] Ejercicio 1: pesos 5/3/2, 100 peticiones a `/whoami`
- [ ] Ejercicio 2: `max_fails` / `fail_timeout`, caída y recuperación de `backend2`
- [ ] Ejercicio 3: `ab` directo vs. a través de Nginx
- [ ] Parte B: VPC, Security Groups, 2 EC2, Target Group, ALB, prueba de failover
- [ ] Ejercicio 4: `tg-lab-api` + regla `/api/*`
- [ ] Ejercicio 5: Launch Template + Auto Scaling + carga con `/carga`
- [ ] Limpieza AWS: ASG → ALB → Target Groups → EC2 → Launch Template → Security Groups → VPC; parámetros SSM y rol IAM
- [ ] 3 conclusiones del GLAB-S07

---

## 14. Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-30 | Primera iteración de planificación y desarrollo parcial (estructura plana, sin pruebas automatizadas). Verificada a mano la sesión compartida entre instancias. |
| 2026-09-30 | Segunda iteración de planificación cerrada: especificación completa para el agente (secciones 1–13). Etapa 3 renombrada a "Infraestructura y balanceo de carga", manual. Base de Neon reiniciada (prerrequisito 1). |
| 2026-09-30 | **F1 cerrada:** venv con Python 3.14.7; dependencias de ejecución instaladas con versiones exactas de la sección 4 y congeladas en `requirements.txt` (`pip freeze`, UTF-8); `requirements-dev.txt` agrega `pytest==9.1.1` y `pytest-cov==7.1.0`; contenedor `postgres:18-alpine` en `localhost:5433` con `lab07_dev` y `lab07_test`; `.env` de desarrollo generado (`SECRET_KEY` propio, no compartido); `.gitignore` completado con `.pytest_cache/`, `.coverage`, `htmlcov/`. Sin código de app tocado todavía. |
| 2026-09-30 | **F2 cerrada:** `app/config.py` reescrito como `construir_configuracion(config_overrides=None)` que valida todas las variables de la sección 8.2 (excepciones claras, sin leer el entorno al importar el módulo); `app/__init__.py` con `create_app(config_overrides=None)` construye la configuración en el momento de la llamada y aplica `ProxyFix` si `DETRAS_DE_PROXY=1`; `wsgi.py` es el único lugar que llama `load_dotenv()`; nuevo paquete `app/blueprints/` con `publico.py` (`/health`, `/whoami`, `/carga`, con `CARGA_ITERACIONES` configurable); `app/publico.py` (ruta antigua) eliminado. `pytest.ini` y `tests/conftest.py` creados con las salvaguardas de la sección 9.2 (exige `TEST_DATABASE_URL`, rechaza `neon.tech`). 45 pruebas nuevas (unitarias de configuración + integración de rutas públicas), todas en verde. Los archivos planos del intento anterior (`auth.py`, `productos.py`, `api.py`, `cli.py`, `forms.py`, `models.py`) se dejan intactos como referencia; se reemplazan en las fases F3–F6. |
| 2026-09-30 | **F3 cerrada:** `app/models.py` reescrito con `Usuario` y `Producto` (incluye `servidor_actualizacion`, las tres `CheckConstraint` con los nombres de la sección 6 y `to_dict()` con precio en texto de 2 decimales y fechas ISO 8601 con zona horaria); `app/models` se importa dentro de `create_app()` para que Flask-Migrate detecte las tablas. Carpeta `migrations/` del intento anterior borrada y regenerada con `flask db init` + `flask db migrate`: una única migración inicial (`f02560b6e5c9_tablas_usuarios_y_productos.py`) aplicada contra `lab07_dev` únicamente. `app/cli.py` con el comando `flask seed`, idempotente, registrado en `create_app()`. `tests/conftest.py` ahora aplica la migración real sobre `lab07_test` al inicio de la sesión de pruebas (esquema limpio, `DROP/CREATE SCHEMA` + `flask db upgrade` vía subproceso) y trunca las tablas de datos entre pruebas. 10 pruebas nuevas: modelos unitarios, migración sincronizada con los modelos (`compare_metadata`), seed idempotente en minúsculas, y las tres `CHECK` aplicadas por la base. 55 pruebas en total, todas en verde. |
| 2026-09-30 | **F4 cerrada:** nuevo `app/blueprints/auth.py` con `/login` (GET/POST), `/logout` (solo POST), `login_required` y `usuario_de_sesion()` (limpia la cookie si el usuario ya no existe); un `before_app_request` deja `g.usuario` disponible en toda petición del modo `web`. `app/forms.py` reescrito con `LoginForm` (sin el validador `Email()`). `create_app()` registra el blueprint de auth y el `context_processor` de `server_id` solo en modo `web`. Se reutilizan `templates/base.html` y `templates/login.html` del intento anterior (ya cumplían el contrato). `app/auth.py` (plano, del intento anterior) eliminado. 10 pruebas de integración nuevas: login correcto/incorrecto con mensaje único, normalización de correo, `next` seguro e inseguro, `logout` solo `POST`, CSRF obligatorio y aceptado con token válido, sesión con solo `usuario_id`, invalidación de cookie de usuario borrado. 65 pruebas en total, todas en verde. |
| 2026-09-30 | **F5 cerrada:** `app/forms.py` agrega `ProductoForm` (precio/stock con `InputRequired` + validador de número finito + `NumberRange`, `validate_precio` para máximo 2 decimales, `validate_nombre` para rechazar solo espacios). Nuevo `app/blueprints/productos.py`: `GET /` (lista, id descendente), `GET/POST /productos/nuevo` (`servidor_origen = SERVER_ID`), `GET/POST /productos/<int(max=2147483647):id>/editar` (precarga, fija `servidor_actualizacion = SERVER_ID`, nunca toca `servidor_origen`), `POST /productos/<id>/eliminar`; las tres protegidas con `login_required`. Se reutilizan `templates/productos/lista.html` y `form.html` del intento anterior (autoescape activo, `confirm()` con texto fijo). `app/productos.py` (plano) eliminado. Verificado a mano en el navegador: login, crear, editar con precarga, listar. 32 pruebas nuevas: formulario de producto (todos los casos de la sección 9.3), CRUD con `servidor_origen`/`servidor_actualizacion` correctos entre dos instancias simuladas, 404 con id inexistente y con id > 2³¹−1, `eliminar` por `GET` → 405, HTML escapado en la lista. 97 pruebas en total, todas en verde. |
| 2026-09-30 | **F6 cerrada:** nuevo `app/blueprints/api.py` con prefijo `/api`: `GET /api/test` y `GET /api/health` públicos, `GET /api/productos` (paginado, protegido con `api_login_required` basado en la cookie de sesión) y `GET /api/productos/<int(max=2147483647):id>`. `register_api()` agrega manejadores de error 404/405 que devuelven JSON solo bajo `/api/` (fuera de ese prefijo se conserva el comportamiento por defecto de Flask, pendiente de reemplazo en F7). `create_app()` registra este blueprint solo en modo `api`; en ese modo no se registran `auth` ni `productos`, así que `/login`, `/logout`, `/` y `/productos/...` responden 404. `app/api.py` (plano) eliminado. 21 pruebas nuevas: forma exacta del JSON, 401 sin sesión y con cookie inválida, límites de paginación (incluida página gigante sin error 500), 404/405 en JSON, y las rutas web inexistentes en modo `api`. 118 pruebas en total, todas en verde. |
| 2026-09-30 | **F7 cerrada:** `create_app()` centraliza, para ambos modos, un `after_request` que agrega `X-Servidor` a toda respuesta y manejadores de error para `CSRFError` (400), 404, 405 y 500 que devuelven JSON bajo `/api/` y páginas HTML propias (`templates/errores/400.html`, `404.html` —reutilizada también para 405—, `500.html`) fuera de ese prefijo, todas sin traceback y con el pie "Atendido por" heredado de `base.html`. El manejo de errores que vivía en `app/blueprints/api.py` (`register_api`) se eliminó por quedar duplicado; ese módulo ahora solo expone el blueprint `bp`. El CSS en línea de `base.html` se movió a `app/static/css/app.css`, enlazado con `<link>`. Verificado a mano en el navegador: CSS externo aplicado y página 404 propia con pie de página. 12 pruebas nuevas: `X-Servidor` en 200/302/400/404/405/500 y en JSON, páginas 400/404/500 propias sin traceback (incluida una ruta de prueba registrada dinámicamente que lanza una excepción), 500 en modo `api` como JSON sin traceback, CSS servido desde `/static/css/app.css`, pie de página presente. 130 pruebas en total, todas en verde. |
| 2026-09-30 | **F8 cerrada:** nuevo `tests/integration/test_multi_instancia.py` con las 5 filas de la sección 9.5 (login en A/cookie usada en B, formulario de A enviado a B con CSRF aceptado, cookie de una instancia `web` aceptada en una `api`, crear en A/editar en B con `servidor_origen`/`servidor_actualizacion` correctos, control negativo con `SECRET_KEY` distinto → cookie rechazada), transfiriendo la cookie real entre clientes de prueba con `client.set_cookie()`. Se eliminó `ProductoForm.validate_nombre`: era código muerto, ya que `DataRequired` de WTForms trata las cadenas de solo espacios como vacías. Pruebas nuevas para cerrar huecos de cobertura con casos reales del contrato: `GET /productos/nuevo`, reemisión del formulario inválido, precarga en `GET /productos/<id>/editar`, `GET /login` con sesión activa (redirige a `/`), y `DETRAS_DE_PROXY=1` ejercitando `ProxyFix`. La prueba de migración sincronizada con los modelos (`compare_metadata`), ya existente desde F3, se mantiene en verde. **Criterio de "terminado" del agente (9.7) cumplido:** 140 pruebas, cero fallos, cero omitidas; cobertura 99.70 % (`pytest --cov=app --cov-report=term-missing --cov-fail-under=90`); una única migración inicial; ninguna prueba depende de la hora, del orden de ejecución ni de `sleep`. |
| 2026-09-30 | **F9 cerrada — etapa 2 (Desarrollo) completa.** `README.md` nuevo: requisitos, instalación paso a paso (venv, dependencias, contenedor PostgreSQL, `.env`, migración, `flask seed`), ejecución (`flask run` / `gunicorn wsgi:app`), variables de entorno más relevantes, cómo correr las pruebas con y sin cobertura, estructura del proyecto, y los pasos de aceptación manual contra Neon que le corresponden al usuario (9.8). `.env.example` reescrito: documenta las 10 variables de la sección 8.2 con comentarios, corrige el `SERVER_ID` de ejemplo (tenía un carácter no-ASCII, inválido según la validación de la sección 8.2), y separa el valor de desarrollo local (contenedor Docker) del de producción (Neon, comentado). Esta tabla (sección 3) y la sección 14 quedan como cierre; no se modificaron las secciones de decisiones (12) sin aprobación. Siguiente paso: ninguno para el agente — sigue la etapa 3, manual, a cargo del usuario. |