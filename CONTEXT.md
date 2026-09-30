# CONTEXT.md — Lab07: App LOGIN + CRUD con Balanceo de Carga

> **Para cualquier agente o sesión nueva:** lee este archivo completo antes de cualquier tarea. Es la fuente de verdad del proyecto. Al terminar cada paso, actualiza la sección **3. Estado actual**, el **Registro de tiempos** (sección 12) y agrega una entrada en el **Changelog** (sección 14). Si algo que te pidan contradice una decisión de la sección 5, detente y consúltalo antes de cambiarla.

---

## 1. Resumen

| Campo | Valor |
|---|---|
| Laboratorio | GLAB-S07 — "Diseñar un entorno", curso *Desarrollo de Soluciones en la Nube*, Tecsup |
| Requerimiento | Aplicación **LOGIN + CRUD** servida detrás de un **balanceador de carga**, en dos topologías: local (Nginx + 3 backends) y AWS (ALB + EC2 en 2 zonas) |
| Alcance | Parte A + Parte B + los 5 ejercicios de la guía `Laboratorio_Balanceador_de_Carga.md` |
| Entidad del CRUD | `productos` |
| Repositorio | **público** |
| Autor | Diego Nina |

---

## 2. Etapas

| # | Etapa | Estado |
|---|---|---|
| 1 | Planificación | ✅ Cerrada |
| 2 | Desarrollo | ⏳ En curso |
| 3 | Despliegue / Producción (Parte A, Parte B, Ejercicios 1–5, limpieza) | ⏳ Pendiente |

---

## 3. Estado actual

- Planificación cerrada: stack, modelo de datos, decisiones C1–C12 y arquitectura.
- **Siguiente paso:** crear el repositorio y subir este archivo como primer commit.

---

## 4. Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | **Python 3.13** en todos los entornos |
| Framework | Flask + plantillas Jinja (renderizado en servidor, sin frontend separado) |
| ORM / migraciones | Flask-SQLAlchemy + Flask-Migrate (Alembic) |
| Seguridad de formularios | Flask-WTF (CSRF) |
| Contraseñas | `werkzeug.security` (incluido en Flask) — **no usar passlib** |
| Sesión | Cookie firmada nativa de Flask (*stateless*, válida en cualquier backend con el mismo `SECRET_KEY`) |
| Base de datos | PostgreSQL en **Neon**, proyecto nuevo `lab07`, región `us-east-2` |
| Servidor de aplicación | gunicorn |
| Balanceo local | Nginx (en EC2 Ubuntu) |
| Balanceo en la nube | AWS Application Load Balancer (`us-east-2`) |
| Driver PostgreSQL | psycopg 3 (psycopg[binary]); SQLAlchemy ≥ 2.1 lo usa por defecto |

---

## 5. Decisiones de diseño (no cambiar sin consultar)

| # | Decisión | Motivo |
|---|---|---|
| C1 | `/whoami` público (identidad del servidor en texto plano). `/carga` público **solo** si `LOAD_TEST=1` | Los `curl` de los ejercicios necesitan distinguir backends sin login; `/carga` genera CPU para el Auto Scaling sin ser una puerta de DoS permanente |
| C2 | Públicos: `/api/test` y `/api/health`. Protegido: `/api/productos` (401 JSON sin sesión). API **solo lectura** | El `curl` del Ejercicio 4 funciona sin credenciales; los datos no quedan expuestos |
| C3 | CSRF con Flask-WTF en todos los formularios HTML; la API queda exenta | La API es solo GET |
| C4 | Proyecto **nuevo** en Neon (`lab07`, `us-east-2`) | Aislado de SecureDocs |
| C5 | Secretos en **SSM Parameter Store** (`SecureString`) + rol IAM para las EC2. Plan B: User Data | En User Data los secretos quedan visibles en la plantilla de lanzamiento |
| C6 | Python 3.13: local ya instalado (3.13.5); AL2023 con `dnf install python3.13`; Ubuntu con su Python 3 (≥ 3.13) | Misma versión en desarrollo y producción |
| C7 | Repositorio **público** | El User Data lo clona sin credenciales; no contiene secretos |
| C8 | gunicorn en el puerto **8000** en las EC2; Target Groups al 8000 | Evita correr la app como root |
| C9 | Dos Security Groups: `sg-alb-lab` (80 desde Internet) y `sg-web-lab` (8000 solo desde `sg-alb-lab` y tu IP; 22 desde tu IP) | Las EC2 no quedan expuestas a Internet |
| C10 | Backends de la Parte A como servicios `systemd` con plantilla (`lab07@8081`, `@8082`, `@8083`) | Detener/levantar un backend en el Ejercicio 2 de forma limpia |
| C11 | Retirar las 2 EC2 originales de `tg-lab-web` antes del Ejercicio 5 | El Target Group refleja solo lo que gestiona el Auto Scaling |
| C12 | Monitoreo **detallado** de CloudWatch en la plantilla de lanzamiento | Escalado observable en minutos, no en un cuarto de hora |

