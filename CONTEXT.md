# CONTEXT.md — Lab07: App LOGIN + CRUD detrás de un balanceador de carga

> ## Instrucciones para el agente (léelas antes que nada)
>
> 1. Este archivo es la **especificación completa y la fuente de verdad** del proyecto. Léelo entero antes de cualquier tarea y vuelve a él cuando pierdas contexto.
> 2. La **etapa 2 (Desarrollo) está cerrada y congelada**: no modifiques `app/`, `tests/`, `migrations/` ni los archivos `requirements*.txt` sin aprobación explícita. Tu alcance ahora es la **etapa 3 (Infraestructura y balanceo de carga)**: todo lo que vive en `infra/`, más los registros y entregables descritos en la sección 11.
> 3. Trabajas sobre **infraestructura real y con costo** en la cuenta AWS del usuario. Las reglas de la **sección 10** (perfil acotado, etiquetas, compuertas de aprobación, control de costos, secretos y limpieza) son obligatorias y prevalecen sobre cualquier otra instrucción.
> 4. Trabaja por **fases I0–I9**. Avanza entre fases sin esperar, salvo en las **compuertas G1–G4** (sección 10.4) y cuando se cumpla una condición de detención (sección 10.3).
> 5. Al cerrar cada fase: verifica, haz commit y push (solo lo versionable), actualiza la **sección 3** y agrega una entrada en la **sección 14**. No modifiques las secciones de decisiones (12) sin aprobación.
> 6. **Nunca imprimas, registres ni versiones secretos** (`SECRET_KEY`, contraseñas, `DATABASE_URL` completa, claves de acceso, tokens). Si ves uno en una salida, no lo copies.
> 7. Si la especificación es ambigua o crees que una decisión debería cambiar, **detente y pregunta**. Puedes proponer cambios; no aplicarlos sin aprobación.

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
| 2 | Desarrollo (código y pruebas) | Agente de IA | ✅ Cerrada y congelada (152 pruebas, cobertura 99,70 %) |
| 3 | Infraestructura y balanceo de carga (Docker, Nginx, AWS) | **Agente de IA**, con compuertas de aprobación del usuario | ⏳ Pendiente |

**Cambio respecto a la versión anterior:** la etapa 3 se había definido como manual (aprendizaje DevOps); el usuario decidió delegarla al agente de punta a punta (D19).

**Sigue en manos del usuario:** credenciales y perfil de AWS, presupuesto, `docker login` en Docker Hub, las aprobaciones G1–G4, las **capturas de la consola de AWS**, el **video de demostración**, el informe y las 3 conclusiones del GLAB-S07.

---

## 3. Estado actual

**Última actualización:** 2026-10-01

- **Etapa 2 cerrada.** F1–F9 y la ronda de correcciones R1 completas. Verificado por el usuario en una terminal limpia: `pytest` a secas → **152 pruebas aprobadas, cobertura 99,70 %**, contra el PostgreSQL local.
- **Neon descartado** (D16). PostgreSQL 18 en contenedor en todos los entornos.
- **I0 cerrada.** Prerrequisitos y estado del repo verificados (ver changelog). **Bloqueada en la compuerta G1**: faltan 3 de los 4 prerrequisitos del usuario.

### Artefactos de la etapa 3 que pueden existir ya (el agente los verifica en I0; no asume que funcionan)

| Artefacto | Origen | Estado conocido |
|---|---|---|
| `infra/docker/Dockerfile` y `Dockerfile.dockerignore` | Usuario | Presentes en el repo (sin commitear todavía), contenido idéntico a la referencia de 11.1. Imagen `lab07:dev` construida y probada por el usuario: 266 MB en disco (61,7 MB de contenido), `healthy`, `/whoami` y `/health` correctos, cabecera `X-Servidor` presente, servidor gunicorn. **Sin verificar aún (tarea de I1):** login contra una base real desde el contenedor, usuario no root (`id`), tamaño del contexto de build |
| `infra/compose/` y `infra/nginx/` (Parte A) | Asistente (paquete ZIP) | **No están extraídos en el repo** (verificado en I0: `infra/` solo contiene `infra/docker/`). Pendientes para I2 |

### Prerrequisitos del usuario antes de lanzar al agente

| # | Prerrequisito | Estado |
|---|---|---|
| 1 | AWS CLI v2 instalado y **perfil `lab07`** configurado con las credenciales de un **usuario IAM dedicado** (no root), región `us-east-2` | ❌ AWS CLI v2 instalado (`aws-cli/2.36.6`); **el perfil `lab07` no existe** (`aws configure list-profiles` solo muestra `r2`) |
| 2 | **Alerta de presupuesto** (AWS Budgets) con aviso por correo | ⏳ No verificable sin el perfil `lab07` |
| 3 | Docker Desktop encendido y `docker login` hecho en Docker Hub; nombre de usuario de Docker Hub comunicado al agente | ❌ Docker Desktop encendido (`docker info` responde); **sin sesión de Docker Hub** detectable (`docker info` no reporta `Username`); nombre de usuario no comunicado |
| 4 | Este `CONTEXT.md` en la raíz del repo, con commit y push | ✅ Commiteado y pusheado al cerrar I0 |

**Siguiente paso:** ninguno para el agente. **Esperando la confirmación de la compuerta G1** (sección 10.4): cuenta de AWS (ARN) y región, presupuesto configurado, perfil `lab07` creado, y usuario de Docker Hub.

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
| Base de datos | PostgreSQL | **18** (contenedor `postgres:18-alpine` en todos los entornos; Neon descartado, D16) |

Verificado el 2026-09-30: `psycopg-binary` y `SQLAlchemy` publican paquetes precompilados para Python 3.14 en Windows, Linux glibc y Linux musl.

### Reglas del stack

- **Versiones fijadas con `==`.** `requirements.txt` contiene las dependencias de ejecución **y sus dependencias indirectas**, generado con `pip freeze` desde un entorno limpio que solo tenga las dependencias de ejecución.
- `requirements-dev.txt` empieza con `-r requirements.txt` y agrega solo `pytest` y `pytest-cov` fijados.
- **No agregar dependencias** fuera de esta tabla sin aprobación.
- **Contraseñas con `werkzeug.security`**. No usar `passlib` ni `bcrypt`.
- **No usar el validador `Email()`** de WTForms (exige `email-validator`, no incluido).

### Herramientas de la etapa 3

| Componente | Versión / imagen |
|---|---|
| Docker Engine / Compose | 29.6.1 / v5.3.0 (Docker Desktop del usuario) |
| Imagen base de la app | `python:3.14-slim` |
| Balanceador local | `nginx:alpine` |
| Base de datos | `postgres:18-alpine` |
| Pruebas de carga | `httpd:alpine` (`ab`); alternativa `httpd:2.4` |
| AWS CLI | v2, perfil `lab07`, región `us-east-2` |
| SO de las EC2 | Amazon Linux 2023, x86_64 |

