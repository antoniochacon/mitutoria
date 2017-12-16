from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Date, text, desc, DateTime, Boolean, Time, desc, DECIMAL
from sqlalchemy.orm import sessionmaker, relationship, backref, scoped_session
from sqlalchemy.sql import func, or_, and_
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.sql.functions import ReturnTypeFromArgs
# **************************************
import random
import datetime
# **************************************
from config import Server_Config
engine = create_engine(Server_Config.engine_url, echo=False)
# **************************************
# create a configured Session_SQL class
Session_SQL = sessionmaker(bind=engine)
Base = declarative_base()
# create a Session_SQL
Session_SQL = sessionmaker() # NOTE linea original
# Session_SQL = scoped_session(Session_SQL)  # NOTE scoped_session es la recomendada para web apps
Session_SQL.configure(bind=engine)
session_sql = Session_SQL()


class User (UserMixin, Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    password = Column(String(80))
    email = Column(String(120), unique=True)
    settings = relationship('Settings', uselist=False, back_populates='user', cascade='delete')


class Settings (Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='settings')
    oauth2_credentials = Column(String)
    email_validated = Column(Boolean, default=False)
    email_validated_intentos = Column(Integer, default=1)
    email_robinson = Column(Boolean, default=False)
    role = Column(String(80), default='user')
    ban = Column(Boolean, default=False)
    calendar = Column(Boolean, default=False)
    calendar_sincronizado = Column(Boolean, default=False)
    cleanup_tutorias_status = Column(Boolean, default=False)
    tutoria_duracion = Column(Integer, default=20)
    tutoria_timeout = Column(Boolean, default=True)
    show_asignaturas_analisis = Column(Boolean, default=True)
    diferencial = Column(Integer, default=15)
    show_analisis_detalles = Column(Boolean, default=False)
    show_analisis_preguntas_splines = Column(Boolean, default=False)
    show_analisis_asignaturas_splines = Column(Boolean, default=False)
    show_analisis_detallado_por_asignatura = Column(Boolean, default=False)
    grupo_activo_id = Column(Integer)
    asignaturas_orden = Column(Boolean, default=True)
    grupos = relationship('Grupo', backref='settings', lazy='dynamic', cascade='delete')
    preguntas = relationship('Association_Settings_Pregunta', cascade='delete')
    created_at = Column(DateTime, default=datetime.datetime.now())
    edited_at = Column(DateTime, default=datetime.datetime.now())
    visit_last = Column(DateTime, default=datetime.datetime.now())
    visit_number = Column(Integer, default=1)


class Settings_Global (Base):
    __tablename__ = 'settings_global'
    id = Column(Integer, primary_key=True)
    oauth2_credentials = Column(String)
    gmail_sender = Column(String(120))
    diferencial_default = Column(Integer, default=15)  # %
    periodo_participacion_recent = Column(Integer, default=30)  # dias
    periodo_cleanup_tutorias = Column(Integer, default=3)  # meses
    periodo_deleted_tutorias = Column(Integer, default=15)  # dias
    cleanup_tutorias_automatic = Column(Boolean, default=False)


class Grupo (Base):
    __tablename__ = 'grupo'
    id = Column(Integer, primary_key=True)
    settings_id = Column(Integer, ForeignKey('settings.id'))
    nombre = Column(String(80))
    tutor_nombre = Column(String(80))
    tutor_apellidos = Column(String(80))
    curso_academico = Column(Integer)
    centro = Column(String(80))
    alumnos = relationship('Alumno', backref='grupo', lazy='dynamic', cascade='delete')
    asignaturas = relationship('Asignatura', backref='grupo', lazy='dynamic', cascade='delete')
    created_at = Column(DateTime, default=datetime.datetime.now())


class Pregunta (Base):
    __tablename__ = 'pregunta'
    id = Column(Integer, primary_key=True)
    enunciado = Column(String)
    enunciado_ticker = Column(String)  # evita enunciados largo en eje X de los graficos
    orden = Column(Integer)
    visible = Column(Boolean, default=False)  # Controla la visibilidad hacia los usuarios
    active_default = Column(Boolean, default=False)  # controla las preguntas activas por defecto estaran activas para un nuevo usuario. Al crear nuevo usuario, habra que insertar estas preguntas en su preguntas de settings
    categoria_id = Column(Integer, ForeignKey('categoria.id'))
    respuestas = relationship('Respuesta', backref='pregunta', lazy='dynamic', cascade='delete')
    created_at = Column(DateTime, default=datetime.datetime.now())


class Categoria (Base):
    __tablename__ = 'categoria'
    id = Column(Integer, primary_key=True)
    enunciado = Column(String)
    color = Column(String, default='#343a40')
    orden = Column(Integer)
    preguntas = relationship('Pregunta', backref='categoria', lazy='dynamic', cascade='delete')


class Association_Settings_Pregunta (Base):
    __tablename__ = 'association_settings_pregunta'
    id = Column(Integer, primary_key=True)
    settings_id = Column(Integer, ForeignKey('settings.id'))
    pregunta_id = Column(Integer, ForeignKey('pregunta.id'))
    settings = relationship('Settings', backref=backref('pregunta_association_settings_pregunta', cascade='delete, delete-orphan'))
    pregunta = relationship('Pregunta', backref=backref('settings_association_settings_pregunta', cascade='delete, delete-orphan'))
    edited_at = Column(DateTime, default=datetime.datetime.now())


class Respuesta (Base):
    __tablename__ = 'respuesta'
    id = Column(Integer, primary_key=True)
    informe_id = Column(Integer, ForeignKey('informe.id'))
    pregunta_id = Column(Integer, ForeignKey('pregunta.id'))
    resultado = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())