### Hechos técnicos aplicados

- **IMDSv2:** el User Data pide un token antes de leer el Instance ID y la zona (AL2023 lo exige).
- **Health checks** de los Target Groups en `/health` (existe en modo web y api; no toca la BD).
- **VPC "y más":** NAT Gateway *Ninguno*, sin VPC endpoints (evita costos por hora).
- **Neon:** URL siempre con `sslmode=require`; la app usa la URL con *pooler*; las migraciones se ejecutan con la URL **directa** (sin pooler).
- **Pool de conexiones** pequeño con `pool_pre_ping=True` (Neon cierra conexiones inactivas; con varios workers × varias instancias las conexiones se multiplican).
- **Auto Scaling:** health check tipo *ELB* con periodo de gracia ≥ 300 s.
- **Migraciones** generadas en local y versionadas en el repo. **Ninguna EC2 ejecuta `flask db migrate` ni `flask db upgrade`.**
- **Esquema y seed** se aplican una sola vez: `flask db upgrade` y luego `flask seed`.
- **Cookie de sesión:** `HttpOnly` y `SameSite=Lax`, **sin** `Secure` (el ALB solo expone HTTP). Limitación documentada.
- **Ejercicio 3:** `ab` corre en la misma máquina que los backends y compite por CPU; se deja explícito en el análisis.
- **Tipo de instancia:** el que la consola marque como *Free tier eligible* (`t2.micro` o `t3.micro`).
- **El ALB no recorta el prefijo:** la instancia de API recibe `/api/...` completo, por eso sus rutas se registran con prefijo `/api`.

---

## 6. Modelo de datos

| Tabla | Campos |
|---|---|
| `usuarios` | `id` (PK), `nombre`, `correo` (único), `password_hash`, `creado_en` |
| `productos` | `id` (PK), `nombre`, `precio` (Numeric 10,2), `stock` (int), `servidor_origen` (texto), `creado_en`, `actualizado_en` |

`servidor_origen` guarda qué backend atendió la creación: evidencia de que el balanceo reparte **y** de que la base de datos es compartida.

Usuario semilla: `demo@lab07.pe` / `Demo1234!` (solo pruebas).

---

## 7. Rutas de la aplicación

| Ruta | Acceso | Modo (`APP_MODE`) | Uso |
|---|---|---|---|
| `/login`, `/logout` | Público | web | Autenticación |
| `/` y `/productos/...` | Con sesión | web | CRUD de productos (CSRF) |
| `/health` | Público | web y api | Health checks |
| `/whoami` | Público | web y api | Identidad del servidor |
| `/carga` | Público solo con `LOAD_TEST=1` | web y api | Carga de CPU para el Ejercicio 5 |
| `/api/test`, `/api/health` | Público | api | Ruteo por path (Ejercicio 4) |
| `/api/productos` | Con sesión (401 JSON) | api | Lectura del CRUD en JSON |

Todas las páginas muestran en el pie **qué servidor respondió**.

---

## 8. Variables de entorno

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Firma de la cookie de sesión y CSRF. **Idéntica en todos los servidores** |
| `DATABASE_URL` | URL de Neon **con pooler**, `sslmode=require` |
| `SERVER_ID` | Identidad mostrada en el pie y en `/whoami` (local: `Backend 1 · 8081`; AWS: Instance ID + zona, generado por el User Data) |
| `APP_MODE` | `web` (por defecto) o `api` |
| `LOAD_TEST` | `1` solo durante el Ejercicio 5 |

En AWS, `SECRET_KEY` y `DATABASE_URL` se leen de SSM: `/lab07/SECRET_KEY`, `/lab07/DATABASE_URL`.

---

## 9. Arquitectura

### Parte A — Local (EC2 Ubuntu `ubuntu-Lab03`, Ejercicios 1–3)