- La imagen de la app se publica con **etiqueta de versión inmutable** (`v1.0.0`), nunca `latest`. Las imágenes de terceros se fijan por etiqueta mayor (`nginx:alpine`, `postgres:18-alpine`).

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
└── infra/                      # ✅ ETAPA 3 — la construye el agente
    ├── docker/                 # Dockerfile y Dockerfile.dockerignore
    ├── compose/                # docker-compose.yml de la Parte A y .env.example (el .env real NO se versiona)
    ├── nginx/
    │   ├── conf.d/             # balanceador.conf: configuración ACTIVA (montada en el contenedor)
    │   └── variantes/          # roundrobin, pesos, failover, iphash, leastconn
    ├── aws/                    # 00-config.ps1 … 99-limpieza.ps1 y userdata/ (db.sh, web.sh)
    ├── RUNBOOK.md              # reconstrucción desde cero y el porqué de cada decisión
    ├── RESULTADOS.md           # resultados medidos de los ejercicios
    ├── GUIA-CAPTURAS.md        # capturas de la consola de AWS que debe tomar el usuario
    └── evidencias/             # salidas de CLI y logs — NO se versiona (repositorio público)
```

- Etapa 2 (congelada): `app/`, `tests/`, `migrations/` y `requirements*.txt` no se tocan sin aprobación. Etapa 3: todo lo que vive en `infra/`.
- El `Dockerfile` se construirá con la raíz como contexto: `docker build -f infra/docker/Dockerfile .` (BuildKit lee `Dockerfile.dockerignore` junto al `Dockerfile`).
- `.gitignore` debe incluir: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `instance/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `infra/evidencias/` y `infra/compose/.env`.

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
- La migración se genera contra `lab07_dev` (local), **nunca contra una base compartida o de producción**.
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
| `DATABASE_URL_DIRECT` | Solo si `USE_DIRECT_DB=1` | — | Misma validación y normalización. *Heredada de Neon: sin uso desde D16* |
| `USE_DIRECT_DB` | No | `0` | `0` o `1`. Con `1`, la app usa `DATABASE_URL_DIRECT`. *Heredada de Neon: sin uso desde D16* |
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

Neon fue descartado (D16): no hay URLs externas.

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

`.env.example` documenta estas variables con valores de ejemplo. La versión de la etapa 2 incluye comentarios sobre Neon: retirarlos en la fase I9.

### 8.5 Origen de las variables por entorno

| Entorno | Origen | Responsable |
|---|---|---|
| Desarrollo local | `.env` | Agente |
| Contenedores Parte A | Compose (`environment`; `SECRET_KEY` desde `infra/compose/.env`) | Agente, etapa 3 |
| EC2 en AWS | SSM Parameter Store → `docker run -e` (sección 11.4) | Agente, etapa 3 |

### 8.6 Parámetros SSM (AWS)

`/lab07/SECRET_KEY`, `/lab07/POSTGRES_PASSWORD` y `/lab07/DATABASE_URL`, todos `SecureString`. Detalle en la sección 11.4.

---

## 9. Pruebas

### 9.1 Bases de datos

| Base | Dónde | Uso | Quién |
|---|---|---|---|
| `lab07_dev` | PostgreSQL 18 local en Docker | Correr la app en desarrollo y generar la migración | Agente |
| `lab07_test` | Mismo contenedor | Pruebas automatizadas | Agente |
| Postgres de la etapa 3 | Compose (Parte A) / EC2 `db-server` (Parte B) | Verificación de la infraestructura | Agente (etapa 3) |

Contenedor local (sin volumen, desechable; puerto 5433 para no chocar con un PostgreSQL existente):

```powershell
docker run -d --name lab07-postgres -e POSTGRES_USER=lab07 -e POSTGRES_PASSWORD=lab07 -e POSTGRES_DB=lab07_dev -p 5433:5432 postgres:18-alpine
docker exec lab07-postgres createdb -U lab07 lab07_test
```

Nota: desde PostgreSQL 18 la imagen oficial cambió la ruta de datos: **montar los volúmenes en `/var/lib/postgresql`**, no en `/var/lib/postgresql/data`.

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

### 9.8 Aceptación manual contra Neon — retirada

Neon fue descartado (D16). La aceptación en infraestructura real se define en la sección 11.9.

---

## 10. Reglas de trabajo del agente (etapa 3)

### 10.1 Alcance

- **Solo la etapa 3:** `infra/`, las secciones de ejecución y despliegue del `README.md`, `.gitignore`, y en este archivo las secciones 3, 13, 14 y 15.
- **Etapa 2 congelada.** Si la infraestructura revela un defecto de la app, **detente y repórtalo con una propuesta**; no lo corrijas por tu cuenta.
- No cambies el diseño de la sección 11 (nombres, puertos, topología, tipos de recurso) sin aprobación.
- **No son tu responsabilidad:** las capturas de la consola de AWS, el video, el informe y las conclusiones. Sí debes entregar la guía que le indica al usuario qué capturar y cuándo (11.12).

### 10.2 AWS: perfil, región, identidad y etiquetas

- Todas las llamadas con `--profile lab07 --region us-east-2`. Región única: **nunca** crear recursos en otra.
- En I0 ejecuta `aws sts get-caller-identity` y muestra el **ARN** al usuario (G1). El ID de cuenta **no debe aparecer** en archivos versionados ni en commits; obtenlo en tiempo de ejecución y enmascáralo en las evidencias.
- **Nunca** usar credenciales root; **nunca** crear ni rotar claves de acceso; **nunca** modificar usuarios, grupos o políticas IAM existentes. Lo único que puedes crear en IAM es el rol `role-lab07-ec2` y su perfil de instancia `profile-lab07-ec2`.
- **Todo recurso que crees lleva la etiqueta `Project=lab07`** (y `Name` donde aplique).
- Mantén un **registro de recursos** `infra/evidencias/recursos.md` (fuera del control de versiones): cada recurso con su ID, tipo, fase y hora de creación. La limpieza se basa en ese registro y en la consulta por etiqueta.
- **Solo modifica o elimina recursos con la etiqueta `Project=lab07` o que figuren en tu registro.** Cualquier otro: detente y pregunta.
- Antes de crear algo, haz una consulta de solo lectura (`describe-*`) y usa `--dry-run` cuando el comando lo admita.
- **Prohibido sin aprobación:** NAT Gateway, Elastic IP, VPC endpoints, RDS, instancias fuera del free tier, más de 6 instancias simultáneas, y cualquier recurso que no esté en la sección 11.
- **Puertos:** nunca abrir a `0.0.0.0/0` otro puerto que no sea el 80 de `sg-alb-lab`. **Nunca** abrir el 22 ni el 5432 a Internet.

### 10.3 Cuándo detenerte y preguntar

- Un comando que crearía, modificaría o eliminaría un recurso sin etiqueta o que no creaste tú.
- Un costo no previsto en la sección 11.8.
- Una falla que persiste tras 2 reintentos con causa distinta.
- Una prueba que solo pasa relajando el criterio de aceptación.
- Un defecto de la app (etapa 2).
- Una discrepancia entre esta especificación y la realidad (por ejemplo, un comando o parámetro de AWS que no existe como está escrito).
- Un prerrequisito faltante.

### 10.4 Fases y compuertas