class Prueba_Evaluable (Base):
    __tablename__ = 'prueba_evaluable'
    id = Column(Integer, primary_key=True)
    informe_id = Column(Integer, ForeignKey('informe.id'))
    nombre = Column(String(80))
    nota = Column(DECIMAL)
    created_at = Column(DateTime, default=datetime.datetime.now())


class Informe (Base):
    __tablename__ = 'informe'
    id = Column(Integer, primary_key=True)
    tutoria_id = Column(Integer, ForeignKey('tutoria.id'))
    asignatura_id = Column(Integer, ForeignKey('asignatura.id'))
    respuestas = relationship('Respuesta', backref='informe', lazy='dynamic', cascade='delete')
    pruebas_evaluables = relationship('Prueba_Evaluable', backref='informe', lazy='dynamic', cascade='delete')
    comentario = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())


class Alumno (Base):
    __tablename__ = 'alumno'
    id = Column(Integer, primary_key=True)
    grupo_id = Column(Integer, ForeignKey('grupo.id'))
    nombre = Column(String(80))
    apellidos = Column(String(80))
    tutorias = relationship('Tutoria', backref='alumno', lazy='dynamic', cascade='delete')
    asignaturas = relationship('Asignatura', secondary='association_alumno_asignatura', lazy='dynamic', passive_deletes=True, single_parent=True)
    created_at = Column(DateTime, default=datetime.datetime.now())


class Asignatura (Base):
    __tablename__ = 'asignatura'
    id = Column(Integer, primary_key=True)
    grupo_id = Column(Integer, ForeignKey('grupo.id'))
    asignatura = Column(String(80))
    nombre = Column(String(80))
    apellidos = Column(String(80))
    email = Column(String(120))
    informes = relationship('Informe', backref='asignatura', lazy='dynamic', cascade='delete')
    created_at = Column(DateTime, default=datetime.datetime.now())


class Association_Alumno_Asignatura (Base):
    __tablename__ = 'association_alumno_asignatura'
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey('alumno.id'))
    asignatura_id = Column(Integer, ForeignKey('asignatura.id'))
    alumno = relationship('Alumno', backref=backref('asignatura_alumno_asignatura', cascade='delete, delete-orphan'))
    asignatura = relationship('Asignatura', backref=backref('alumno_alumno_asignatura', cascade='delete, delete-orphan'))
    created_at = Column(DateTime, default=datetime.datetime.now())


class Tutoria (Base):
    __tablename__ = 'tutoria'
    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey('alumno.id'))
    fecha = Column(Date)
    hora = Column(Time)
    activa = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(Date)
    calendar_event_id = Column(String)
    acuerdo = Column(String)
    informes = relationship('Informe', backref='tutoria', lazy='dynamic', cascade='delete')
    created_at = Column(DateTime, default=datetime.datetime.now())


class Association_Tutoria_Asignatura (Base):
    __tablename__ = 'association_tutoria_asignatura'
    id = Column(Integer, primary_key=True)
    tutoria_id = Column(Integer, ForeignKey('tutoria.id'))
    asignatura_id = Column(Integer, ForeignKey('asignatura.id'))
    asignatura = relationship('Asignatura', backref=backref('tutoria_tutoria_asignatura', cascade='delete, delete-orphan'))
    tutoria = relationship('Tutoria', backref=backref('asignautra_tutoria_asignatura', cascade='delete, delete-orphan'))
    created_at = Column(DateTime, default=datetime.datetime.now())


class Cita (Base):
    __tablename__ = 'cita'
    id = Column(Integer, primary_key=True)
    frase = Column(String)
    autor = Column(String)
    visible = Column(Boolean, default=True)  # Controla la visibilidad hacia los usuarios
    created_at = Column(DateTime, default=datetime.datetime.now())
