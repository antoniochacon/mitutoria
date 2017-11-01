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
# XXX: google api
import httplib2
from apiclient import errors, discovery
from oauth2client import client
from oauth2client import tools
import json  # NOTE necesario para google API
# ****************************************
# XXX: mail threading
import threading
# ****************************************
import arrow
utc = arrow.utcnow()
# ****************************************
from statistics import mean, mode
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
# email_validate_link = 'http://localhost:5000/email_validate/'
# index_link = 'http://localhost:5000/'
# password_reset_link = 'http://localhost:5000/password_reset/'
# email_time_sleep = 3


# XXX Heroku_Host
tutoria_email_link = 'https://mitutoria.herokuapp.com/informe/'
email_validate_link = 'https://mitutoria.herokuapp.com/email_validate/'
index_link = 'https://mitutoria.herokuapp.com/'
password_reset_link = 'https://mitutoria.herokuapp.com/password_reset/'
email_time_sleep = 3