| Fase | Contenido |
|---|---|
| **I0** | Verificar prerrequisitos y el estado del repo: `docker`, `aws sts get-caller-identity`, `docker login`, `infra/` existente, `git status` limpio, que `pytest` siga en verde |
| **I1** | Imagen: validar `Dockerfile`; construir; probar; **publicar en Docker Hub** como `v1.0.0` y verificar el `pull` |
| **I2** | Parte A: Compose + Nginx; Round Robin; sesión a través del balanceador |
| **I3** | Ejercicios 1 a 3 con resultados en `infra/RESULTADOS.md` |
| **I4** | AWS base (sin costo): VPC, subredes, rutas, Security Groups, rol IAM, parámetros SSM, `00-config.ps1` y `99-limpieza.ps1` |
| **I5** | `db-server`; migración y seed desde dentro de la VPC |
| **I6** | Parte B: `web-server-1`, `web-server-2`, `tg-lab-web`, ALB; prueba de failover |
| **I7** | Ejercicio 4: `api-server`, `tg-lab-api` y la regla `/api/*` |
| **I8** | Ejercicio 5: Launch Template, Auto Scaling y carga con `/carga` |
| **I9** | Cierre: `RESULTADOS.md`, `RUNBOOK.md`, `GUIA-CAPTURAS.md`, README, **limpieza** y verificación de que no queda nada |

**Compuertas** (el agente se detiene y espera la respuesta del usuario):

| Compuerta | Cuándo | Qué se confirma |
|---|---|---|
| **G1** | Tras I0 | Cuenta (ARN), región, presupuesto configurado y usuario de Docker Hub |
| **G2** | Tras I3, antes de I4 | Reporte de la Parte A y de los Ejercicios 1–3; el usuario aprueba iniciar AWS |
| **G3** | Antes de I8 | El usuario aprueba la carga del Ejercicio 5 (genera costo y tráfico) y confirma que **ya capturó las evidencias de la Parte B y del Ejercicio 4**: en I8 `web-server-1/2` se detienen y el Target Group cambia |
| **G4** | Antes de la limpieza en I9 | El usuario confirma que **capturó las evidencias de la consola** |

Entre compuertas, avanza sin esperar. Al llegar a G4, deja todos los recursos arriba hasta recibir confirmación.

### 10.5 Protocolo al cerrar cada fase

1. Ejecutar las verificaciones de la sección 11.9 correspondientes y registrar el resultado.
2. Comprobar que `git status` no incluya secretos, evidencias ni archivos `.env`.
3. Commit en **Conventional Commits** (`feat(infra):`, `docs:`, `chore:`) y push. Sin `--force`, sin reescribir el historial.
4. Actualizar el registro de recursos y las secciones 3 y 14.
5. Informar brevemente: qué se hizo, resultado de las verificaciones, recursos activos y cualquier desviación.

### 10.6 Secretos y datos sensibles

- **Nunca** en el repo, los logs, las salidas, los commits ni las evidencias: `SECRET_KEY`, contraseña de PostgreSQL, `DATABASE_URL` completa, claves de acceso de AWS, token de Docker Hub.
- Los valores se generan con `secrets.token_urlsafe` (alfabeto seguro para URL), se guardan **solo en SSM Parameter Store** y los lee la propia instancia. El agente no los imprime.
- Para pasar valores entre comandos usa variables locales de PowerShell (no `$env:`) y libéralas al terminar.
- **Nunca uses `set -x`** en los scripts de User Data: imprimiría los secretos en el log de la instancia.
- `infra/evidencias/` va en `.gitignore`: el repositorio es **público**.

### 10.7 Control de costos y tiempo

- Con costo: ALB, instancias EC2 (`db-server`, 2 web, `api-server` y las del Auto Scaling), direcciones IPv4 públicas y el monitoreo detallado de CloudWatch. **Ejecuta y limpia el mismo día**; no dejes recursos corriendo entre sesiones sin avisar al usuario.
- Al cerrar cada fase con recursos AWS, informa cuántos hay activos y desde cuándo.
- Si el usuario pide detener todo, ejecuta la limpieza (`99-limpieza.ps1`) tras confirmar el alcance.

### 10.8 Entorno del usuario

- Windows con PowerShell. Python 3.14.7 (`python` y `py` apuntan a la misma instalación). Docker 29.6.1 y Compose v5.3.0 (Docker Desktop).
- AWS CLI v2 con el perfil `lab07` (prerrequisito del usuario).
- **Variables de entorno en PowerShell:** `$env:X = ...` **persiste en esa terminal** y ya contaminó una ejecución de `pytest` (`APP_MODE=api` dejó 34 pruebas fallando). Evita `$env:`; si es imprescindible, elimínala al terminar con `Remove-Item Env:X`.
- Si la activación del venv falla por la política de ejecución: `Set-ExecutionPolicy Bypass -Scope Process`.

### 10.9 Trampas conocidas

**De la app (etapa 2):**

| Trampa | Regla |
|---|---|
| SQLAlchemy 2.1 cambió su driver por defecto para `postgresql://` | La configuración normaliza a `postgresql+psycopg://` |
| `SERVER_ID` con caracteres no ASCII | Inválido: las cabeceras HTTP solo admiten ASCII. Usar `Backend 1 - 8081`, no `Backend 1 · 8081` |
| Decoradores pegados en una línea (`)@login_required`) | Verificar con `Select-String -Path app\*.py,app\blueprints\*.py -Pattern "\)@"` si se tocara código |
| Placeholders `<...>` olvidados en variables | La validación de arranque lo detecta: el contenedor se niega a iniciar |

**De la infraestructura:**

| Trampa | Regla |
|---|---|
| PostgreSQL 18: cambió la ruta de datos | Montar el volumen en **`/var/lib/postgresql`**, no en `/var/lib/postgresql/data` |
| El puerto 80 de Windows puede estar ocupado | Publicar Nginx en `8080:80` y documentarlo |
| Recargar Nginx con un backend detenido | Falla (`host not found in upstream`). No recargar con un backend caído |
| Tras `docker compose start`, un backend puede recibir otra IP | Nginx resolvió los nombres al cargar: `nginx -s reload` lo corrige |
| Un contenedor detenido no *rechaza* conexiones: su IP deja de responder | Por eso `proxy_connect_timeout 2s`. Las primeras peticiones que toquen al backend caído tardan ~2 s |
| Amazon Linux 2023 exige **IMDSv2** | Pedir un token antes de leer los metadatos. El AWS CLI viene preinstalado; Docker se instala con `dnf install -y docker` |
| El User Data corre **solo en el primer arranque** | El contenedor debe usar `--restart unless-stopped`; tras `stop/start` de la EC2 vuelve solo |
| Tras `stop/start` de una EC2 cambia la IP pública, no la privada | Por eso `db-server` tiene IP privada fija |
| Target Groups: el health check debe ser `/health` (sin sesión) y aceptar `200` | `/` devuelve `302` y marcaría los targets como no saludables |
| El ALB no recorta prefijos | La instancia de API recibe `/api/...` completo |
| Referencias entre Security Groups | Usar el SG como origen (no CIDR) para 8000 y 5432; borrarlos en orden inverso de dependencia |
| Instancias `t3`: créditos de CPU en modo *unlimited* por defecto | Evitar cargas prolongadas fuera del Ejercicio 5 |
| Auto Scaling con *target tracking* | El escalado hacia afuera tarda unos minutos y **el escalado hacia adentro hasta ~15 min**: no es una falla |
| SSM `SecureString` | Si `get-parameter --with-decryption` falla por KMS, añadir `kms:Decrypt` sobre la clave `aws/ssm` al rol |
| Docker Hub | El repositorio debe ser **público** para que las EC2 hagan `pull` sin credenciales |

---

## 11. Infraestructura — especificación de la etapa 3

