from app.extensions import db
from app.models.materia import Materia
from app.models.usuario import Usuario


def seed_database() -> None:
    materias = [
        Materia(nombre='Física I', carrera='Ingeniería en Sistemas', semestre=1, icono='⚛️'),
        Materia(nombre='Cálculo I', carrera='Ingeniería en Sistemas', semestre=1, icono='📐'),
        Materia(nombre='Física II', carrera='Ingeniería en Sistemas', semestre=2, icono='🌊'),
        Materia(
            nombre='Infraestructura, Plataformas Tecnológicas y Redes',
            carrera='Ingeniería en Sistemas',
            semestre=6,
            icono='☁️',
        ),
    ]
    for m in materias:
        if not Materia.query.filter_by(nombre=m.nombre, carrera=m.carrera).first():
            db.session.add(m)
    db.session.commit()

    sis313 = Materia.query.filter_by(
        nombre='Infraestructura, Plataformas Tecnológicas y Redes'
    ).first()

    if not Usuario.query.filter_by(email='daniel@usfx.bo').first():
        docente = Usuario(
            nombre='Gutierrez Montiel Daniel Ivan',
            email='daniel@usfx.bo',
            rol=Usuario.ROL_DOCENTE,
            materia_id=sis313.id,
        )
        docente.set_password('test1234')
        db.session.add(docente)

    if not Usuario.query.filter_by(email='alumno@usfx.bo').first():
        alumno = Usuario(
            nombre='Estudiante de prueba',
            email='alumno@usfx.bo',
            rol=Usuario.ROL_ESTUDIANTE,
        )
        alumno.set_password('test1234')
        db.session.add(alumno)

    db.session.commit()
    print("✅ Seed completado")
