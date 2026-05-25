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

## Producción (EC2)

Build de la imagen production-ready (multi-stage, gunicorn, usuario no-root):

```bash
docker build -t uniagent-back:prod .
```

Compose de producción (sin LocalStack, sin DB local — usa RDS y S3 reales):

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Variables de entorno requeridas en producción

| Variable | Descripción |
|----------|-------------|
| `APP_ENV` | Debe ser `production` |
| `SECRET_KEY` | Secret de Flask (mínimo 32 bytes). **Sin default — fail-fast si falta.** |
| `JWT_SECRET_KEY` | Secret para firmar JWTs (mínimo 32 bytes). **Sin default — fail-fast si falta.** |
| `JWT_ACCESS_TOKEN_EXPIRES_HOURS` | TTL del access token. Default: `24` |
| `DATABASE_URL` | Connection string a RDS. Ej: `mysql+pymysql://user:pass@rds-host:3306/uniagent` |
| `AWS_REGION` | Región AWS del bucket. Ej: `us-east-1` |
| `AWS_S3_BUCKET` | Nombre del bucket. Ej: `uniagent-hub-skills-prod` |
| `AWS_ACCESS_KEY_ID` | **Solo si NO usás IAM Instance Profile** (preferible omitir y usar el role) |
| `AWS_SECRET_ACCESS_KEY` | Idem |
| `SQS_SKILLS_QUEUE_URL` | URL completa de la cola SQS FIFO |
| `CORS_ORIGINS` | Lista separada por coma de orígenes permitidos. Ej: `https://uniagent.miuni.edu` |
| `AGENT_API_URL` | URL del agente IA on-premise |
| `AGENT_HMAC_SECRET` | Secret para firmar requests al agente |
| `CF_ACCESS_CLIENT_ID` | Cloudflare Access Service Token (ID) |
| `CF_ACCESS_CLIENT_SECRET` | Cloudflare Access Service Token (Secret) |

> **Recomendación de seguridad:** en EC2 adjuntá un **IAM Instance Profile** con la policy mínima sobre el bucket en vez de manejar `AWS_ACCESS_KEY_ID`/`SECRET_ACCESS_KEY` en disco. boto3 los descubre automáticamente vía IMDSv2.

## Docs
Ver `/docs` del repo raíz para arquitectura completa.