### 11.1 Imagen de la aplicación

**Contrato de la imagen** (el agente puede mejorar el `Dockerfile` sin romperlo):

| Requisito | Valor |
|---|---|
| Base | `python:3.14-slim` (no Alpine; sin multi-stage: no hay etapa de compilación) |
| Usuario | No root (`uid 10001`) |
| Puerto | 8000 (gunicorn) |
| Workers | `WEB_CONCURRENCY`, por defecto 2, ajustable con `-e` sin reconstruir |
| Configuración | Solo por variables de entorno; sin `.env` dentro de la imagen |
| Logs | Salida estándar |
| `HEALTHCHECK` | `GET /health` |
| Contenido | `wsgi.py`, `app/`, `migrations/` (para poder ejecutar `flask db upgrade` y `flask seed` con la misma imagen) |
| Arranque sin `SECRET_KEY` o `DATABASE_URL` | El contenedor **se niega a iniciar** (diseño intencional) |

**Contenido de referencia** (`infra/docker/Dockerfile`; ya creado por el usuario):

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WEB_CONCURRENCY=2

WORKDIR /app

# El proceso no corre como root
RUN useradd --system --uid 10001 --no-create-home appuser

# Dependencias primero: esta capa solo se reconstruye si cambia requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser wsgi.py .
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
```

`infra/docker/Dockerfile.dockerignore` excluye: `.git`, `.gitignore`, `.env`, `.env.*`, `venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `tests/`, `infra/`, `*.md`, `pytest.ini`, `requirements-dev.txt`. Se construye con la raíz del repo como contexto: `docker build -f infra/docker/Dockerfile -t lab07:dev .` (BuildKit lee `Dockerfile.dockerignore` junto al Dockerfile; **el contexto debe medir KB, no cientos de MB**).

**Publicación:** repositorio **público** en Docker Hub, etiqueta de versión inmutable (`<usuario>/lab07:v1.0.0`), **nunca** `latest` para la app. Se verifica con un `docker pull` desde cero.

### 11.2 Parte A — local, en el PC del usuario (Docker Compose)

```
Navegador / curl / ab
      │  http://localhost  (8080 si el 80 está ocupado)
      ▼
Docker Compose (red lab07_default)
  nginx:alpine :80 ── upstream (RR / weight / max_fails / ip_hash / least_conn)
      ├─► backend1  127.0.0.1:8081  SERVER_ID="Backend 1 - 8081"
      ├─► backend2  127.0.0.1:8082  SERVER_ID="Backend 2 - 8082"
      └─► backend3  127.0.0.1:8083  SERVER_ID="Backend 3 - 8083"
            │  (misma imagen, DETRAS_DE_PROXY=1)
            ▼
      db  postgres:18-alpine (volumen pgdata)    migrate: tarea única (flask db upgrade && flask seed)
```

**Archivos de referencia** (el agente los valida con Docker real y los corrige si hace falta):

`infra/compose/docker-compose.yml`

```yaml
name: lab07

# Plantilla común de los 3 backends (misma imagen, distinto SERVER_ID)
x-backend: &backend
  image: lab07:dev
  pull_policy: never          # usa solo la imagen local; error claro si no existe
  restart: unless-stopped
  depends_on:
    migrate:
      condition: service_completed_successfully
  environment: &backend-env
    SECRET_KEY: ${SECRET_KEY:?Define SECRET_KEY en infra/compose/.env}
    DATABASE_URL: postgresql://lab07:lab07@db:5432/lab07
    DETRAS_DE_PROXY: "1"      # detrás de Nginx: confiar en X-Forwarded-*

services:
  db:
    image: postgres:18-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: lab07
      POSTGRES_PASSWORD: lab07          # solo para uso local
      POSTGRES_DB: lab07
    volumes:
      - pgdata:/var/lib/postgresql      # PostgreSQL 18+: se monta el directorio padre
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lab07 -d lab07"]
      interval: 5s
      timeout: 3s
      retries: 10

  # Tarea de una sola ejecución: crea el esquema y el usuario demo, y termina.
  # Así ningún backend migra al arrancar (evita carreras entre réplicas).
  migrate:
    image: lab07:dev
    pull_policy: never
    command: ["sh", "-c", "flask db upgrade && flask seed"]
    environment:
      SECRET_KEY: ${SECRET_KEY:?Define SECRET_KEY en infra/compose/.env}
      DATABASE_URL: postgresql://lab07:lab07@db:5432/lab07
    depends_on:
      db:
        condition: service_healthy
    restart: "no"

  backend1:
    <<: *backend
    environment:
      <<: *backend-env
      SERVER_ID: "Backend 1 - 8081"
    ports:
      - "127.0.0.1:8081:8000"

  backend2:
    <<: *backend
    environment:
      <<: *backend-env
      SERVER_ID: "Backend 2 - 8082"
    ports:
      - "127.0.0.1:8082:8000"

  backend3:
    <<: *backend
    environment:
      <<: *backend-env
      SERVER_ID: "Backend 3 - 8083"
    ports:
      - "127.0.0.1:8083:8000"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    depends_on:
      backend1: {condition: service_healthy}
      backend2: {condition: service_healthy}
      backend3: {condition: service_healthy}
    ports:
      - "80:80"                         # si el 80 está ocupado en tu PC, usa "8080:80"
    volumes:
      - ../nginx/conf.d:/etc/nginx/conf.d:ro

volumes:
  pgdata:
```

`infra/nginx/conf.d/balanceador.conf` (la configuración **activa**, montada como directorio en `/etc/nginx/conf.d`):

```nginx
# ACTIVA: Round Robin (predeterminado)
upstream backend_pool {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://backend_pool;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Detección rápida de un backend caído y paso al siguiente
        proxy_connect_timeout 2s;
        proxy_next_upstream error timeout;
    }
}
```

**Variantes** (`infra/nginx/variantes/`): son el mismo archivo con otro bloque `upstream`. Se activan con `Copy-Item ..\nginx\variantes\<x>.conf ..\nginx\conf.d\balanceador.conf -Force` y `docker compose exec nginx nginx -s reload`.

| Archivo | Bloque `upstream` |
|---|---|
| `roundrobin.conf` | Los 3 `server backendN:8000;` sin parámetros |
| `pesos.conf` | `weight=5`, `weight=3`, `weight=2` |
| `failover.conf` | `max_fails=2 fail_timeout=15s` en los tres |
| `iphash.conf` | `ip_hash;` + los 3 servidores |
| `leastconn.conf` | `least_conn;` + los 3 servidores |

**Pruebas y resultados esperados.** Los valores se verificaron con backends simulados (Nginx 1.24); con Docker real pueden variar los tiempos, no el reparto:

