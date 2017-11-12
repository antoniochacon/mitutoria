from wtforms import Form, StringField, TextField, PasswordField, BooleanField, validators, DateField, DateTimeField, IntegerField, ValidationError, HiddenField
from wtforms.fields.html5 import EmailField
from wtforms.ext.django.fields import QuerySetSelectField
import datetime

from flask import g


class User_Add (Form):
    username = StringField('usuario', [validators.Required(message='usuario es obligatorio'),
                                       validators.length(min=4, message='usuario debe tener minimo 4 caracteres'),
                                       validators.length(max=25, message='usuario debe tener maximo 25 caracteres')])

    password = PasswordField('password',
                             [validators.Required(message='password es obligatorio'),
                              validators.length(min=6, message='password debe tener minimo 7 caracteres'),
                              validators.length(max=80, message='password debe tener maximo 25 caracteres')])

    email = EmailField('email', [validators.Required(message='email es obligatorio'),
                                 validators.Email(message='Escriba una direccion valida de email'),
                                 validators.length(max=120, message='email debe tener maximo 120 caracteres')])


class Password_Reset_Request (Form):
    username = StringField('usuario', [validators.Required(message='usuario es obligatorio'),
                                       validators.length(min=4, message='usuario debe tener minimo 4 caracteres'),
                                       validators.length(max=25, message='usuario debe tener maximo 25 caracteres')])

    email = EmailField('email', [validators.Required(message='email es obligatorio'),
                                 validators.Email(message='Escriba una direccion valida de email'),
                                 validators.length(max=120, message='email debe tener maximo 120 caracteres')])


class Password_Reset (Form):
    password = PasswordField('password',
                             [validators.Required(message='password es obligatorio'),
                              validators.length(min=6, message='password debe tener minimo 7 caracteres'),
                              validators.length(max=80, message='password debe tener maximo 25 caracteres')])


class Usuario_Edit (Form):
    username = StringField('usuario', [validators.Required(message='usuario es obligatorio'),
                                       validators.length(min=4, message='usuario debe tener minimo 4 caracteres'),
                                       validators.length(max=25, message='usuario debe tener maximo 25 caracteres')])
    password = PasswordField('password',
                             [validators.length(max=80, message='password debe tener maximo 25 caracteres')])
    email = EmailField('email', [validators.Required(message='email es obligatorio'),
                                 validators.Email(message='Escriba una direccion valida de email'),
                                 validators.length(max=120, message='email debe tener maximo 120 caracteres')])
    email_validated = BooleanField('email validado')
    email_robinson = BooleanField('lista Robinson')
    show_asignaturas_analisis = BooleanField('evolucion asignaturas')
    role = StringField('role', [validators.length(min=3, message='role debe tener minimo 3 caracteres'),
                                validators.length(max=80, message='role debe tener maximo 25 caracteres')])
    ban = BooleanField('ban')

    current_usuario_id = HiddenField('current_usuario_id')


class User_Login (Form):
    username = StringField('usuario', [validators.Required(message='usuario es obligatorio'),
                                       validators.length(min=4, message='usuario debe tener minimo 4 caracteres'),
                                       validators.length(max=25, message='usuario debe tener maximo 25 caracteres')])

    password = PasswordField('password', [validators.Required(message='password es obligatorio'),
                                          validators.length(min=6, message='password debe tener minimo 7 caracteres'),
                                          validators.length(max=80, message='password debe tener maximo 25 caracteres')])
    remember = BooleanField('recuerdame')


class Grupo_Add (Form):
    nombre = StringField('grupo', [validators.Required(message='el nombre grupo es obligatorio'),
                                              validators.length(min=3, message='el nombre grupo debe tener minimo 3 caracteres'),
                                              validators.length(max=80, message='el nombre grupo debe tener maximo 80 caracteres')])

    tutor_nombre = StringField('tutor nombre', [validators.Required(message='el nombre del tutor es obligatorio')])
    tutor_apellidos = StringField('tutor apellidos', [validators.Required(message='los apellidos del tutor son obligatorios')])

    centro = StringField('centro', [validators.length(min=3, message='centro debe tener minimo 3 caracteres'),
                                    validators.length(max=80, message='centro debe tener maximo 25 caracteres')])
    curso_academico = HiddenField('curso_academico')
    current_grupo_id = HiddenField('current_grupo_id')