```
Cliente (navegador / curl / ab)
      │ HTTP :80  (SG: 80 y 22 solo desde tu IP)
      ▼
Nginx :80 ── upstream backend_pool (RR / least_conn / ip_hash / weight · max_fails)
      ├─► lab07@8081  gunicorn  "Backend 1"
      ├─► lab07@8082  gunicorn  "Backend 2"
      └─► lab07@8083  gunicorn  "Backend 3"
                 │ SSL
                 ▼
        Neon · lab07 · us-east-2
```

### Parte B — AWS (Ejercicios 4–5)

```
Internet → ALB alb-lab-web (sg-alb-lab) · Listener HTTP:80
   ├─ prioridad 10: /api/*  → tg-lab-api (:8000, /health) → api-server (APP_MODE=api)
   └─ por defecto           → tg-lab-web (:8000, /health) → web-server-1 (us-east-2a)
                                                           → web-server-2 (us-east-2b)
                                                           → asg-lab-web (lt-lab-web, 2/2/4, CPU 50%)
VPC vpc-lab-lb 10.0.0.0/16 · 2 subredes públicas · IGW · sin NAT
EC2: sg-web-lab · rol IAM (lectura SSM) · User Data (python3.13, git clone, IMDSv2, gunicorn :8000)
Salida a Neon · lab07 · us-east-2
```

### Nombres de recursos AWS

`vpc-lab-lb` · `sg-alb-lab` · `sg-web-lab` · `web-server-1` · `web-server-2` · `api-server` · `tg-lab-web` · `tg-lab-api` · `alb-lab-web` · `lt-lab-web` · `asg-lab-web` · rol IAM de EC2 para SSM *(nombre por definir)*

---

## 10. Estructura prevista del repositorio

```
lab07/
├── CONTEXT.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── wsgi.py                  # punto de entrada para gunicorn
├── app/
│   ├── __init__.py          # create_app() + registro de blueprints según APP_MODE
│   ├── config.py
│   ├── extensions.py        # db, migrate, csrf
│   ├── models.py            # Usuario, Producto
│   ├── auth.py              # /login, /logout
│   ├── productos.py         # CRUD
│   ├── publico.py           # /health, /whoami, /carga
│   ├── api.py               # /api/*
│   ├── cli.py               # comando `flask seed`
│   └── templates/
├── migrations/              # generadas en local, versionadas
└── deploy/
    ├── nginx/balanceador.conf
    ├── systemd/lab07@.service
    └── userdata/            # scripts de arranque para EC2 web y api
```

La carpeta `deploy/` versiona toda la configuración de infraestructura, para que el despliegue sea reproducible y trazable.

---

## 11. Checklist del laboratorio

- [ ] Desarrollo: app funcionando en local contra Neon
- [ ] Parte A: Nginx + 3 backends (Round Robin)
- [ ] Ejercicio 1: pesos 5/3/2, 100 peticiones a `/whoami`
- [ ] Ejercicio 2: `max_fails` / `fail_timeout`, caída y recuperación de `lab07@8082`
- [ ] Ejercicio 3: `ab` directo vs. a través de Nginx
- [ ] Parte B: VPC, SGs, 2 EC2, Target Group, ALB, prueba de failover
- [ ] Ejercicio 4: `tg-lab-api` + regla `/api/*`
- [ ] Ejercicio 5: Launch Template + ASG + carga con `/carga`
- [ ] Limpieza de recursos AWS (ASG → ALB → Target Groups → EC2 → Launch Template → SGs → VPC) y detener la EC2 de la Parte A
- [ ] 3 conclusiones del GLAB-S07

---

## 12. Registro de tiempos

| Etapa / paso | Inicio | Fin | Duración | Notas |
|---|---|---|---|---|
| Planificación | | | | |
| Desarrollo | | | | |
| Parte A + Ejercicios 1–3 | | | | |
| Parte B + Ejercicio 4 | | | | |
| Ejercicio 5 | | | | |
| Limpieza | | | | |

---

## 13. Advertencias operativas

- **Máquina del instituto:** se borra al reiniciar. El venv y los paquetes se reinstalan en cada sesión; **push al cierre de cada paso**.
- Usar `python`, no `py`. Si la activación del venv falla: `Set-ExecutionPolicy Bypass -Scope Process`.
- **Costos:** el ALB y las instancias del Auto Scaling cobran por hora. La limpieza se hace el mismo día.

---

## 14. Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-30 | Planificación cerrada: alcance completo, stack Flask + Flask-SQLAlchemy + Neon, decisiones C1–C12, arquitectura Parte A/B. Se crea este CONTEXT.md. |
| 2026-09-30 | Estructura base (create_app, config, extensiones, endpoints públicos). Driver cambiado a psycopg 3. Blueprint público registrado en ambos modos. |