| Prueba | Procedimiento | Resultado esperado |
|---|---|---|
| Arranque | `docker compose up -d`; `docker compose ps` | `db` y los 3 backends `healthy`; `migrate` en `Exited (0)`; `nginx` arriba |
| Round Robin | 9 × `GET /whoami` | 3 / 3 / 3 |
| Sesión a través del balanceador | Iniciar sesión por Nginx (`demo@lab07.pe` / `Demo1234!`) y crear 4–5 productos | La columna "Creado por" muestra **≥ 2 backends distintos** y la sesión no se cae |
| **Ej. 1** pesos | `pesos.conf`; 100 × `/whoami` | **50 / 30 / 20** |
| `ip_hash` | 30 × `/whoami` desde el mismo origen | Todas al mismo backend |
| `least_conn` | 30 × `/whoami` secuenciales | ≈ 10 / 10 / 10 |
| **Ej. 2** failover | `failover.conf`; `docker compose stop backend2`; 20 × `/whoami`; `docker compose start backend2`; esperar ~20 s | **0 errores**, solo backends 1 y 3 mientras está caído; backend 2 reaparece (si no, `nginx -s reload`) |
| **Ej. 3** carga | `docker run --rm --network lab07_default httpd:alpine ab -n 1000 -c 50 http://backend1:8000/whoami` y el mismo contra `http://nginx/whoami` | Registrar *Requests per second*, *Time per request* y *Failed requests*. Si `ab` no existe en `alpine`, usar `httpd:2.4` |

Anotar en el análisis del Ejercicio 3 que `ab`, Nginx y los backends **comparten la CPU** del mismo PC.

### 11.3 Parte B — red y cómputo en AWS (`us-east-2`)

```
Internet → ALB alb-lab-web (sg-alb-lab: 80 desde Internet) · Listener HTTP:80
   ├─ prioridad 10: /api/* → tg-lab-api (:8000, /health) → api-server   (APP_MODE=api)
   └─ por defecto          → tg-lab-web (:8000, /health) → web-server-1 (us-east-2a)
                                                         → web-server-2 (us-east-2b)
                                                         → asg-lab-web  (Ejercicio 5)
VPC vpc-lab-lb 10.0.0.0/16 · 2 subredes públicas · IGW · sin NAT · sin VPC endpoints
db-server (10.0.1.10, us-east-2a): postgres:18-alpine · 5432 solo desde sg-web-lab
```

| Recurso | Especificación |
|---|---|
| VPC `vpc-lab-lb` | `10.0.0.0/16`, DNS hostnames habilitado |
| Subredes | `subnet-lab-a` `10.0.1.0/24` (`us-east-2a`) y `subnet-lab-b` `10.0.2.0/24` (`us-east-2b`); ambas con asignación automática de IPv4 pública |
| Internet Gateway `igw-lab` | Adjunto a la VPC |
| Tabla de rutas `rt-lab-public` | `0.0.0.0/0` → `igw-lab`; asociada a ambas subredes |
| `sg-alb-lab` | Entrada: `80/tcp` desde `0.0.0.0/0` |
| `sg-web-lab` (web, API y Auto Scaling) | Entrada: `8000/tcp` desde `sg-alb-lab` y `8000/tcp` desde la IP pública del usuario `/32` (verificación directa; obtenerla con `https://checkip.amazonaws.com`). **Sin SSH** |
| `sg-db-lab` | Entrada: `5432/tcp` **solo desde `sg-web-lab`**. Nada desde Internet |
| EC2 | AMI de Amazon Linux 2023 x86_64 resuelta con el parámetro público `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`. Tipo **elegible para el free tier** (comprobar con `describe-instance-types --filters Name=free-tier-eligible,Values=true`; `t2.micro` o `t3.micro` según la cuenta). Perfil de instancia `profile-lab07-ec2`. IMDSv2 obligatorio. **Sin key pair**. Etiqueta `Project=lab07` |
| `db-server` | `subnet-lab-a`, IP privada fija **`10.0.1.10`**, `sg-db-lab`, User Data `db.sh` |
| `web-server-1` / `web-server-2` | `subnet-lab-a` / `subnet-lab-b`, `sg-web-lab`, User Data `web.sh` (`APP_MODE=web`, `LOAD_TEST=0`) |
| `api-server` | `subnet-lab-a`, `sg-web-lab`, User Data `web.sh` con `APP_MODE=api` |

**Acceso a las instancias:** sin SSH ni key pairs. Se usa **SSM Session Manager y Run Command** (el rol incluye `AmazonSSMManagedInstanceCore`; las instancias tienen IP pública para alcanzar los endpoints de SSM y Docker Hub sin NAT). Para depurar un User Data fallido: `aws ec2 get-console-output` o `aws ssm send-command` con `AWS-RunShellScript`.

### 11.4 IAM y parámetros SSM

- **Rol** `role-lab07-ec2` (confianza: `ec2.amazonaws.com`) y **perfil de instancia** `profile-lab07-ec2`.
- Política administrada `AmazonSSMManagedInstanceCore`.
- Política en línea `lab07-ssm-read` (mínimo privilegio):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ssm:GetParameter", "ssm:GetParameters"],
    "Resource": "arn:aws:ssm:us-east-2:<ID_DE_CUENTA>:parameter/lab07/*"
  }]
}
```

- Parámetros `SecureString` (generados por el agente con `secrets.token_urlsafe`, nunca impresos):

| Parámetro | Valor |
|---|---|
| `/lab07/SECRET_KEY` | ≥ 32 caracteres; **el mismo** para todas las instancias, incluidas las del Auto Scaling |
| `/lab07/POSTGRES_PASSWORD` | Contraseña de la base |
| `/lab07/DATABASE_URL` | `postgresql://lab07:<contraseña>@10.0.1.10:5432/lab07` |

### 11.5 Scripts de User Data (referencia)

`infra/aws/userdata/web.sh` (plantilla; el agente sustituye `__IMAGE__`, `__APP_MODE__` y `__LOAD_TEST__`):

```bash
#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/lab07-userdata.log) 2>&1     # NUNCA usar "set -x": imprimiría los secretos

REGION="us-east-2"
IMAGE="__IMAGE__"            # <usuario>/lab07:v1.0.0
APP_MODE="__APP_MODE__"      # web | api
LOAD_TEST="__LOAD_TEST__"    # 0 | 1 (1 solo en el Ejercicio 5)

dnf install -y docker
systemctl enable --now docker

ssm() {  # lee un parámetro con reintentos
  for i in 1 2 3 4 5; do
    aws ssm get-parameter --region "$REGION" --name "$1" --with-decryption \
      --query Parameter.Value --output text && return 0
    sleep 5
  done
  return 1
}

# IMDSv2: pedir un token antes de leer los metadatos
TOKEN=$(curl -fsS -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
IID=$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
AZ=$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)

SECRET_KEY=$(ssm /lab07/SECRET_KEY)
DATABASE_URL=$(ssm /lab07/DATABASE_URL)

docker run -d --name lab07 --restart unless-stopped -p 8000:8000 \
  -e SECRET_KEY="$SECRET_KEY" -e DATABASE_URL="$DATABASE_URL" \
  -e SERVER_ID="$IID - $AZ" -e APP_MODE="$APP_MODE" -e LOAD_TEST="$LOAD_TEST" \
  -e DETRAS_DE_PROXY=1 -e WEB_CONCURRENCY=2 "$IMAGE"
```

`infra/aws/userdata/db.sh`:

```bash
#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/lab07-userdata.log) 2>&1

REGION="us-east-2"
dnf install -y docker
systemctl enable --now docker

PGPASS=$(aws ssm get-parameter --region "$REGION" --name /lab07/POSTGRES_PASSWORD --with-decryption --query Parameter.Value --output text)

docker run -d --name lab07-db --restart unless-stopped -p 5432:5432 \
  -e POSTGRES_USER=lab07 -e POSTGRES_PASSWORD="$PGPASS" -e POSTGRES_DB=lab07 \
  -v lab07-pgdata:/var/lib/postgresql postgres:18-alpine
```

