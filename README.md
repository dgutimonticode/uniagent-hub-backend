# UniAgent Hub — Backend

Backend de UniAgent Hub. Plataforma universitaria de agentes IA.
**Materia:** COM610 — Infraestructura, Plataformas Tecnológicas y Redes | USFX

## Stack
Python 3.14 · Flask 3 · SQLAlchemy · JWT · MySQL 8 · AWS S3 · SQS · Docker · gunicorn

## Setup local

Antes que nada, creá tu archivo de variables de entorno a partir del template:

```bash
cp .env.example .env
# editá .env y reemplazá los placeholders (al menos SECRET_KEY y JWT_SECRET_KEY)
```

Luego levantá los contenedores:

```bash
docker compose up -d
docker compose exec api flask db upgrade
docker compose exec api flask seed
```

El API queda en `http://localhost:5000`. Health check: `GET /health`.

LocalStack (S3 + SQS mock) corre dentro del mismo compose. El bucket `uniagent-hub-skills` se crea con:

```bash
docker compose exec localstack awslocal s3 mb s3://uniagent-hub-skills
```

## Tests

```bash
source venv/bin/activate
pytest
```

## Deploy en EC2

Stack completo en la instancia: API + MySQL containerizados, S3 real para skills. La DB corre en un volumen nombrado `uniagent-db-data` persistente en la EC2. boto3 usa el IAM Role de la instancia para S3 — sin credenciales en disco.

```bash
# 1. SSH al EC2
ssh ec2-user@<EC2_IP>

# 2. Clonar el repo
git clone <REPO_URL>
cd uniagent-hub-backend

# 3. Crear el archivo de variables de entorno
cp .env.production.example .env.production

# 4. Editar con valores reales
nano .env.production

# 5. Levantar los contenedores
docker compose -f docker-compose.prod.yml up -d

# 6. Aplicar migraciones
docker compose -f docker-compose.prod.yml exec api flask db upgrade

# 7. Seed inicial
docker compose -f docker-compose.prod.yml exec api flask seed
```

### Variables de entorno requeridas en producción

Ver `.env.production.example` para el template completo.

| Variable | Descripción |
|----------|-------------|
| `FLASK_ENV` | Debe ser `production` |
| `SECRET_KEY` | Secret de Flask (mínimo 32 bytes). **Sin default — fail-fast si falta.** |
| `JWT_SECRET_KEY` | Secret para firmar JWTs (mínimo 32 bytes). **Sin default — fail-fast si falta.** |
| `DATABASE_URL` | `mysql+pymysql://uniagent_user:PASS@db:3306/uniagent` (`db` = nombre del servicio Docker) |
| `MYSQL_ROOT_PASSWORD` | Password del root de MySQL |
| `MYSQL_DATABASE` | Nombre de la base de datos (ej: `uniagent`) |
| `MYSQL_USER` | Usuario de la app |
| `MYSQL_PASSWORD` | Password del usuario de la app |
| `AWS_REGION` | Región del bucket S3. Ej: `us-east-1` |
| `AWS_S3_BUCKET` | Nombre del bucket. Ej: `uniagent-hub-skills-prod` |
| `CORS_ORIGINS` | Orígenes permitidos separados por coma. Ej: `https://uniagent.miuni.edu` |

> **Seguridad:** adjuntá un **IAM Instance Profile** a la EC2 con la policy mínima sobre el bucket. boto3 descubre las credenciales automáticamente vía IMDSv2 — no pongas `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` en `.env.production`.

## Docs
Ver `/docs` del repo raíz para arquitectura completa.
