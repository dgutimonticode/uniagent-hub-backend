from io import BytesIO
from posixpath import basename

from app.extensions import db
from app.models.agente import Agente
from app.models.skill import Skill
from app.repositories import skill_repository
from app.services.exceptions import S3ServiceError, SkillServiceError
from app.services.s3_service import s3_service
from app.utils.slugify import slugify


_MARKDOWN_CONTENT_TYPE = "text/markdown"


def get_by_agente(agente_id: int) -> list[Skill]:
    return skill_repository.find_by_agente(agente_id)


def get_by_id(skill_id: int) -> Skill:
    skill = skill_repository.find_by_id(skill_id)
    if skill is None:
        raise SkillServiceError("SKILL_NOT_FOUND", "Skill no existe", 404)
    return skill


def get_content(skill_id: int) -> str:
    skill = get_by_id(skill_id)
    raw = s3_service.download_file(skill.s3_key)
    return raw.decode("utf-8")


def create(agente: Agente, data: dict) -> Skill:
    nombre = data["nombre"]
    descripcion = data.get("descripcion")
    contenido = data.get("contenido") or ""

    if skill_repository.find_by_agente_and_nombre(agente.id, nombre) is not None:
        raise SkillServiceError(
            "DUPLICATE_SKILL_NAME",
            "Ya existe una skill con ese nombre en este agente",
            409,
        )

    slug = slugify(nombre)
    s3_key = f"{agente.s3_prefix}/{slug}.md"

    encoded = contenido.encode("utf-8")
    s3_service.upload_file(BytesIO(encoded), s3_key, _MARKDOWN_CONTENT_TYPE)

    try:
        skill = skill_repository.create(
            {
                "agente_id": agente.id,
                "nombre": nombre,
                "descripcion": descripcion,
                "s3_key": s3_key,
                "tamano_kb": _calc_tamano_kb(encoded),
                "orden": 0,
            }
        )
    except Exception:
        db.session.rollback()
        _delete_s3_best_effort(s3_key)
        raise

    # TODO: publicar evento SQS (ASL futuro)
    return skill


def update(skill: Skill, data: dict) -> Skill:
    nuevo_nombre = data.get("nombre")
    nuevo_contenido = data.get("contenido")
    nueva_descripcion = data.get("descripcion")

    updates: dict = {}
    if nueva_descripcion is not None:
        updates["descripcion"] = nueva_descripcion

    nombre_cambia = nuevo_nombre is not None and nuevo_nombre != skill.nombre
    contenido_cambia = nuevo_contenido is not None

    if nombre_cambia:
        if (
            skill_repository.find_by_agente_and_nombre(skill.agente_id, nuevo_nombre)
            is not None
        ):
            raise SkillServiceError(
                "DUPLICATE_SKILL_NAME",
                "Ya existe una skill con ese nombre en este agente",
                409,
            )

        prefix = skill.s3_key.rsplit("/", 1)[0] if "/" in skill.s3_key else ""
        slug = slugify(nuevo_nombre)
        new_s3_key = f"{prefix}/{slug}.md" if prefix else f"{slug}.md"
        old_s3_key = skill.s3_key

        if contenido_cambia:
            body_bytes = nuevo_contenido.encode("utf-8")
        else:
            body_bytes = s3_service.download_file(old_s3_key)

        s3_service.upload_file(
            BytesIO(body_bytes), new_s3_key, _MARKDOWN_CONTENT_TYPE
        )
        _delete_s3_best_effort(old_s3_key)

        updates["nombre"] = nuevo_nombre
        updates["s3_key"] = new_s3_key
        updates["tamano_kb"] = _calc_tamano_kb(body_bytes)

    elif contenido_cambia:
        body_bytes = nuevo_contenido.encode("utf-8")
        s3_service.upload_file(
            BytesIO(body_bytes), skill.s3_key, _MARKDOWN_CONTENT_TYPE
        )
        updates["tamano_kb"] = _calc_tamano_kb(body_bytes)

    if updates:
        skill = skill_repository.update(skill, updates)

    # TODO: publicar evento SQS (ASL futuro)
    return skill


def delete(skill: Skill) -> None:
    try:
        s3_service.delete_file(skill.s3_key)
    except S3ServiceError as err:
        if err.code != "S3_NOT_FOUND":
            raise
    skill_repository.delete(skill)
    # TODO: publicar evento SQS (ASL futuro)


def get_presigned_url(skill_id: int, expiration: int = 900) -> dict:
    skill = get_by_id(skill_id)
    url = s3_service.generate_presigned_url(skill.s3_key, expiration=expiration)
    return {
        "url": url,
        "expires_in": expiration,
        "filename": basename(skill.s3_key),
    }


def _calc_tamano_kb(content: bytes) -> int:
    if not content:
        return 0
    return max(1, len(content) // 1024)


def _delete_s3_best_effort(s3_key: str) -> None:
    try:
        s3_service.delete_file(s3_key)
    except S3ServiceError:
        # best effort: log silently — orphan cleanup deferred to manual ops.
        pass