> El volumen nombrado `lab07-pgdata` sobrevive a la recreación del contenedor, **no** a la terminación de la instancia. `db-server` es un **punto único de falla** (D18).

**Migración y seed (D22):** se ejecutan **desde dentro de la VPC**, con SSM Run Command sobre `db-server` y la misma imagen. El comando espera a que la base responda (`docker exec lab07-db pg_isready -U lab07 -d lab07`), lee los secretos de SSM en la propia instancia y ejecuta `docker run --rm --network host -e SECRET_KEY=... -e DATABASE_URL=postgresql://lab07:...@127.0.0.1:5432/lab07 <imagen> sh -c "flask db upgrade && flask seed"`. Los valores nunca viajan en el texto del comando.

### 11.6 Target Groups y ALB

| Recurso | Especificación |
|---|---|
| `tg-lab-web` | HTTP, puerto 8000, destino por instancia; health check `GET /health`, esperado `200`, umbrales 2/2, intervalo 30 s, timeout 5 s |
| `tg-lab-api` | Igual que `tg-lab-web` (`/health` existe también en modo `api`) |
| `alb-lab-web` | Application Load Balancer, *internet-facing*, IPv4, subredes `subnet-lab-a` y `subnet-lab-b`, `sg-alb-lab` |
| Listener `HTTP:80` | Acción por defecto: reenviar a `tg-lab-web` |
| Regla (Ejercicio 4) | Prioridad **10**, condición ruta `/api/*`, reenviar a `tg-lab-api` |

**Failover (Parte B):** detener `web-server-1` (`aws ec2 stop-instances`), esperar ~1 minuto, comprobar que `tg-lab-web` lo marca `unhealthy` y que 10 peticiones al ALB responden solo desde `web-server-2`; reiniciarlo y comprobar que vuelve a `healthy` (el contenedor arranca solo por `--restart unless-stopped`).

### 11.7 Auto Scaling (Ejercicio 5)

| Recurso | Especificación |
|---|---|
| Launch Template `lt-lab-web` | Misma AMI y tipo; perfil `profile-lab07-ec2`; `sg-web-lab`; User Data `web.sh` con `APP_MODE=web` y **`LOAD_TEST=1`** (solo en la versión del Ejercicio 5); **monitoreo detallado habilitado**; IMDSv2 obligatorio; etiquetas `Project=lab07` en instancia y volumen |
| Auto Scaling Group `asg-lab-web` | Mínimo 2, deseada 2, máximo 4; subredes a y b; adjunto a `tg-lab-web`; tipo de health check **ELB**; periodo de gracia **300 s**; etiqueta `Project=lab07` propagada |
| Política | *Target tracking* sobre `ASGAverageCPUUtilization`, objetivo **50 %** |

**Procedimiento:**

1. **Antes** de crear el ASG, retirar `web-server-1` y `web-server-2` de `tg-lab-web` y **detenerlas** (`stop-instances`, no terminarlas): así el grupo refleja solo lo que gestiona el ASG, siguen visibles en la consola y el máximo en ejecución es 6.
2. Generar carga desde el PC del usuario: `docker run --rm httpd:alpine ab -t 600 -c 100 http://<DNS-del-ALB>/carga` (`-t` limita la duración; si las instancias no pasan del 50 % de CPU, subir `-c`, no el código).
3. Cada 60 s registrar `describe-auto-scaling-groups` y `describe-scaling-activities` hasta que haya **≥ 3 instancias en servicio** o pasen 15 minutos.
4. Detener `ab`. Esperar el escalado hacia adentro (**hasta ~15–20 min**: es normal) y registrar cuándo vuelve a 2.
5. Guardar las métricas de CloudWatch: `AWS/EC2` `CPUUtilization` (dimensión `AutoScalingGroupName`) y `AWS/ApplicationELB` `RequestCount`, con `get-metric-statistics`, periodo 60 s.
6. **Retirar `LOAD_TEST=1`** (D7): o bien se procede a la limpieza, o bien se crea una versión nueva del Launch Template sin esa variable y se lanza un *instance refresh*.

### 11.8 Recursos con costo

| Recurso | Cantidad máxima |
|---|---|
| Application Load Balancer | 1 |
| Instancias EC2 en ejecución | Hasta 6: `db-server` + `api-server` + hasta 4 del ASG. En el Ejercicio 5, `web-server-1/2` pasan a **detenidas** (no cuentan como en ejecución) |
| IPv4 públicas | 1 por instancia |
| Monitoreo detallado de CloudWatch | Instancias del ASG |
| Sin costo | VPC, subredes, IGW, rutas, Security Groups, IAM, parámetros SSM estándar |

### 11.9 Criterios de aceptación por fase

| Fase | Verificación |
|---|---|
| **I1** | Build correcto, contexto en KB; contenedor `healthy`; `/whoami` y `/health` (con `X-Servidor`) correctos; `docker exec <c> id` → `uid=10001`; **sin** `SECRET_KEY` el contenedor se niega a iniciar con un mensaje claro; `docker pull` de `<usuario>/lab07:v1.0.0` desde cero funciona y arranca |
| **I2–I3** | Tabla de 11.2 completa, con los resultados reales anotados en `infra/RESULTADOS.md` |
| **I4** | `describe-*` confirma VPC, subredes, rutas, IGW y los 3 SG **exactamente** como en 11.3 (ningún `0.0.0.0/0` salvo el 80 de `sg-alb-lab`; ningún 22 ni 5432 abierto a Internet); los 3 parámetros existen como `SecureString`; rol y perfil creados |
| **I5** | `db-server` en ejecución; la migración y el seed se ejecutaron (`Running upgrade`, usuario demo creado); `psql \dt` (vía SSM) lista `usuarios`, `productos` y `alembic_version`; el 5432 no es alcanzable desde Internet |
| **I6** | 2 targets `healthy`; 10 × `GET http://<ALB>/whoami` muestran **ambas** instancias; iniciar sesión **a través del ALB** (con *cookie jar* y token CSRF) y hacer 10 × `GET /` → todos `200`, con `X-Servidor` de **ambas** instancias; failover y recuperación de 11.6 |
| **I7** | `/` y `/whoami` → instancias web; `/api/test` → `API SERVER · <id> - <az>` (de `api-server`); `/api/productos` **sin** cookie → `401` JSON; **con la cookie de una sesión iniciada por el ALB** → `200` JSON con `servidor` = `api-server` (sesión válida entre Target Groups) |
| **I8** | Línea de tiempo del Auto Scaling (≥ 3 instancias en servicio y regreso a 2), métricas guardadas |
| **I9** | `RESULTADOS.md`, `RUNBOOK.md`, `GUIA-CAPTURAS.md` y README actualizados; tras la limpieza, **cero recursos** (ver 11.10) |

### 11.10 Limpieza

`infra/aws/99-limpieza.ps1` existe desde I4, es **idempotente** (ignora lo que ya no existe), **lista lo que va a eliminar y exige `-Confirmar`**. Orden:

