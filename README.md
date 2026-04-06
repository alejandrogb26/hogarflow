# 🏠 HogarFlow

**Gestión de la economía del hogar** — aplicación web server-rendered con Flask, Jinja2, SQLAlchemy, MariaDB, Tailwind CSS, Alpine.js y Chart.js.

---

## Decisiones de arquitectura destacadas

### ¿Se guarda el saldo en base de datos?

**No.** El saldo se calcula siempre como `SUM(amount)` sobre todos los movimientos. Esto garantiza coherencia absoluta: editar o borrar cualquier movimiento se refleja automáticamente en el saldo sin ninguna lógica de sincronización. Para un hogar con miles de movimientos el coste de la consulta es despreciable. Si en el futuro la app escala a millones de filas se puede añadir una vista materializada o un campo cacheado con triggers, pero sería optimización prematura hoy.

### ¿Flask-WTF o validación manual?

**Validación manual.** Los formularios son simples (3-4 campos cada uno) y Flask-WTF añadiría una dependencia extra sin aportar valor proporcional. Las funciones de validación son legibles, testeables y fáciles de extender.

### ¿Paginación en movimientos?

**Sí**, paginación de 20 ítems por página. El listado tiene además filtro por mes/año y por categoría, lo que en la práctica hace que el usuario nunca llegue a la paginación en uso normal.

### ¿Borrado de categorías con movimientos?

**Bloqueo con mensaje claro.** Borrar silenciosamente o reasignar corrompería datos históricos. El usuario recibe un mensaje informativo que le indica cuántos movimientos tiene la categoría.

### ¿Seeds de categorías?

**Sí**, comando `flask seed` con 12 categorías representativas de un hogar real.

---

## Estructura del proyecto

```
hogarflow/
├── run.py                  # Punto de entrada + CLI commands
├── config.py               # Configuraciones dev/prod/test
├── requirements.txt
├── .env.example
├── .gitignore
└── app/
    ├── __init__.py         # App factory
    ├── models.py           # Modelos SQLAlchemy (Category, Movement)
    ├── utils.py            # Filtros Jinja + queries de negocio
    ├── blueprints/
    │   ├── main.py         # Dashboard
    │   ├── movements.py    # CRUD de movimientos
    │   ├── categories.py   # CRUD de categorías
    │   └── errors.py       # Manejadores 404/500
    ├── templates/
    │   ├── base.html       # Layout base + navegación inferior
    │   ├── main/
    │   │   └── dashboard.html
    │   ├── movements/
    │   │   ├── index.html
    │   │   └── form.html
    │   ├── categories/
    │   │   ├── index.html
    │   │   └── form.html
    │   ├── components/
    │   │   ├── page_header.html
    │   │   ├── movement_row.html
    │   │   ├── confirm_delete.html
    │   │   └── empty_chart.html
    │   └── errors/
    │       ├── 404.html
    │       └── 500.html
    └── static/             # (reservado para assets compilados)
```

---

## Requisitos previos

- Python 3.10+
- MariaDB 10.6+ (o MySQL 8+)
- pip

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd hogarflow
```

### 2. Crear y activar entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear base de datos en MariaDB

```sql
CREATE DATABASE hogarflow_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hogarflow'@'localhost' IDENTIFIED BY 'hogarflow';
GRANT ALL PRIVILEGES ON hogarflow_dev.* TO 'hogarflow'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tu SECRET_KEY y DATABASE_URL si es necesario
```

### 6. Crear las tablas (migraciones)

```bash
flask db init        # Solo la primera vez (crea carpeta migrations/)
flask db migrate -m "initial schema"
flask db upgrade
```

### 7. (Opcional) Cargar categorías de ejemplo

```bash
flask seed
```

### 8. Ejecutar la aplicación

```bash
flask run
# o
python run.py
```

Abre **http://localhost:5000** en el navegador.

---

## Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `FLASK_ENV` | Entorno activo | `development` |
| `FLASK_APP` | Módulo de arranque | `run.py` |
| `SECRET_KEY` | Clave para sesiones y CSRF | string aleatorio |
| `DATABASE_URL` | Cadena de conexión SQLAlchemy | `mysql+pymysql://user:pass@host/db` |

---

## Comandos útiles

```bash
# Abrir shell interactivo con contexto de la app
flask shell

# Crear nueva migración tras modificar modelos
flask db migrate -m "descripcion del cambio"
flask db upgrade

# Cargar categorías de ejemplo
flask seed

# Ver rutas registradas
flask routes
```

---

## Pantallas de la aplicación

| Ruta | Descripción |
|---|---|
| `/` | Dashboard: saldo, KPIs, gráficas, últimos movimientos |
| `/movimientos/` | Listado con filtros por mes y categoría |
| `/movimientos/nuevo` | Formulario de nuevo movimiento |
| `/movimientos/<id>/editar` | Formulario de edición |
| `/movimientos/<id>/borrar` | POST para borrar (con confirmación modal) |
| `/categorias/` | Listado de categorías |
| `/categorias/nueva` | Formulario de nueva categoría |
| `/categorias/<id>/editar` | Formulario de edición |
| `/categorias/<id>/borrar` | POST para borrar (bloqueado si tiene movimientos) |

---

## Convención de importes

- **Importe positivo** → ingreso (suma al saldo)
- **Importe negativo** → gasto (resta del saldo)

El tipo (ingreso/gasto) se infiere siempre del signo del importe, nunca hay un campo `type` separado. Esto simplifica el modelo y evita incoherencias.

---

## Gráficas implementadas

1. **Donut Ingresos vs Gastos** — visión global de toda la historia
2. **Barras por mes** — ingresos y gastos de los últimos 6 meses
3. **Donut gastos por categoría** — desglose del mes actual

---

## Despliegue en producción

```bash
# Variables mínimas necesarias
export FLASK_ENV=production
export SECRET_KEY=<clave-segura>
export DATABASE_URL=mysql+pymysql://...

# Aplicar migraciones pendientes
flask db upgrade

# Servir con Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

Se recomienda poner Nginx como reverse proxy delante de Gunicorn.

---

## Posibles mejoras futuras

- **Presupuestos por categoría** con alertas al superar el límite
- **Exportación CSV/Excel** del historial de movimientos
- **Movimientos recurrentes** (domiciliaciones automáticas)
- **Multi-hogar / multi-usuario** con autenticación Flask-Login
- **Notificaciones push** para recordatorios
- **API REST** para integración con apps nativas
- **Tests automáticos** con pytest y pytest-flask
- **Build de Tailwind** con CLI para purgar CSS no usado en producción
- **Modo PWA** para instalación en móvil como app nativa
