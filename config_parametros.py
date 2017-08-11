import os
from app import app
from flask import flash, Markup, render_template, request, copy_current_request_context, session, redirect, url_for, g, Response, abort
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import time
import locale
from models import *
from forms import *
import csv
# ****************************************
# XXX: mail threading
import threading
from flask_mail import Mail, Message
from config_mail import *
from secrets import token_urlsafe
# ****************************************
import arrow
utc = arrow.utcnow()
# ****************************************
from statistics import mean
# ****************************************
import pandas as pd
# ****************************************
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
password = b"00bocata00"
salt_f = os.urandom(16)  # NOTE original: os.urandom(16)
iterations_f = 5  # NOTE original:100000
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                 length=32,  # NOTE no se puede reducir pues es un sistema 32bits
                 salt=salt_f,
                 iterations=iterations_f,
                 backend=default_backend()
                 )
key = base64.urlsafe_b64encode(kdf.derive(password))
f = Fernet(key)
# ****************************************
from hashids import Hashids
salt = '00bocata00'  # NOTE hay que mantenerlo constante para poder generar junto con el token un mismo id-token para cada informe y luego poder recuperarlo
# hashids = Hashids(salt=salt, min_length=16)
# salt = str(os.urandom(16))  # NOTE se generera nuevo random cada vez que se reinicia el servidor (NO se puede usar debido al tutoria_id+token+asignatura_id almacenado en la base de datos)
hashids = Hashids(salt=salt)
# ****************************************
# NOTE sobre cryptography:
# todos los id fuera de una funcion iran como hashids_encode. Ejemplo: anchor_{{hashids_encode(alumno.id)}}
# todos los id dentro de una funcion iran tal cual se cogen del diccionario. Ejemplo: alumno_asignaturas(alumno.id) || equal_str(alumno.id, params['current_alumno_id'])
# redirect usar siempre params=dic_encode(params): Ejemplo: return redirect(url_for('alumnos_html', params=dic_encode(params)))
# render_template usar siempre params=params: Ejemplo return render_template('alumnos.html', params=params)
# ****************************************
# XXX Local_Host
# tutoria_email_link = 'http://localhost:5000/informe/'
# email_time_sleep = 3

# XXX Heroku_Host
tutoria_email_link = 'https://mitutoria.herokuapp.com/informe/'
email_time_sleep = 10
# ****************************************
# FIXME hay que buscar otra forma, estos contadores son compartidos por todos los usuarios.
# collapse_asignatura_edit_alumnos_contador = 0
# collapse_alumno_edit_asignaturas_contador = 0
# ****************************************


#
# parametros_fresh = ('current_alumno_id', 'current_tutoria_id', 'current_grupo_id',
#                     'current_cita_id', 'current_pregunta_id', 'current_user_id',
#                     'anchor', 'from_url', 'login', 'tutoria_edit_link',
#                     'tutoria_re_enviar_link', 'alumno_importar_link', 'alumno_delete_link',
#                     'asignatura_delete_link', 'tutoria_delete_link', 'grupo_delete_link',
#                     'cita_delete_link', 'pregunta_delete_link', 'user_delete_link',
#                     'alumno_edit_close', 'collapse_alumno', 'collapse_alumno_add',
#                     'collapse_alumno_edit', 'collapse_alumno_edit_asignaturas',
#                     'collapse_alumno_asignatura', 'collapse_tutoria_add', 'collapse_tutoria_add_enviar_a',
#                     'collapse_tutorias', 'collapse_tutorias_historial', 'collapse_tutoria_no_activa',
#                     'collapse_asignatura_add', 'collapse_asignatura_edit', 'collapse_grupo_add',
#                     'collapse_grupo_edit', 'collapse_cita_add', 'collapse_cita_edit',
#                     'collapse_pregunta_add', 'collapse_pregunta_edit', 'collapse_user_edit',
#                     )
#
params_default = {
    'anchor': 'anchor_top', 'from_url': False, 'login': False, 'tutoria_edit_link': False,
    'tutoria_re_enviar_link': False, 'alumno_importar_link': False, 'alumno_delete_link': False,
    'asignatura_delete_link': False, 'tutoria_delete_link': False, 'grupo_delete_link': False,
    'cita_delete_link': False, 'pregunta_delete_link': False, 'user_delete_link': False,
    'alumno_edit_close': False, 'collapse_alumno': False, 'collapse_alumno_add': False,
    'collapse_alumno_edit': False, 'collapse_alumno_edit_asignaturas': False,
    'collapse_alumno_asignatura': False, 'collapse_tutoria_add': False, 'collapse_tutoria_add_enviar_a': False,
    'collapse_tutorias': False, 'collapse_tutorias_historial': False, 'collapse_tutoria_no_activa': False,
    'collapse_asignatura_add': False, 'collapse_asignatura_edit': False, 'collapse_grupo_add': False,
    'collapse_grupo_edit': False, 'collapse_cita_add': False, 'collapse_cita_edit': False,
    'collapse_pregunta_add': False, 'collapse_pregunta_edit': False, 'collapse_user_edit': False,
    'current_alumno_id': 0, 'current_tutoria_id': 0, 'current_asignatura_id': 0, 'current_grupo_id': 0,
    'current_cita_id': 0, 'current_pregunta_id': 0, 'current_user_id': 0
}

# parametros_url = {
#     'anchor': 'par_00', 'from_url': 'par_01', 'login': 'par_02', 'tutoria_edit_link': 'par_03',
#     'tutoria_re_enviar_link': 'par_04', 'alumno_importar_link': 'par_05', 'alumno_delete_link': 'par_06',
#     'asignatura_delete_link': 'par_07', 'tutoria_delete_link': 'par_08', 'grupo_delete_link': 'par_09',
#     'cita_delete_link': 'par_10', 'pregunta_delete_link': 'par_11', 'user_delete_link': 'par_12',
#     'alumno_edit_close': 'par_13', 'collapse_alumno': 'par_14', 'collapse_alumno_add': 'par_15',
#     'collapse_alumno_edit': 'par_16', 'collapse_alumno_edit_asignaturas': 'par_17',
#     'collapse_alumno_asignatura': 'par_18', 'collapse_tutoria_add': 'par_19', 'collapse_tutoria_add_enviar_a': 'par_20',
#     'collapse_tutorias': 'par_21', 'collapse_tutorias_historial': 'par_22', 'collapse_tutoria_no_activa': 'par_23',
#     'collapse_asignatura_add': 'par_24', 'collapse_asignatura_edit': 'par_25', 'collapse_grupo_add': 'par_26',
#     'collapse_grupo_edit': 'par_27', 'collapse_cita_add': 'par_28', 'collapse_cita_edit': 'par_29',
#     'collapse_pregunta_add': 'par_30', 'collapse_pregunta_edit': 'par_31', 'collapse_user_edit': 'par_32'
# }