1. Auto Scaling Group (borrado forzado) y espera a que sus instancias terminen.
2. Reglas del listener, listener y ALB (esperar a que se elimine).
3. Target Groups.
4. Instancias EC2 (`db-server`, web, `api-server`) y espera a que terminen.
5. Launch Template.
6. Security Groups, en este orden: `sg-db-lab`, `sg-web-lab`, `sg-alb-lab` (reintentar: la liberación de interfaces de red demora).
7. Asociaciones de la tabla de rutas, `igw-lab` (desadjuntar y eliminar), subredes y VPC.
8. Perfil de instancia y rol IAM.
9. Parámetros SSM `/lab07/*`.

**Verificación final** (todas deben devolver vacío): consulta por etiqueta `Project=lab07`, instancias en estado distinto de `terminated`, ALB, Auto Scaling Groups, VPC con la etiqueta, parámetros bajo `/lab07`, y `iam get-role` → `NoSuchEntity`. La imagen de Docker Hub puede permanecer.

### 11.11 Nombres de recursos

`vpc-lab-lb` · `subnet-lab-a` · `subnet-lab-b` · `igw-lab` · `rt-lab-public` · `sg-alb-lab` · `sg-web-lab` · `sg-db-lab` · `db-server` · `web-server-1` · `web-server-2` · `api-server` · `tg-lab-web` · `tg-lab-api` · `alb-lab-web` · `lt-lab-web` · `asg-lab-web` · `role-lab07-ec2` · `profile-lab07-ec2`

### 11.12 Entregables del agente en la etapa 3

| Archivo | Contenido |
|---|---|
| `infra/RESULTADOS.md` | Resultados medidos: Ej. 1 (conteos), Ej. 2 (bitácora antes/durante/después), Ej. 3 (tabla de `ab`), Parte B (reparto del ALB, failover), Ej. 4 (salidas de `curl` y diagrama Mermaid del ruteo), Ej. 5 (línea de tiempo y métricas) |
| `infra/RUNBOOK.md` | Cómo reconstruir todo desde cero y **por qué** se tomó cada decisión (el usuario quería aprender DevOps: que el documento enseñe) |
| `infra/GUIA-CAPTURAS.md` | Lista exacta de las capturas de la **consola de AWS** que debe tomar el usuario y **en qué momento** (antes de la limpieza) |
| `infra/aws/*.ps1` y `infra/aws/userdata/*.sh` | Scripts por fase, con variables comunes en `00-config.ps1` (sin secretos ni ID de cuenta) |
| `infra/evidencias/` | Salidas de la CLI y logs (**no se versiona**) |
| `README.md` | Reemplazar la sección "Despliegue contra Neon" por cómo ejecutar la Parte A y cómo desplegar en AWS |

---

## 12. Registro de decisiones

| # | Decisión | Motivo |
|---|---|---|
| D1 | Flask + plantillas Jinja, sin frontend separado | Menos piezas; despliegue en contenedor directo |
| D2 | Flask-SQLAlchemy + Flask-Migrate | ORM y consultas parametrizadas por defecto |
| D3 | Sesión en cookie firmada | Válida en cualquier instancia con el mismo `SECRET_KEY` |
| D4 | Base compartida por todas las instancias de cada topología (Neon descartado: ver D16) | Todas las instancias ven los mismos datos |
| D5 | `/health` sin base | Una caída de la base no marca todos los targets como no saludables |
| D6 | `/whoami` y cabecera `X-Servidor` | Balanceo verificable con `curl`, incluso en redirecciones y errores |
| D7 | `/carga` solo con `LOAD_TEST=1` e iteraciones configurables | Generar CPU para el Auto Scaling sin dejar una puerta permanente a DoS |
| D8 | API de solo lectura; `/api/test` y `/api/health` públicos | El `curl` del Ejercicio 4 funciona sin credenciales; datos protegidos |
| D9 | `servidor_origen` inmutable + `servidor_actualizacion` | Evidencia de escrituras de distintos servidores sobre el mismo registro |
| D10 | Infraestructura con Docker; archivos en `infra/`, escritos por el agente (antes: por el usuario; ver D19) | Arranque reproducible del Auto Scaling |
| D11 | Pruebas contra PostgreSQL 18 local, nunca contra una base compartida o de producción | Mismo motor que producción, aislado y desechable |
| D12 | Configuración construida en `create_app()` con overrides | Pruebas multi-instancia en un solo proceso |
| D13 | `SERVER_ID` ASCII | Las cabeceras HTTP no admiten caracteres fuera de ASCII |
| D14 | `DETRAS_DE_PROXY` desactivado por defecto | Confiar en `X-Forwarded-*` sin proxy permitiría falsificarlas |
| D15 | Secretos en SSM Parameter Store en AWS (`SECRET_KEY`, contraseña y URL de la base) | En User Data quedarían visibles en la plantilla de lanzamiento |
| D16 | **Neon descartado.** PostgreSQL 18 en contenedor (`postgres:18-alpine`) en todos los entornos | El usuario prefirió una base propia; elimina la dependencia externa |
| D17 | Parte A: servicio `db` en el Compose del PC del usuario | La topología local queda autocontenida |
| D18 | Parte B: EC2 `db-server` con IP privada fija `10.0.1.10`, volumen nombrado en `/var/lib/postgresql` y `sg-db-lab` (5432 solo desde `sg-web-lab`) | Base compartida por las instancias web y las del Auto Scaling. **Punto único de falla aceptado** |
| D19 | **La etapa 3 la ejecuta el agente de punta a punta**, con compuertas de aprobación (G1–G4) | Decisión del usuario; reemplaza la decisión original de hacerla manualmente |
| D20 | Perfil AWS dedicado `lab07`, región única `us-east-2`, etiqueta `Project=lab07` y registro de recursos | Limita el alcance del agente y hace exacta la limpieza |
| D21 | Sin SSH ni key pairs: acceso a las instancias por SSM (Session Manager y Run Command) | Menos superficie de ataque y menos piezas que gestionar |
| D22 | Migración y seed contra la base de AWS desde dentro de la VPC (SSM Run Command en `db-server`, misma imagen) | El 5432 nunca se expone a Internet |
| D23 | Imagen en Docker Hub, repositorio público, etiqueta de versión inmutable (`v1.0.0`) | Las EC2 hacen `pull` sin credenciales y el Auto Scaling lanza siempre la versión probada |
| D24 | `infra/evidencias/` fuera del control de versiones; capturas de la consola y video, del usuario | El repositorio es público; el agente no tiene sesión en la consola |
| D25 | Se mantiene el diseño completo: VPC propia `vpc-lab-lb` y secretos en SSM (se retiró la propuesta de atajos) | Decisión del usuario |
| D26 | El Ejercicio 5 (Auto Scaling) se incluye; en él `web-server-1/2` pasan a detenidas | Respeta el tope de 6 instancias en ejecución |

---

## 13. Checklist del laboratorio

