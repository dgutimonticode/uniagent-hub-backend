# UniAgent Hub — Backend

Backend de UniAgent Hub. Plataforma universitaria de agentes IA.
**Materia:** COM610 — Infraestructura, Plataformas Tecnológicas y Redes | USFX

## Stack
Python 3.11 · Flask 3 · SQLAlchemy · JWT · MySQL 8 · AWS S3 · SQS · Docker

## Setup local
```bash
docker compose up -d
docker compose exec api flask db upgrade
docker compose exec api flask seed
```

## Docs
Ver `/docs` del repo raíz para arquitectura completa.