class Alumno_Add (Form):
    nombre = StringField('nombre', [validators.Required(message='el nombre es obligatorio'),
                                    validators.length(min=3, message='el nomre debe tener minimo 3 caracteres'),
                                    validators.length(max=80, message='el nombre debe tener maximo 80 caracteres')])
    apellidos = StringField('apellidos', [validators.Required(message='los apellidos son obligatorios'),
                                          validators.length(min=3, message='los apellidos deben tener minimo 3 caracteres'),
                                          validators.length(max=80, message='los apellidos deben tener maximo 80 caracteres')])
    current_alumno_id = HiddenField('current_alumno_id')


class Asignatura_Add (Form):
    grupo_id = HiddenField('grupo_id')
    asignatura = StringField('asignatura', [validators.Required(message='la asignatura es obligatoria'),
                                            validators.length(min=3, message='la asignatura debe tener minimo 3 caracteres'),
                                            validators.length(max=80, message='la asignatura debe tener maximo 80 caracteres')])
    nombre = StringField('nombre del docente', [validators.Required(message='el nombre es obligatorio'),
                                                validators.length(min=3, message='el nomre debe tener minimo 3 caracteres'),
                                                validators.length(max=80, message='el nombre debe tener maximo 80 caracteres')])
    apellidos = StringField('apellidos del docente', [validators.length(min=3, message='los apellidos deben tener minimo 3 caracteres'),
                                                      validators.length(max=80, message='los apellidos deben tener maximo 80 caracteres')])

    email = EmailField('email del docente', [validators.Required(message='email es obligatorio'),
                                             validators.Email(message='Escriba una direccion valida de email'),
                                             validators.length(max=120, message='email debe tener maximo 120 caracteres')])
    current_asignatura_id = HiddenField('current_asignatura_id')


class Tutoria_Add (Form):
    current_alumno_id = HiddenField('current_alumno_id')
    fecha = DateTimeField('fecha', [validators.Required(message='la fecha es obligatoria')])
    hora = DateTimeField('hora',  [validators.Required(message='la hora es obligatoria')])
    current_tutoria_id = HiddenField('current_tutoria_id')


class Cita_Add (Form):
    frase = StringField('frase', [validators.Required(message='frase es obligatoria')])
    autor = StringField('autor', [validators.Required(message='autor es obligatorio')])
    current_cita_id = HiddenField('current_cita_id')


class Invitado_Informe (Form):
    email = StringField('email', [validators.Required(message='indica las 5 primeras letras de tu email'),
                                  validators.length(min=5, message='indica al menos las 5 primeras letras de tu email')])
    tutoria_id = HiddenField('tutoria_id')
    asignatura_id = HiddenField('asignatura_id')


class Pregunta_Add (Form):
    enunciado = StringField('enunciado', [validators.Required(message='enunciado es obligatorio')])
    enunciado_ticker = StringField('ticker', [validators.Required(message='ticker es obligatorio')])
    categoria_id = IntegerField('categoria', [validators.Required(message='categoria es obligatoria')])
    orden = IntegerField('orden', [validators.Required(message='orden es obligatorio')])
    visible = BooleanField('visible')
    active_default = BooleanField('active_default')
    current_pregunta_id = HiddenField('current_pregunta_id')


class Categoria_Add (Form):
    enunciado = StringField('categoria', [validators.Required(message='categoria es obligatoria')])
    color = StringField('color', [validators.Required(message='color es obligatorio')])
    orden = IntegerField('orden', [validators.Required(message='orden es obligatorio')])
    current_categoria_id = HiddenField('current_categoria_id')