- [x] Etapa 2: criterio de terminado (9.7) y ronda R1
- [ ] **I0** Prerrequisitos y estado verificados · **G1**
- [ ] **I1** Imagen validada y publicada en Docker Hub (`v1.0.0`)
- [ ] **I2** Parte A: Compose + Nginx (Round Robin) y sesión a través del balanceador
- [ ] **I3** Ejercicio 1 (pesos 5/3/2) · Ejercicio 2 (`max_fails`/`fail_timeout`) · Ejercicio 3 (`ab`) · **G2**
- [ ] **I4** AWS base: VPC, subredes, rutas, Security Groups, rol IAM, parámetros SSM, scripts
- [ ] **I5** `db-server`, migración y seed desde la VPC
- [ ] **I6** Parte B: 2 EC2, `tg-lab-web`, ALB y prueba de failover
- [ ] **I7** Ejercicio 4: `api-server`, `tg-lab-api` y regla `/api/*`
- [ ] **G3** · **I8** Ejercicio 5: Launch Template, Auto Scaling y carga con `/carga`
- [ ] **I9** `RESULTADOS.md`, `RUNBOOK.md`, `GUIA-CAPTURAS.md`, README · **G4** · limpieza y verificación de cero recursos
- [ ] *(usuario)* Capturas de la consola de AWS, video, informe y 3 conclusiones del GLAB-S07

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
| 2026-09-30 | **Ronda R1 (correcciones posteriores a F9), 4 puntos, un commit cada uno:** **(1)** `app/blueprints/auth.py`: el `before_app_request` que cargaba `g.usuario` corría en toda petición del modo `web`, incluidas las rutas públicas, consultando la base en cuanto había cookie de sesión — con la base inalcanzable, `/health` devolvía 500 en vez de 200 (D5 y 7.1 violadas). Reemplazado por `usuario_actual()`, perezoso y cacheado en `g`, que nada invoca por defecto; solo lo llaman `login_required` y las plantillas. Al verificar el fix se encontró y corrigió una regresión propia: `usuario_actual()` también se invoca al renderizar una página de error (404/500) en modo `api` cuando no es bajo `/api/`, y sin distinguir el modo intentaba enlazar a `auth.logout` (inexistente ahí) si llegaba una cookie de sesión `web` válida — ahora devuelve `None` sin tocar la base cuando `APP_MODE != "web"`. Aclarada la sección 9.4. **(2)** `pytest.ini`: `pytest` a secas fallaba con `ModuleNotFoundError: No module named 'app'` en un clon limpio (reproducido); solo funcionaba `python -m pytest`. Se agregó `pythonpath = .` y `addopts = --cov=app --cov-report=term-missing --cov-fail-under=90`; `--no-cov` (pytest-cov 7.1.0) se comporta como se esperaba para correr una sola prueba sin el umbral de cobertura. Aclarada la sección 9.7 y el README. **(3)** `tests/conftest.py` solo leía `TEST_DATABASE_URL` de `os.environ`. Se agregó `resolver_test_database_url()`: variable de entorno → `.env` (con `dotenv_values()`, sin `load_dotenv()` ni tocar el entorno) → error claro si falta en ambas; el rechazo de `neon.tech` se aplica al valor resuelto. Al exponerlo como variable global de módulo salió a la luz que pytest cargaba `tests/conftest.py` dos veces (como `conftest` y como `tests.conftest`, por la combinación de la falta de `tests/__init__.py` con el nuevo `pythonpath = .`), cada una con su propio estado; se agregó `tests/__init__.py` para unificarlas. Aclarada la sección 9.2 y el README (exportar la variable pasa a ser opcional). **(4)** `connect_args: {"connect_timeout": 10}` agregado a `SQLALCHEMY_ENGINE_OPTIONS` (sección 8.3): sin él, un intento de conexión con la base inalcanzable dependía del timeout del sistema operativo. **Cierre:** 152 pruebas, 0 fallos, 0 omitidas; cobertura 99.70 % (`pytest --cov=app --cov-fail-under=90`, vía `addopts`); verificado también sin exportar `TEST_DATABASE_URL` (respaldo desde `.env`). Ningún hueco adicional encontrado fuera de la regresión del punto 1, ya corregida dentro del mismo punto. |
| 2026-10-01 | **Neon descartado (D16).** Decisiones D17 y D18 sobre dónde corre PostgreSQL en cada parte. Imagen `lab07:dev` construida y probada por el usuario (266 MB en disco, `healthy`, `/whoami` y `/health` correctos). Paquete de la Parte A (Compose + Nginx) entregado por el asistente: semántica de Nginx verificada con backends simulados; sin ejecutar con Docker. |
| 2026-10-01 | **Especificación de la etapa 3 para el agente.** La etapa 3 pasa de manual a delegada (D19). Reescritas las secciones 2, 3, 10, 11 y 13; actualizadas la 4, 5, 6, 8, 9 y 12; nueva sección 15 (limitaciones conocidas). Decisiones D16–D26. |
| 2026-10-01 | **I0 cerrada.** Verificados: Docker 29.6.1 / Compose v5.3.0 (coincide con la sección 4); AWS CLI v2 instalado (`aws-cli/2.36.6`); `infra/docker/Dockerfile` y `Dockerfile.dockerignore` presentes, contenido idéntico a la referencia de 11.1; `pytest` a secas → 152 pruebas, cero fallos, cobertura 99,70 % (etapa 2 sigue verde). **Bloqueada en la compuerta G1**, faltan 3 de 4 prerrequisitos: el perfil AWS `lab07` no existe (`aws configure list-profiles` solo lista `r2`), por lo que no se pudo ejecutar `aws sts get-caller-identity` ni verificar la alerta de presupuesto; `docker info` no reporta una sesión iniciada en Docker Hub. `infra/compose/` e `infra/nginx/` (paquete de la Parte A) **no están extraídos** en el repo, a diferencia de lo que la sección 3 anterior daba a entender — quedan pendientes para I2. Este `CONTEXT.md` (reescrito para la etapa 3) y `infra/docker/` quedan commiteados y pusheados al cierre de esta fase. |


---

## 15. Limitaciones conocidas

| # | Limitación | Estado |
|---|---|---|
| 1 | Con una cookie de sesión válida y la base inalcanzable, `GET /` muestra la página 500 **por defecto de Werkzeug** (en inglés, sin estilo) en vez de la propia (verificado a mano por el usuario el 2026-09-30), y esa respuesta posiblemente no lleve `X-Servidor`. **Causa probable**, a partir del punto (1) de R1: `usuario_actual()` es perezoso y lo invocan las plantillas; al renderizar `base.html` dentro del manejador del 500 vuelve a consultar la base caída, la excepción se repite dentro del manejador y Flask cae a la página por defecto. `/health` sí responde `ok` en esas condiciones (verificado a mano) | Abierta. No bloquea la etapa 3. **Corrección propuesta** (requiere aprobación: la app está congelada): que `usuario_actual()` no consulte la base cuando se invoca desde un manejador de error, con su prueba (cookie válida + base inalcanzable + ruta que falla → página 500 propia con `X-Servidor`). Si aparece durante las pruebas de la etapa 3, **reportar** |
| 2 | La suite de pruebas depende de variables de entorno exportadas en la terminal (`APP_MODE`, `SERVER_ID`…). Con `APP_MODE=api` fallaron 34 pruebas | Abierta. Ejecutar `pytest` en una terminal limpia. Mejora pendiente: una *fixture* que las elimine antes de cada prueba |
| 3 | La cookie de sesión no es `Secure`: el ALB solo expone HTTP | Aceptada |
| 4 | `db-server` es un punto único de falla | Aceptada (D18) |
| 5 | PostgreSQL sin TLS; el tráfico viaja dentro de la VPC | Aceptada |
| 6 | Los secretos pasados con `docker run -e` son visibles con `docker inspect` en la propia instancia | Aceptada |
| 7 | El `README.md` y `.env.example` aún mencionan Neon | A corregir en I9 |