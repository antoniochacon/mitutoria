from app import app
from functions import *
import functions
# *************************************


@app.url_defaults  # Fuerza el reload de los archivos de static
def hashed_url_for_static_file(endpoint, values):
    if 'static' == endpoint or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if '.' in endpoint:  # has higher priority
                blueprint = endpoint.rsplit('.', 1)[0]
            else:
                blueprint = request.blueprint  # can be None too
            if blueprint:
                static_folder = app.blueprints[blueprint].static_folder
            else:
                static_folder = app.static_folder
            param_name = 'h'
            while param_name in values:
                param_name = '_' + param_name
            values[param_name] = static_file_hash(
                os.path.join(static_folder, filename))


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)


# (FIN) Fuerza el reload de los archivos de static
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_html'


@login_manager.user_loader
def load_user(user_id):
    return session_sql.query(User).get(int(user_id))


@app.before_request
def before_request_html():
    g.current_year = datetime.date.today().year
    g.current_date = datetime.date.today()
    g.current_time = datetime.datetime.now()
    g.current_user = current_user


@app.route('/getos')
def getos():
    return (os.name)


@app.errorhandler(404)
def page_not_found_html(warning):

    return render_template('page_not_found.html')


@app.route('/')
def index_html():
    return redirect(url_for('alumnos_html'))


@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets('static/credentials/client_secret.json', scope='https://www.googleapis.com/auth/calendar', redirect_uri=index_link + 'oauth2callback')
    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        settings().oauth2_credentials = credentials.to_json()
        session_sql.commit()
    return redirect(url_for('settings_opciones_html'))


@app.route('/calendar_api')
@login_required
def calendar_api_html():
    if settings().oauth2_credentials:
        try:
            credentials = oauth2client.client.Credentials.new_from_json(settings().oauth2_credentials)
            settings().oauth2_credentials = credentials.to_json()
            session_sql.commit()
            http = httplib2.Http()
            http = credentials.authorize(http)
            service = discovery.build('calendar', 'v3', http=http)
        except:
            return redirect(url_for('oauth2callback'))
    else:
        return redirect(url_for('oauth2callback'))

    event = {
        'summary': 'Tutoria',
        'location': grupo_activo().centro,
        'description': 'Evento creado por https://mitutoria.herokuapp.com/',
        'colorId': '3',
        'start': {
            'dateTime': '2017-09-10T09:00:00-07:00',
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': '2017-09-11T09:00:00-07:00',
            'timeZone': 'Europe/Madrid',
        }
    }
    event = service.events().insert(calendarId='primary', body=event).execute()

    return render_template('calendar_api.html')


@app.route('/admin_estadisticas', methods=['GET', 'POST'])
@app.route('/admin_estadisticas/<params>', methods=['GET', 'POST'])
@login_required
def admin_estadisticas_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')

    stats = {}
    stats['usuarios_all'] = usuarios_all_count()

    stats['emails_validados'] = emails_validados_count()[0]
    stats['emails_validados_percent'] = emails_validados_count()[1]

    stats['emails_no_robinson'] = emails_no_robinson_count()[0]
    stats['emails_no_robinson_percent'] = emails_no_robinson_count()[1]

    stats['emails_no_ban'] = emails_no_ban_count()[0]
    stats['emails_no_ban_percent'] = emails_no_ban_count()[1]

    stats['tutoria_timeout'] = tutoria_timeout_count()[0]
    stats['tutoria_timeout_percent'] = tutoria_timeout_count()[1]
    stats['evolucion_equipo_educativo'] = evolucion_equipo_educativo_count()[0]
    stats['evolucion_equipo_educativo_percent'] = evolucion_equipo_educativo_count()[1]

    stats['tutorias_all_count'] = tutorias_all_count()
    stats['tutorias_con_respuesta'] = tutorias_con_respuesta_count()[0]
    stats['tutorias_con_respuesta_percent'] = tutorias_con_respuesta_count()[1]

    stats['preguntas_por_cuestionario_min'] = preguntas_por_cuestionario()[0]
    stats['preguntas_por_cuestionario_media'] = preguntas_por_cuestionario()[1]
    stats['preguntas_por_cuestionario_max'] = preguntas_por_cuestionario()[2]
    stats['preguntas_por_cuestionario_percent'] = preguntas_por_cuestionario()[3]

    stats['profesores_all_count'] = profesores_all_cunt()
    stats['profesores_por_usuario_min'] = profesores_por_usuario()[0]
    stats['profesores_por_usuario_media'] = profesores_por_usuario()[1]
    stats['profesores_por_usuario_max'] = profesores_por_usuario()[2]

    stats['profesores_actividad'] = profesores_actividad_count()[0]
    stats['profesores_actividad_percent'] = profesores_actividad_count()[1]
    stats['profesores_activos_evolucion'] = profesores_actividad_count()[2]
    stats['profesores_activos_evolucion_frecuencia'] = profesores_actividad_count()[3]
    stats['profesores_activos_evolucion_frecuencia_absoluta'] = profesores_actividad_count()[4]
    stats['profesores_activos_evolucion_media'] = profesores_actividad_count()[5]

    stats['tutorias_por_usuario_min'] = tutorias_por_usuario_count()[0]
    stats['tutorias_por_usuario_media'] = tutorias_por_usuario_count()[1]
    stats['tutorias_por_usuario_max'] = tutorias_por_usuario_count()[2]

    stats['cuestionario_actividad'] = cuestionario_actividad()

    stats['informes_con_comentario'] = informes_con_comentario_count()[0]
    stats['informes_con_comentario_percent'] = informes_con_comentario_count()[1]

    stats['informes_con_pruebas_evalubles'] = informes_con_pruebas_evalubles_count()[0]
    stats['informes_con_pruebas_evalubles_percent'] = informes_con_pruebas_evalubles_count()[1]

    stats['diferencial_media'] = diferencial_media()

    stats['tutores_over_all'] = (20 * stats['emails_validados_percent'] + 20 * stats['emails_no_ban_percent'] + 10 * stats['emails_no_robinson_percent'] + 40 * stats['preguntas_por_cuestionario_percent'] + 10 * stats['evolucion_equipo_educativo_percent']) / 100
    stats['profesores_over_all'] = (50 * stats['tutorias_con_respuesta_percent'] + 30 * stats['profesores_actividad_percent'] + 10 * stats['informes_con_pruebas_evalubles_percent'] + 10 * stats['informes_con_comentario_percent']) / 100
    # --------------------------------
    return render_template(
        'admin_estadisticas.html', params=params, stats=stats)


# XXX wellcome


@app.route('/wellcome')
@login_required
def wellcome_html():
    params = {}
    params['anchor'] = 'anchor_top'
    # flash_toast('Bienvenido ' + current_user.username, 'success')
    return render_template('wellcome.html', params=params)


# XXX admin_usuario_edit


@app.route('/admin_usuario_edit', methods=['GET', 'POST'])
@app.route('/admin_usuario_edit/<params>', methods=['GET', 'POST'])
@login_required
def admin_usuario_edit_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_usuario_id'] = params_old.get('current_usuario_id', 0)
    params['usuario_delete_link'] = params_old.get('usuario_delete_link', False)
    params['usuario_edit_link'] = params_old.get('usuario_edit_link', False)
    params['current_url'] = params_old.get('current_url', 'admin_usuario_data_grupos_html')

    if request.method == 'POST':
        usuario_edit_form = Usuario_Edit(request.form)
        current_usuario_id = current_id_request('current_usuario_id')
        params['current_usuario_id'] = current_usuario_id
        current_url = request.form.get('current_url')
        params['current_url'] = current_url

        # XXX selector_usuario_edit_link
        if request.form['selector_button'] == 'selector_usuario_edit_link':
            params['usuario_edit_link'] = True
            return redirect(url_for(current_url, params=dic_encode(params)))

        # XXX usuario_edit
        if request.form['selector_button'] == 'selector_usuario_edit':
            settings_edit_ban = usuario_edit_form.ban.data
            settings_email_validated = usuario_edit_form.email_validated.data
            settings_email_robinson = usuario_edit_form.email_robinson.data

            params['usuario_edit_link'] = True
            if not settings_edit_ban:
                settings_edit_ban = False
            if not settings_email_validated:
                settings_email_validated = False
            if not settings_email_robinson:
                settings_email_robinson = False

            if usuario_edit_form.validate():
                settings_sql = session_sql.query(Settings).filter(Settings.id == current_usuario_id).first()
                settings_sql.role = usuario_edit_form.role.data
                settings_sql.ban = settings_edit_ban
                settings_sql.email_validated = settings_email_validated
                settings_sql.email_robinson = settings_email_robinson

                usuario_sql = session_sql.query(User).filter(User.id == current_usuario_id).first()
                usuario_password_new = usuario_edit_form.password.data

                if usuario_password_new:
                    hashed_password = generate_password_hash(usuario_password_new, method='sha256')
                    usuario_sql.password = hashed_password

                session_sql.commit()

                # NOTE usuario_username_unicidad
                usuario_username_duplicado = session_sql.query(User).filter(User.username == usuario_edit_form.username.data).all()
                for usuario_duplicado in usuario_username_duplicado:
                    if usuario_duplicado.id != usuario_sql.id:
                        flash_toast('Usuario ya registrado', 'warning')
                        return render_template(
                            'admin_usuario_data_grupos.html', usuario_edit=usuario_edit_form, usuario=user_by_id(current_usuario_id), params=params)
                else:
                    usuario_sql.username = usuario_edit_form.username.data
                    # session_sql.commit()

                # NOTE usuario_email_unicidad
                usuario_email_duplicado = session_sql.query(User).filter(User.email == usuario_edit_form.email.data).all()
                for usuario_duplicado in usuario_email_duplicado:
                    if usuario_duplicado.id != usuario_sql.id:
                        flash_toast('Email ya registrado', 'warning')
                        return render_template(
                            'admin_usuario_data_grupos.html', usuario_edit=usuario_edit_form, usuario=user_by_id(current_usuario_id), params=params)
                else:
                    usuario_sql.email = usuario_edit_form.email.data
                    session_sql.commit()

                flash_toast(Markup('Usuario <strong>') + usuario_edit_form.username.data + Markup('</strong>') + ' actualizado', 'success')
                session_sql.commit()
                return redirect(url_for('admin_usuario_data_grupos_html', params=dic_encode(params)))
            else:
                flash_wtforms(usuario_edit_form, flash_toast, 'warning')
            return render_template(
                'admin_usuario_data_grupos.html', usuario_edit=usuario_edit_form, usuario=user_by_id(current_usuario_id), params=params)

        # XXX selector_usuario_edit_close
        if request.form['selector_button'] == 'selector_usuario_edit_close':
            return redirect(url_for('admin_usuario_data_grupos_html', params=dic_encode(params)))

        # XXX usuario_edit_rollback
        if request.form['selector_button'] == 'selector_usuario_edit_rollback':
            session_sql.rollback()
            return redirect(url_for('admin_usuario_data_grupos_html', params=dic_encode(params)))

        # XXX usuario_delete_link
        if request.form['selector_button'] == 'selector_usuario_delete_link':
            params['usuario_edit_link'] = True
            params['usuario_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('admin_usuario_data_grupos_html', params=dic_encode(params)))

        # XXX usuario_delete
        if request.form['selector_button'] == 'selector_usuario_delete':
            if request.form['selector_button'] == 'selector_usuario_delete':
                current_usuario_id = current_id_request('current_usuario_id')
                usuario_sql = session_sql.query(User).filter(User.id == current_usuario_id).first()
                session_sql.delete(usuario_sql)
                session_sql.commit()
                flash_toast(Markup('Usuario <strong>') + usuario_sql.username + Markup('</strong>') + ' elminado', 'success')
                return redirect(url_for('admin_usuarios_html'))

        # XXX usuario_delete_close
        if request.form['selector_button'] == 'selector_usuario_delete_close':
            current_usuario_id = current_id_request('current_usuario_id')
            params['current_usuario_id'] = current_usuario_id
            return redirect(url_for('admin_usuario_data_grupos_html', params=dic_encode(params)))

    return render_template(
        'admin_usuarios.html', usuario_edit=Usuario_Edit(), params=params)

# XXX admin_usuario_data_grupos


@app.route('/admin_usuario_data_grupos', methods=['GET', 'POST'])
@app.route('/admin_usuario_data_grupos/<params>', methods=['GET', 'POST'])
@login_required
def admin_usuario_data_grupos_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_usuario_id'] = params_old.get('current_usuario_id', 0)
    params['usuario_delete_link'] = params_old.get('usuario_delete_link', False)
    params['usuario_edit_link'] = params_old.get('usuario_edit_link', False)

    current_usuario_id = params['current_usuario_id']
    usuario = user_by_id(current_usuario_id)
    params['current_url'] = 'admin_usuario_data_grupos_html'
    return render_template(
        'admin_usuario_data_grupos.html', usuario_edit=Usuario_Edit(), usuario=usuario, params=params)


# XXX admin_usuario_data_opciones

@app.route('/admin_usuario_data_opciones', methods=['GET', 'POST'])
@app.route('/admin_usuario_data_opciones/<params>', methods=['GET', 'POST'])
@login_required
def admin_usuario_data_opciones_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_usuario_id'] = params_old.get('current_usuario_id', 0)
    params['usuario_delete_link'] = params_old.get('usuario_delete_link', False)
    params['usuario_edit_link'] = params_old.get('usuario_edit_link', False)
    current_usuario_id = params['current_usuario_id']
    usuario = user_by_id(current_usuario_id)
    params['current_url'] = 'admin_usuario_data_opciones_html'
    return render_template(
        'admin_usuario_data_opciones.html', usuario_edit=Usuario_Edit(), usuario=usuario, params=params)


# XXX admin_usuario_data_cuestionario
@app.route('/admin_usuario_data_cuestionario', methods=['GET', 'POST'])
@app.route('/admin_usuario_data_cuestionario/<params>', methods=['GET', 'POST'])
@login_required
def admin_usuario_data_cuestionario_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_usuario_id'] = params_old.get('current_usuario_id', 0)
    params['usuario_delete_link'] = params_old.get('usuario_delete_link', False)
    params['usuario_edit_link'] = params_old.get('usuario_edit_link', False)
    current_usuario_id = params['current_usuario_id']
    usuario = user_by_id(current_usuario_id)
    params['current_url'] = 'admin_usuario_data_cuestionario_html'
    return render_template(
        'admin_usuario_data_cuestionario.html', usuario_edit=Usuario_Edit(), usuario=usuario, params=params)


# XXX admin_usuarios


@app.route('/admin_usuarios', methods=['GET', 'POST'])
@app.route('/admin_usuarios/<params>', methods=['GET', 'POST'])
@login_required
def admin_usuarios_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')

    return render_template(
        'admin_usuarios.html', params=params)


# XXX user_ficha_alumnos
@app.route('/user_ficha_alumnos', methods=['GET', 'POST'])
@app.route('/user_ficha_alumnos/<params>', methods=['GET', 'POST'])
@login_required
def user_ficha_alumnos_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_user_id'] = params_old.get('current_user_id', 0)
    current_user_id = params['current_user_id']
    user = user_by_id(current_user_id)

    return render_template(
        'user_ficha_alumnos.html', user=user, params=params)


# XXX pruebas


@app.route('/pagina_1/', methods=['GET', 'POST'])
@app.route('/pagina_1/<params>', methods=['GET', 'POST'])
def pagina_1_html(params={}):
    par_1 = ''
    par_2 = ''
    # NOTE ejemplo de args (funcional)
    # args_decoded = f_decode(request.args.get('args', False))
    # par_1 = args_decoded.split('&')[0].split('=')[1]
    # return render_template('pagina_1.html', par_1=par_1, par_2=par_2)
    # NOTE ejemplo de params (funcional)
    try:
        params = dic_decode(params)
    except:
        abort(404)
    params['collapse'] = False
    # params = dic_decode(params)
    # NOTE ejemplo de decorardor
    # params = dic_decode(params)
    # params = 'hola'
    flash_toast('ejemplo de flash_toast sin sesion', 'success')

    return render_template('pagina_1.html', par_1=par_1, par_2=par_2, params=params)


@app.route('/pagina_2', methods=['GET', 'POST'])
def pagina_2_html():

    # NOTE ejemplo de args (funcional)
    # args = 'par_1=hola&par_2=adios'
    # par_1 = 'xxxxxx'
    # args = f.encrypt(str.encode('par_1=' + par_1 + '&par_2=adios'))
    # return redirect(url_for('pagina_1_html', args=args))

    # NOTE ejemplo de params (fucional)
    alumnos_id = 'hola'
    params = {'alumno_id': alumnos_id, 'anchor': 'top'}
    params = dic_encode(params)
    # NOTE ejemplo de decorardor
    # params = 'hola'

    return redirect(url_for('pagina_1_html', params=params))

# XXX alumnos


@app.route('/alumnos', methods=['GET', 'POST'])
@app.route('/alumnos/<params>', methods=['GET', 'POST'])
@login_required
def alumnos_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['collapse_alumno_add'] = params_old.get('collapse_alumno_add', False)
    params['alumno_importar_link'] = params_old.get('alumno_importar_link', False)
    params['collapse_alumno'] = params_old.get('collapse_alumno', False)
    params['alumno_edit_link'] = params_old.get('alumno_edit_link', False)
    params['collapse_alumno_edit'] = params_old.get('collapse_alumno_edit', False)
    params['collapse_alumno_edit_asignaturas'] = params_old.get('collapse_alumno_edit_asignaturas', False)
    params['current_alumno_id'] = params_old.get('current_alumno_id', 0)
    params['from_url'] = params_old.get('from_url', False)
    params['alumno_delete_link'] = params_old.get('alumno_delete_link', False)
    params['collapse_tutorias'] = params_old.get('collapse_tutorias', False)
    params['collapse_tutoria_no_activas'] = params_old.get('collapse_tutoria_no_activas', False)
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
    params['invitado'] = params_old.get('invitado', False)

    if not settings().grupo_activo_id:
        if not grupos():
            params['collapse_grupo_add'] = True
        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

    if request.method == 'POST':
        # NOTE almacena current_alumno_id para el resto de situacones
        current_alumno_id = current_id_request('current_alumno_id')
        params['current_alumno_id'] = current_alumno_id
        # XXX alumno_add
        if request.form['selector_button'] == 'selector_alumno_add':
            params['collapse_alumno_add'] = True
            alumno_add_form = Alumno_Add(request.form)
            if alumno_add_form.validate():
                alumno = session_sql.query(Alumno).filter(Alumno.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Alumno.apellidos)) == unaccent(func.lower(alumno_add_form.apellidos.data)), unaccent(func.lower(Alumno.nombre)) == unaccent(func.lower(alumno_add_form.nombre.data))).first()
                if alumno:
                    alumno_add_form.nombre.errors = ['']
                    alumno_add_form.apellidos.errors = ['']
                    params['anchor'] = 'anchor_alu_add'
                    flash_toast(Markup('<strong>') + alumno_add_form.nombre.data.title() + Markup('</strong>') + ' ' + Markup('<strong>') + alumno_add_form.apellidos.data.title() + Markup('</strong>') + ' ya esta registrado', 'warning')
                    return render_template(
                        'alumnos.html', alumno_add=alumno_add_form, alumno_edit=Alumno_Add(), tutoria_add=Tutoria_Add(),
                        params=params)
                else:
                    params['collapse_alumno_add'] = False
                    alumno_add = Alumno(grupo_id=settings().grupo_activo_id, apellidos=alumno_add_form.apellidos.data.title(), nombre=alumno_add_form.nombre.data.title())
                    session_sql.add(alumno_add)
                    session_sql.commit()
                    flash_toast(Markup('<strong>') + alumno_add_form.nombre.data.title() + Markup('</strong>') + ' agregado', 'success')
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))
            else:
                params['anchor'] = 'anchor_alu_add'
                flash_wtforms(alumno_add_form, flash_toast, 'warning')
                return render_template(
                    'alumnos.html', alumno_add=alumno_add_form, alumno_edit=Alumno_Add(), tutoria_add=Tutoria_Add(),
                    params=params)

        # XXX selector_alumno_add_cerrar
        if request.form['selector_button'] == 'selector_alumno_add_cerrar':
            return redirect(url_for('alumnos_html'))

        # XXX alumno_importar_link
        if request.form['selector_button'] == 'selector_alumno_importar_link':
            params['collapse_alumno_add'] = True
            params['alumno_importar_link'] = True
            params['anchor'] = 'anchor_alu_add'
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX alumno_importar
        if request.form['selector_button'] == 'selector_alumno_importar':
            alumno_repetido_contador = 0
            alumno_add_contador = 0
            params['collapse_alumno_add'] = True
            params['alumno_importar_link'] = True
            fichero = request.files['fichero']
            if fichero.filename == '':
                flash_toast('No has seleccionado ningun archivo', 'warning')
            else:
                if not allowed_file(fichero.filename):
                    flash_toast('Archivo seleccionado no tiene formato CSV', 'warning')
                else:
                    params['collapse_alumno_add'] = False
                    params['alumno_importar_link'] = False
                    fichero_data = fichero.stream.read().decode('iso-8859-1')
                    alumnos_reader = csv.DictReader(fichero_data)
                    for alumno in alumnos_reader:
                        alumno_apellidos = alumno['Alumno'].split(', ')[0]
                        alumno_nombre = alumno['Alumno'].split(', ')[1]
                        alumno_sql = session_sql.query(Alumno).filter(Alumno.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Alumno.apellidos)) == unaccent(func.lower(alumno_apellidos)), unaccent(func.lower(Alumno.nombre)) == unaccent(func.lower(alumno_nombre))).first()
                        if alumno_sql:
                            alumno_repetido_contador = alumno_repetido_contador + 1
                        else:
                            alumno_add_contador = alumno_add_contador + 1
                            alumno_add = Alumno(grupo_id=settings().grupo_activo_id, apellidos=alumno_apellidos, nombre=alumno_nombre)
                            session_sql.add(alumno_add)
                    session_sql.commit()
                    if alumno_add_contador != 0:
                        flash_toast(Markup('<strong>') + str(alumno_add_contador) + Markup('</strong>') + ' ' + singular_plural('alumno', 'alumnos', alumno_add_contador) + ' ' + singular_plural('agregado', 'agregados', alumno_add_contador), 'success')
                    if alumno_repetido_contador != 0:
                        flash_toast(Markup('<strong>') + str(alumno_repetido_contador) + Markup('</strong>') + ' ' + singular_plural('alumno', 'alumnos', alumno_repetido_contador) + ' descartados, ya estan registrados', 'warning')
                    return redirect(url_for('alumnos_html'))
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX alumno_importar_cerrar
        if request.form['selector_button'] == 'selector_alumno_importar_cerrar':
            params['collapse_alumno_add'] = True
            params['alumno_importar_link'] = False
            params['anchor'] = 'anchor_alu_add'
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX alumno_edit_link
        if request.form['selector_button'] == 'selector_alumno_edit_link':
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['alumno_edit_link'] = True
            params['anchor'] = 'anchor_ficha_' + str(hashids_encode(current_alumno_id))
            if not alumno_asignaturas(current_alumno_id):
                params['collapse_alumno_edit_asignaturas'] = True
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX selector_alumno_edit_link_close
        if request.form['selector_button'] == 'selector_alumno_edit_link_close':
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['anchor'] = 'anchor_ficha_' + str(hashids_encode(current_alumno_id))
            # NOTE redirect a tutoria_add
            if params['from_url'] == 'from_tutoria_add':
                params['collapse_tutoria_add'] = True
                params['anchor'] = 'anchor_ficha_' + str(hashids_encode(current_alumno_id))
                return redirect(url_for('alumnos_html', params=dic_encode(params)))
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX selector_alumno_edit_close
        if request.form['selector_button'] == 'selector_alumno_edit_close':
            return redirect(url_for('alumnos_html'))

        # XXX alumno_edit
        if request.form['selector_button'] == 'selector_alumno_edit':
            alumno_edit_form = Alumno_Add(request.form)
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['alumno_edit_link'] = True
            params['anchor'] = 'anchor_ficha_' + str(hashids_encode(current_alumno_id))
            # XXX asignar asignaturas
            # ***************************************
            asignaturas_id_lista_encoded = request.form.getlist('asignatura')
            asignaturas_id_lista = []
            for asignatura_id_encoded in asignaturas_id_lista_encoded:
                asignaturas_id_lista.append(hashids_decode(asignatura_id_encoded))
            collapse_alumno_edit_asignaturas_contador = 0
            for asignatura in asignaturas_not_sorted():
                if asignatura.id in asignaturas_id_lista:
                    if not association_alumno_asignatura_check(current_alumno_id, asignatura.id):
                        alumno_asignatura_add = Association_Alumno_Asignatura(alumno_id=current_alumno_id, asignatura_id=asignatura.id)
                        session_sql.add(alumno_asignatura_add)
                        collapse_alumno_edit_asignaturas_contador += 1
                else:
                    if association_alumno_asignatura_check(current_alumno_id, asignatura.id):
                        alumno_asignatura_delete = session_sql.query(Association_Alumno_Asignatura).filter_by(alumno_id=current_alumno_id, asignatura_id=asignatura.id).first()
                        session_sql.delete(alumno_asignatura_delete)
                        collapse_alumno_edit_asignaturas_contador += 1
            if not alumno_asignaturas_id(current_alumno_id):
                params['collapse_alumno_edit_asignaturas'] = True
                flash_toast('Debería asignar asignaturas a ' + Markup('<strong>') + alumno_edit_form.nombre.data + Markup('</strong>'), 'warning')
            else:
                if collapse_alumno_edit_asignaturas_contador != 0:
                    params['collapse_alumno_edit_asignaturas'] = True
                    flash_toast('Asignadas asignaturas a ' + Markup('<strong>') + alumno_edit_form.nombre.data + Markup('</strong>'), 'success')
                    collapse_alumno_edit_asignaturas_contador = 0
                    # return redirect(url_for('alumnos_html', params=dic_encode(params)))
            session_sql.commit()  # NOTE agregado en caso de no modificar datos del alumno y solo asignacion de asignaturas

            # ***************************************
            if alumno_edit_form.validate():
                alumno_edit = Alumno(grupo_id=settings().grupo_activo_id, nombre=alumno_edit_form.nombre.data.title(), apellidos=alumno_edit_form.apellidos.data.title())
                alumno_sql = session_sql.query(Alumno).filter_by(id=current_alumno_id).first()
                if alumno_sql.nombre.lower() != alumno_edit.nombre.lower() or alumno_sql.apellidos.lower() != alumno_edit.apellidos.lower():
                    if alumno_sql.nombre.lower() != alumno_edit.nombre.lower():
                        alumno_sql.nombre = alumno_edit.nombre.title()
                        flash_toast(Markup('<strong>') + alumno_edit.nombre + Markup('</strong>') + ' actualizado', 'success')
                    if alumno_sql.apellidos.lower() != alumno_edit.apellidos.lower():
                        alumno_sql.apellidos = alumno_edit.apellidos.title()
                        flash_toast(Markup('<strong>') + alumno_edit.apellidos + Markup('</strong>') + ' actualizado', 'success')
                    session_sql.commit()
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))

                # XXX redirect a tutoria_add
                if params['from_url'] == 'from_tutoria_add':
                    params['collapse_alumno'] = True
                    params['collapse_tutoria_add'] = True
                    params['anchor'] = 'anchor_tut_add_' + str(hashids_encode(current_alumno_id))
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))
            else:
                flash_wtforms(alumno_edit_form, flash_toast, 'warning')
            return render_template('alumnos.html', alumno_add=Alumno_Add(), alumno_edit=alumno_edit_form,
                                   grupo_add=Grupo_Add(), tutoria_add=Tutoria_Add(), params=params)
        # XXX alumno_edit_rollback
        if request.form['selector_button'] == 'selector_alumno_edit_rollback':
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['alumno_edit_link'] = True
            params['anchor'] = 'anchor_tut_add_' + str(hashids_encode(current_alumno_id))
            session_sql.rollback()
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX alumno_delete_link
        if request.form['selector_button'] == 'selector_alumno_delete_link':
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['alumno_edit_link'] = True
            params['alumno_delete_link'] = True
            params['anchor'] = 'anchor_ficha_' + str(hashids_encode(current_alumno_id))
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX alumno_delete
        if request.form['selector_button'] == 'selector_alumno_delete':
            alumno_delete_form = Alumno_Add(request.form)
            alumno_delete(current_alumno_id)
            flash_toast(Markup('<strong>') + alumno_delete_form.nombre.data + Markup('</strong>') + ' elminado', 'success')
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX alumno_delete_close
        if request.form['selector_button'] == 'selector_alumno_delete_close':
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['alumno_edit_link'] = True
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX selector_tutoria_analisis
        if request.form['selector_button'] == 'selector_tutoria_analisis':
            current_tutoria_id = current_id_request('current_tutoria_id')
            params['current_tutoria_id'] = current_tutoria_id
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX selector_tutoria_analisis_close
        if request.form['selector_button'] == 'selector_tutoria_analisis_close':
            return redirect(url_for('alumnos_html'))

        # XXX tutoria_add
        if request.form['selector_button'] == 'selector_tutoria_add':
            current_tutoria_id = current_id_request('current_tutoria_id')
            params['current_tutoria_id'] = current_tutoria_id
            params['anchor'] = 'anchor_alu_' + str(hashids_encode(current_alumno_id))
            params['collapse_alumno'] = True
            params['collapse_tutoria_add'] = True
            tutoria_add_form = Tutoria_Add(current_alumno_id=current_alumno_id, fecha=request.form.get('fecha'), hora=request.form.get('hora'))

            # NOTE check si hay asignaturas asignadas al grupo
            if not asignaturas_not_sorted():
                params['collapse_asignatura_add'] = True
                # params['from_url'] = 'from_tutoria_add' # FIXME lo aparco aqui de momento
                flash_toast('Tutoria no solicitada' + Markup('<br>') + 'Debes asignar alguna asignatura', 'warning')
                return redirect(url_for('asignaturas_html', params=dic_encode(params)))

            # NOTE check si hay asignaturas asignadas al alumno
            if not alumno_asignaturas(current_alumno_id):
                params['collapse_alumno_edit'] = True
                params['alumno_edit_link'] = True
                params['collapse_alumno_edit_asignaturas'] = True
                # params['anchor'] = 'anchor_alu_asig_' + str(hashids_encode(current_alumno_id))
                # params['from_url'] = 'from_tutoria_add'  # FIXME revisar si es necesario
                flash_toast('Tutoria no solicitada' + Markup('<br>') + 'Debes asignar alguna asignatura', 'warning')
                return redirect(url_for('alumnos_html', params=dic_encode(params)))

            # NOTE check si hay preguntas asignadas en el cuestionario
            if not informe_preguntas():
                params['current_alumno_id'] = current_alumno_id
                # params['from_url'] = 'from_tutoria_add' # FIXME lo aparco aqui de momento
                flash_toast('Tutoria no solicitada' + Markup('<br>') + 'Debes asignar preguntas al cuestionario', 'warning')
                return redirect(url_for('settings_cuestionario_html', params=dic_encode(params)))

            else:
                if tutoria_add_form.validate():
                    tutoria_add_form_fecha = datetime.datetime.strptime(tutoria_add_form.fecha.data, '%A-%d-%B-%Y').strftime('%Y-%m-%d')
                    tutoria_add = Tutoria(alumno_id=current_alumno_id, fecha=tutoria_add_form_fecha, hora=tutoria_add_form.hora.data)
                    alumno = alumno_by_id(current_alumno_id)
                    tutoria_sql = session_sql.query(Tutoria).filter(Tutoria.alumno_id == current_alumno_id, Tutoria.fecha == tutoria_add_form_fecha).first()
                    # NOTE tutorias_timeout (tutoria_add)
                    if datetime.datetime.strptime(tutoria_add_form_fecha, '%Y-%m-%d').date() < g.current_date:
                        tutoria_add_form.fecha.errors = ['Fecha ya pasada.']
                        flash_toast('Tutoria no generada' + Markup('<br>') + 'Fecha pasada', 'warning')
                    else:
                        if tutoria_sql:
                            # NOTE tutoria ya existe y redirect a al modo de edicion de la tutoria
                            flash_toast('Ya existe esta tutoría' + Markup('<br>') + 'Es aconsejable reenviarla', 'warning')
                            # FIXME: parametros_url
                            params['current_tutoria_id'] = tutoria_sql.id
                            return redirect(url_for('analisis_html', params=dic_encode(params)))
                        else:
                            session_sql.add(tutoria_add)
                            session_sql.commit()
                            send_email_tutoria_asincrono(alumno, tutoria_add)  # NOTE anulado temporalemente para pruebas el envio de mails.
                            flash_toast('Enviando emails al equipo educativo de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>'), 'info')
                            params['current_alumno_id'] = current_alumno_id
                            params['collapse_alumno'] = True
                            params['collapse_tutorias'] = True
                            params['anchor'] = 'anchor_top'
                            # NOTE comprobar permisos de oauth2
                            if settings().calendar:
                                if settings().oauth2_credentials:
                                    try:
                                        credentials = oauth2client.client.Credentials.new_from_json(settings().oauth2_credentials)
                                        http = httplib2.Http()
                                        http = credentials.authorize(http)
                                        service = discovery.build('calendar', 'v3', http=http)
                                    except:
                                        return redirect(url_for('oauth2callback'))
                                else:
                                    return redirect(url_for('oauth2callback'))
                               # NOTE agregar eventos a la agenda
                                tutoria_add_form_hora = datetime.datetime.strptime(tutoria_add_form.hora.data, '%H:%M')
                                calendar_datetime_utc_start = (datetime.datetime.strptime(tutoria_add_form.fecha.data, '%A-%d-%B-%Y') + datetime.timedelta(hours=tutoria_add_form_hora.hour) + datetime.timedelta(minutes=tutoria_add_form_hora.minute)).timestamp()
                                # calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start))
                                # XXXXXXXXXXXXXXXXXXXXXXX tutoria_add
                                calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start).to('local'))
                                # calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start).to('Europe/Madrid'))

                                calendar_datetime_utc_end = (datetime.datetime.strptime(tutoria_add_form.fecha.data, '%A-%d-%B-%Y') + datetime.timedelta(hours=tutoria_add_form_hora.hour) + datetime.timedelta(minutes=(tutoria_add_form_hora.minute + settings().tutoria_duracion))).timestamp()
                                calendar_datetime_utc_end_arrow = str(arrow.get(calendar_datetime_utc_end))

                                event = {
                                    'summary': 'Tutoria de ' + alumno.nombre,
                                    'location': grupo_activo().centro,
                                    'description': 'Evento creado por https://mitutoria.herokuapp.com/',
                                    'colorId': '3',
                                    'start': {
                                        'dateTime': calendar_datetime_utc_start_arrow,
                                        'timeZone': 'Europe/London',
                                        # 'timeZone': 'local',
                                    },
                                    'end': {
                                        'dateTime': calendar_datetime_utc_end_arrow,
                                        'timeZone': 'Europe/London',
                                        # 'timeZone': 'local',
                                    }
                                }
                                event = service.events().insert(calendarId='primary', body=event).execute()
                                session_sql.flush()
                                session_sql.refresh(tutoria_add)
                                tutoria_add_id = tutoria_add.id
                                tutoria_sql = tutoria_by_id(tutoria_add_id)
                                tutoria_sql.calendar_event_id = event['id']
                                session_sql.commit()
                            return redirect(url_for('alumnos_html', params=dic_encode(params)))
                else:
                    flash_wtforms(tutoria_add_form, flash_toast, 'warning')
            return render_template(
                'alumnos.html', alumno_add=Alumno_Add(), alumno_edit=Alumno_Add(),
                tutoria_add=tutoria_add_form, params=params)

        # XXX selector_tutoria_add_close
        if request.form['selector_button'] == 'selector_tutoria_add_close':
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

    # XXX tutorias_timeout
    tutorias_timeout()

    # XXX sincronizar con google calendar
    tutoria_calendar_sync()

    return render_template(
        'alumnos.html', alumno_add=Alumno_Add(), alumno_edit=Alumno_Add(),
        tutoria_add=Tutoria_Add(), tutoria_edit=Tutoria_Add(), asignatura_add=Asignatura_Add(),
        params=params)

# XXX admin_cuestionario


@app.route('/admin_cuestionario', methods=['GET', 'POST'])
@app.route('/admin_cuestionario/<params>', methods=['GET', 'POST'])
@login_required
def admin_cuestionario_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_pregunta_id'] = params_old.get('current_pregunta_id', 0)
    params['collapse_pregunta_edit'] = params_old.get('collapse_pregunta_edit', False)
    params['pregunta_delete_link'] = params_old.get('pregunta_delete_link', False)
    params['collapse_pregunta_add'] = params_old.get('collapse_pregunta_add', False)
    params['pregunta_edit_link'] = params_old.get('pregunta_edit_link', False)

    if request.method == 'POST':
        current_pregunta_id = current_id_request('current_pregunta_id')
        params['current_pregunta_id'] = current_pregunta_id

        # XXX pregunta_add
        if request.form['selector_button'] == 'selector_pregunta_add':
            params['collapse_pregunta_add'] = True
            pregunta_add_form = Pregunta_Add(request.form)
            if pregunta_add_form.validate():
                pregunta_add = Pregunta(enunciado=pregunta_add_form.enunciado.data, enunciado_ticker=pregunta_add_form.enunciado_ticker.data,
                                        orden=pregunta_add_form.orden.data, visible=pregunta_add_form.visible.data, active_default=pregunta_add_form.active_default.data)
                # NOTE checking unicidad de enunciado, ticker y orden
                pregunta_enunciado_sql = session_sql.query(Pregunta).filter(Pregunta.enunciado == pregunta_add_form.enunciado.data).first()
                pregunta_enunciado_ticker_sql = session_sql.query(Pregunta).filter(Pregunta.enunciado_ticker == pregunta_add_form.enunciado_ticker.data).first()
                pregunta_orden_sql = session_sql.query(Pregunta).filter(Pregunta.orden == pregunta_add_form.orden.data).first()
                if pregunta_enunciado_sql or pregunta_enunciado_ticker_sql or pregunta_orden_sql:
                    if pregunta_enunciado_sql:
                        pregunta_add_form.enunciado.errors = ['']
                        flash_toast('Enunciado duplicado', 'warning')
                    if pregunta_enunciado_ticker_sql:
                        pregunta_add_form.enunciado_ticker.errors = ['']
                        flash_toast('Ticker duplicado', 'warning')
                    if pregunta_orden_sql:
                        pregunta_add_form.orden.errors = ['']
                        flash_toast('Orden duplicado', 'warning')
                    return render_template(
                        'admin_cuestionario.html',  pregunta_add=pregunta_add_form, preguntas=preguntas(''),
                        pregunta_edit=Pregunta_Add(), params=params)
                else:
                    session_sql.add(pregunta_add)
                    session_sql.commit()
                    flash_toast('Pregunta agregada', 'success')
                    return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))
            else:
                params['collapse_pregunta_add'] = True
                flash_wtforms(pregunta_add_form, flash_toast, 'warning')
            return render_template(
                'admin_cuestionario.html', pregunta_add=pregunta_add_form, preguntas=preguntas(''),
                pregunta_edit=Pregunta_Add(), params=params)

        # XXX selector_pregunta_add_close
        if request.form['selector_button'] == 'selector_pregunta_add_close':
            return redirect(url_for('admin_cuestionario_html'))

        # XXX selector_pregunta_edit_link
        if request.form['selector_button'] == 'selector_pregunta_edit_link':
            params['pregunta_edit_link'] = True
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX pregunta_edit
        if request.form['selector_button'] in ['selector_pregunta_edit', 'selector_move_down', 'selector_move_up']:
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['pregunta_edit_link'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            move_up = False
            move_down = False
            pregunta_edit_form = Pregunta_Add(request.form)
            visible = pregunta_edit_form.visible.data
            active_default = pregunta_edit_form.active_default.data
            if not visible:
                visible = False

            if not active_default:
                active_default = False

            if pregunta_edit_form.validate():
                pregunta_edit = Pregunta(enunciado=pregunta_edit_form.enunciado.data, enunciado_ticker=pregunta_edit_form.enunciado_ticker.data,
                                         orden=pregunta_edit_form.orden.data, visible=visible, active_default=active_default)
                pregunta = session_sql.query(Pregunta).filter(Pregunta.id == current_pregunta_id).first()
                if pregunta.enunciado.lower() != pregunta_edit.enunciado.lower() or pregunta.enunciado_ticker.lower() != pregunta_edit.enunciado_ticker.lower() or pregunta.orden != pregunta_edit.orden or str(pregunta.visible) != str(visible) or str(pregunta.active_default) != str(active_default):
                    if pregunta.enunciado.lower() != pregunta_edit.enunciado.lower():
                        pregunta.enunciado = pregunta_edit.enunciado
                    if pregunta.enunciado_ticker.lower() != pregunta_edit.enunciado_ticker.lower():
                        pregunta.enunciado_ticker = pregunta_edit.enunciado_ticker
                    if pregunta.orden != pregunta_edit.orden:
                        pregunta.orden = pregunta_edit.orden
                    if pregunta.visible != visible:
                        pregunta.visible = visible
                    if pregunta.active_default != active_default:
                        pregunta.active_default = active_default

                    flash_toast('Pregunta actualizada', 'success')
                if request.form['selector_button'] == 'selector_move_down':
                    for k in range(1, 500):
                        pregunta_down = session_sql.query(Pregunta).filter(Pregunta.orden == (pregunta.orden + k)).first()
                        if pregunta_down:
                            move_down = int(str(pregunta.orden + k))
                            pregunta.orden = pregunta.orden + k
                            pregunta_down.orden = pregunta.orden - k
                            flash_toast('Pregunta bajada', 'success')
                            break

                if request.form['selector_button'] == 'selector_move_up':
                    for k in range(1, 500):
                        pregunta_down = session_sql.query(Pregunta).filter(Pregunta.orden == (pregunta.orden - k)).first()
                        if pregunta_down:
                            move_up = int(str(pregunta.orden - k))
                            pregunta.orden = pregunta.orden - k
                            pregunta_down.orden = pregunta.orden + k
                            flash_toast('Pregunta subida', 'success')
                            break

                session_sql.commit()
                return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))
            else:
                flash_wtforms(pregunta_edit_form, flash_toast, 'warning')
            return render_template(
                'admin_cuestionario.html', pregunta_add=Pregunta_Add(), preguntas=preguntas(''),
                pregunta_edit=pregunta_edit_form, move_down=move_down, move_up=move_up, visible=visible,
                active_default=active_default, params=params)

        # XXX selector_pregunta_edit_close
        if request.form['selector_button'] == 'selector_pregunta_edit_close':
            return redirect(url_for('admin_cuestionario_html'))

        # XXX selector_pregunta_edit_rollback
        if request.form['selector_button'] == 'selector_pregunta_edit_rollback':
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            session_sql.rollback()
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX selector_pregunta_delete_link
        if request.form['selector_button'] == 'selector_pregunta_delete_link':
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            params['pregunta_edit_link'] = True
            params['pregunta_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX pregunta_delete
        if request.form['selector_button'] == 'selector_pregunta_delete':
            pregunta_delete_form = Pregunta_Add(request.form)
            current_pregunta_id = current_id_request('current_pregunta_id')
            pregunta_delete = pregunta_by_id(current_pregunta_id, '')
            session_sql.delete(pregunta_delete)
            session_sql.commit()
            flash_toast('Pregunta elminada', 'success')
            return redirect(url_for('admin_cuestionario_html'))

        # XXX pregunta_delete_close
        if request.form['selector_button'] == 'selector_pregunta_delete_close':
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

    return render_template(
        'admin_cuestionario.html', pregunta_add=Pregunta_Add(), preguntas=preguntas(''),
        pregunta_edit=Pregunta_Add(), params=params)


@app.route('/settings_cuestionario', methods=['GET', 'POST'])
@app.route('/settings_cuestionario/<params>', methods=['GET', 'POST'])
@login_required
def settings_cuestionario_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    if request.method == 'POST':
        if request.form['selector_button'] == 'selector_settings_cuestionario':
            preguntas_id_lista_encoded = request.form.getlist('pregunta')
            preguntas_id_lista = []
            for pregunta_id_encoded in preguntas_id_lista_encoded:
                preguntas_id_lista.append(hashids_decode(pregunta_id_encoded))
            contador = 0
            for pregunta in preguntas(''):
                if pregunta.id in preguntas_id_lista:
                    association_settings_pregunta_sql = session_sql.query(Association_Settings_Pregunta).filter_by(pregunta_id=pregunta.id, settings_id=settings().id).first()
                    if not association_settings_pregunta_sql:
                        association_settings_pregunta_add = Association_Settings_Pregunta(pregunta_id=pregunta.id, settings_id=settings().id)
                        session_sql.add(association_settings_pregunta_add)
                        contador += 1
                else:
                    association_settings_pregunta_sql = session_sql.query(Association_Settings_Pregunta).filter_by(pregunta_id=pregunta.id, settings_id=settings().id).first()
                    if association_settings_pregunta_sql:
                        session_sql.delete(association_settings_pregunta_sql)
                        contador += 1
            session_sql.commit()
            if not settings().preguntas:
                flash_toast('Cuestionario vacío', 'warning')
            else:
                if contador != 0:
                    flash_toast('Cuestionario  actualizado', 'success')
                    contador = 0
            return redirect(url_for('settings_cuestionario_html'))
    return render_template('settings_cuestionario.html', params=params)

# XXX user_grupos


@app.route('/user_grupos', methods=['GET', 'POST'])
@login_required
def user_grupos_html():

    current_user_id = request.args.get('i_7', False)
    user = user_by_id(current_user_id)
    grupos = user_grupos(current_user_id)
    return render_template('user_grupos.html'(True, False, False, True, True, True, True), user=user, grupos=grupos)


# XXX analisis


@app.route('/analisis_tutoria_no_disponible')
@login_required
def analisis_tutoria_no_disponible_html():
    return render_template('analisis_tutoria_no_disponible.html')


@app.route('/analisis', methods=['GET', 'POST'])
@app.route('/analisis/<params>', methods=['GET', 'POST'])
@login_required
def analisis_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
    current_tutoria_id = params['current_tutoria_id']  # NOTE current_tutoria_id evaluado correctamente
    params['tutoria_delete_link'] = params_old.get('tutoria_delete_link', False)
    params['tutoria_re_enviar_link'] = params_old.get('tutoria_re_enviar_link', False)
    params['tutoria_edit_link'] = params_old.get('tutoria_edit_link', False)

    grupo = grupo_activo()
    tutoria_sql = tutoria_by_id(current_tutoria_id)
    alumno_sql = invitado_alumno(current_tutoria_id)
    if not tutoria_sql or not alumno_sql:
        return redirect(url_for('analisis_tutoria_no_disponible_html'))

    df_data = df_load()
    # print(df_data)

    # abort(404)
    return render_template(
        'analisis.html', grupo=grupo, alumno=alumno_sql, tutoria=tutoria_sql,
        df_data=df_data, params=params)


# XXX analisis_tutoria_edit
@app.route('/analisis_tutoria_edit', methods=['GET', 'POST'])
@login_required
def analisis_tutoria_edit_html(params={}):
    params = {}
    if request.method == 'POST':
        current_tutoria_id = current_id_request('current_tutoria_id')
        params['current_tutoria_id'] = current_tutoria_id

        # XXX tutoria_edit_close
        if request.form['selector_button'] == 'selector_tutoria_edit_close':
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_regresar_alumno
        if request.form['selector_button'] == 'selector_tutoria_regresar_alumno':
            current_tutoria = tutoria_by_id(current_tutoria_id)
            alumno = alumno_by_id(current_tutoria.alumno_id)
            current_alumno_id = alumno.id
            params['current_alumno_id'] = current_alumno_id
            params['current_tutoria_id'] = current_tutoria_id
            params['collapse_alumno'] = True
            params['collapse_tutorias'] = True
            if not current_tutoria.activa:
                params['collapse_tutoria_no_activas'] = True
            params['anchor'] = 'anchor_alu_' + str(hashids_encode(current_alumno_id))
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX tutoria_re_enviar_link
        if request.form['selector_button'] == 'selector_tutoria_re_enviar_link':
            current_tutoria = tutoria_by_id(current_tutoria_id)
            if current_tutoria.activa:
                if current_tutoria.fecha < g.current_date:
                    flash_toast('No se puede reenviar una tutoria pasada' + Markup('<br>') + 'Debe cambiar fecha', 'warning')
                else:
                    params['tutoria_re_enviar_link'] = True
                    return redirect(url_for('analisis_html', params=dic_encode(params)))
            else:
                flash_toast('No deberías reenviar una tutoria archivada' + Markup('<br>') + 'Deberías activarla', 'warning')
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX selector_tutoria_re_enviar_close
        if request.form['selector_button'] == 'selector_tutoria_re_enviar_close':
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_re_enviar
        if request.form['selector_button'] == 'selector_tutoria_re_enviar':
            asignaturas_id_lista = []
            asignaturas_id_lista_encoded = request.form.getlist('asignatura')     # NOTE hay que decode esta lista (llega encoded)
            for asignatura_by_id_encoded in asignaturas_id_lista_encoded:
                asignatura_id = hashids_decode(str(asignatura_by_id_encoded))
                asignaturas_id_lista.append(asignatura_id)
            current_tutoria = tutoria_by_id(current_tutoria_id)
            alumno = alumno_by_id(current_tutoria.alumno_id)
            current_alumno_id = alumno.id
            if asignaturas_id_lista:
                re_send_email_tutoria_asincrono(alumno, current_tutoria, asignaturas_id_lista)
                flash_toast('Reenviando emails a las asignaturas elegidas', 'info')
                return redirect(url_for('analisis_html', params=dic_encode(params)))
            else:
                params['tutoria_re_enviar_link'] = True
                flash_toast('Emails no reenviados' + Markup('<br>') + 'Hay que asignar al menos una asignatura', 'warning')
                return redirect(url_for('analisis_html', params=dic_encode(params)))
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_mover_historial
        if request.form['selector_button'] == 'selector_tutoria_archivar':
            tutoria_to_move = tutoria_by_id(current_tutoria_id)
            tutoria_to_move.activa = False
            session_sql.commit()
            tutoria_calendar_delete(event_id=tutoria_to_move.calendar_event_id)
            flash_toast('Tutoria archivada', 'success')
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_activar
        if request.form['selector_button'] == 'selector_tutoria_activar':
            tutoria_to_move = tutoria_by_id(current_tutoria_id)
            if tutoria_to_move.fecha < g.current_date:
                flash_toast('No se puede activar una tutoria pasada' + Markup('<br>') + 'Debe cambiar fecha', 'warning')
            else:
                tutoria_to_move.activa = True
                session_sql.commit()
                tutoria_calendar_undelete(event_id=tutoria_to_move.calendar_event_id)
                flash_toast('Tutoria activada', 'success')
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_delete_link
        if request.form['selector_button'] == 'selector_tutoria_delete_link':
            params['tutoria_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_delete
        if request.form['selector_button'] == 'selector_tutoria_delete':
            tutoria_delete = tutoria_by_id(current_tutoria_id)
            alumno = alumno_by_id(tutoria_delete.alumno_id)
            flash_toast('Tutoria de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' eliminada', 'success')
            tutoria_calendar_delete(event_id=tutoria_delete.calendar_event_id)
            session_sql.delete(tutoria_delete)
            session_sql.commit()
            return redirect(url_for('alumnos_html'))

        # XXX selector_tutoria_delete_archivar
        if request.form['selector_button'] == 'selector_tutoria_delete_archivar':
            tutoria_to_move = tutoria_by_id(current_tutoria_id)
            tutoria_to_move.activa = False
            session_sql.commit()
            flash_toast('Tutoria archivada', 'success')
            params['tutoria_delete_link'] = False
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_delete_link_close
        if request.form['selector_button'] == 'selector_tutoria_delete_link_close':
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_edit_link
        if request.form['selector_button'] == 'selector_tutoria_edit_link':
            params['tutoria_edit_link'] = True
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_edit
        if request.form['selector_button'] == 'selector_tutoria_edit':
            params['tutoria_edit_link'] = True
            tutoria_sql = session_sql.query(Tutoria).filter(Tutoria.id == current_tutoria_id).first()
            tutoria_edit_form = Tutoria_Add(current_tutoria_id=current_tutoria_id, fecha=request.form.get('fecha'), hora=request.form.get('hora'))
            if tutoria_edit_form.validate():
                tutoria_edit_form_fecha = datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%A-%d-%B-%Y').strftime('%Y-%m-%d')
                if datetime.datetime.strptime(tutoria_edit_form_fecha, '%Y-%m-%d').date() < g.current_date:
                    tutoria_edit_form.fecha.errors = ['Tutoría no actualizada.']
                    flash_wtforms(tutoria_edit_form, flash_toast, 'warning')
                    flash_toast('Debe indicar una fecha posterior', 'warning')
                    return redirect(url_for('analisis_html', params=dic_encode(params)))
                else:
                    if settings().calendar:
                        if settings().oauth2_credentials:
                            try:
                                credentials = oauth2client.client.Credentials.new_from_json(settings().oauth2_credentials)
                                http = httplib2.Http()
                                http = credentials.authorize(http)
                                service = discovery.build('calendar', 'v3', http=http)
                            except:
                                return redirect(url_for('oauth2callback'))
                        else:
                            return redirect(url_for('oauth2callback'))

                    # local_tz = pytz.timezone ('Europe/London')
                    tutoria_edit_form_hora = datetime.datetime.strptime(tutoria_edit_form.hora.data, '%H:%M')
                    calendar_datetime_utc_start = (datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%A-%d-%B-%Y') + datetime.timedelta(hours=(tutoria_edit_form_hora.hour)) + datetime.timedelta(minutes=tutoria_edit_form_hora.minute)).timestamp()
                    calendar_datetime_utc_end = (datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%A-%d-%B-%Y') + datetime.timedelta(hours=(tutoria_edit_form_hora.hour)) + datetime.timedelta(minutes=(tutoria_edit_form_hora.minute + settings().tutoria_duracion))).timestamp()

                    # Convert to Europe/Berlin time zone
                    # now_berlin = now_pacific.astimezone(timezone('Europe/Berlin'))

                    # tutoria_edit_form_hora = datetime.datetime.strptime(tutoria_edit_form.hora.data, '%H:%M')
                    # calendar_datetime_utc_start = (datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%A-%d-%B-%Y') + datetime.timedelta(hours=(tutoria_edit_form_hora.hour-2)) + datetime.timedelta(minutes=tutoria_edit_form_hora.minute)).timestamp()
                    calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start))
                    # YYYYYYYYYYYYYYY tutoria_edit
                    # calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start).to('local'))

                    # calendar_datetime_utc_end = (datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%A-%d-%B-%Y') + datetime.timedelta(hours=(tutoria_edit_form_hora.hour-2)) + datetime.timedelta(minutes=(tutoria_edit_form_hora.minute + settings().tutoria_duracion))).timestamp()
                    calendar_datetime_utc_end_arrow = str(arrow.get(calendar_datetime_utc_end))
                    # calendar_datetime_utc_end_arrow = str(arrow.get(calendar_datetime_utc_end).to('local'))

                    try:
                        eventId = str(tutoria_sql.calendar_event_id)
                        event = service.events().get(calendarId='primary', eventId=eventId).execute()
                        event['start']['dateTime'] = calendar_datetime_utc_start_arrow
                        event['end']['dateTime'] = calendar_datetime_utc_end_arrow
                        event['status'] = 'confirmed'
                        updated_event = service.events().update(calendarId='primary', eventId=eventId, body=event).execute()
                    except:
                        pass

                    tutoria_sql.fecha = tutoria_edit_form_fecha
                    tutoria_sql.hora = string_to_time(tutoria_edit_form.hora.data)
                    tutoria_sql.activa = True
                    session_sql.commit()
                    flash_toast('Tutoria actualizada', 'success')
                    return redirect(url_for('analisis_html', params=dic_encode(params)))
            else:
                flash_wtforms(tutoria_edit_form, flash_toast, 'warning')
                return redirect(url_for('analisis_html', params=dic_encode(params)))

    abort(404)


# XXX settings_opciones


@app.route('/settings_opciones', methods=['GET', 'POST'])
@app.route('/settings_opciones/<params>', methods=['GET', 'POST'])
@login_required
def settings_opciones_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')

    if request.method == 'POST':
        # XXX settings_edit
        if request.form['selector_button'] == 'selector_settings_edit':
            settings_edit_tutoria_timeout = request.form.get('settings_edit_tutoria_timeout')
            settings_show_asignaturas_analisis = request.form.get('settings_show_asignaturas_analisis')
            settings_edit_calendar = request.form.get('settings_edit_calendar')
            settings_tutoria_duracion = request.form.get('settings_tutoria_duracion')
            settings_diferencial = request.form.get('settings_diferencial')

            if not settings_edit_tutoria_timeout:
                settings_edit_tutoria_timeout = False
            if not settings_show_asignaturas_analisis:
                settings_show_asignaturas_analisis = False
            if not settings_edit_calendar:
                settings_edit_calendar = False

            settings().tutoria_timeout = settings_edit_tutoria_timeout
            settings().show_asignaturas_analisis = settings_show_asignaturas_analisis
            settings().tutoria_duracion = settings_tutoria_duracion
            settings().diferencial = settings_diferencial
            settings().calendar = settings_edit_calendar
            flash_toast('Configuracion actualizada', 'success')
            session_sql.commit()

            if settings().calendar:
                if settings().oauth2_credentials:
                    credentials = oauth2client.client.Credentials.new_from_json(settings().oauth2_credentials)
                    settings().oauth2_credentials = credentials.to_json()
                    session_sql.commit()
                    http = credentials.authorize(httplib2.Http())
                    service = discovery.build('calendar', 'v3', http=http)
                else:
                    return redirect(url_for('oauth2callback'))

            return redirect(url_for('settings_opciones_html'))
    return render_template('settings_opciones.html', params=params)


# XXX settings_grupos
@app.route('/settings_grupos', methods=['GET', 'POST'])
@app.route('/settings_grupos/<params>', methods=['GET', 'POST'])
@login_required
def settings_grupos_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['login'] = params_old.get('login', False)
    params['collapse_grupo_add'] = params_old.get('collapse_grupo_add', False)
    params['grupo_delete_link'] = params_old.get('grupo_delete_link', False)
    params['collapse_grupo_edit'] = params_old.get('collapse_grupo_edit', False)
    params['current_grupo_id'] = params_old.get('current_grupo_id', 0)
    params['grupo_edit_link'] = params_old.get('grupo_edit_link', False)

    if request.method == 'POST':
        # NOTE recoge current_grupo_id para el resto de situaciones
        current_grupo_id = current_id_request('current_grupo_id')
        params['current_grupo_id'] = current_grupo_id
        # XXX grupo_add
        if request.form['selector_button'] == 'selector_grupo_add':
            params['collapse_grupo_add'] = True
            grupo_add_form = Grupo_Add(request.form)
            grupo_add_grupo_activo = request.form.get('grupo_add_grupo_activo')
            if grupo_add_form.validate():
                grupo_add = Grupo(settings_id=settings().id, nombre=grupo_add_form.nombre.data, tutor=grupo_add_form.tutor.data,
                                  centro=grupo_add_form.centro.data, curso_academico=grupo_add_form.curso_academico.data)
                # NOTE checking unicidad de nombre, centro, fecha y usuario
                unicidad_de_grupo_sql = session_sql.query(Settings).filter(Settings.id == settings().id).join(Grupo).filter(Grupo.nombre == grupo_add_form.nombre.data, Grupo.curso_academico == grupo_add_form.curso_academico.data, Grupo.centro == grupo_add_form.centro.data).first()
                if unicidad_de_grupo_sql:
                    grupo_add_form.nombre.errors = ['']
                    flash_toast(Markup('<strong>') + grupo_add.nombre + Markup('</strong> ya existe en ') + str(grupo_add.curso_academico) + Markup(' | ') + str(int(grupo_add.curso_academico) + 1) + Markup('<br> Cambie el nombre'), 'warning')
                    return render_template(
                        'settings_grupos.html', grupo_add=grupo_add_form, grupo_edit=Grupo_Add(), grupos=grupos(), params=params)
                else:
                    # NOTE set grupo_activo
                    session_sql.add(grupo_add)
                    session_sql.flush()
                    # session_sql.refresh(grupo_add)
                    if grupo_add_grupo_activo:
                        settings().grupo_activo_id = grupo_add.id
                        flash_toast(Markup('Grupo <strong>') + grupo_add_form.nombre.data + Markup('</strong>') + ' agregado' + Markup('<br>Ahora este tu grupo activo'), 'success')
                    else:
                        if settings().grupo_activo_id:
                            flash_toast(Markup('Grupo <strong>') + grupo_add_form.nombre.data + Markup('</strong>') + ' agregado' + Markup('<br>Si deseas usar este grupo debes activarlo'), 'success')
                        else:
                            settings().grupo_activo_id = grupo_add.id

                    session_sql.commit()
                    params['collapse_grupo_add'] = False
                    if params['login']:
                        return redirect(url_for('alumnos_html', params=dic_encode(params)))
                    else:
                        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
            else:
                flash_wtforms(grupo_add_form, flash_toast, 'warning')
            return render_template(
                'settings_grupos.html', grupo_add=grupo_add_form, grupo_edit=Grupo_Add(),
                grupos=grupos(), params=params)

        # XXX selector_grupo_edit_link
        if request.form['selector_button'] == 'selector_grupo_edit_link':
            params['collapse_grupo_edit'] = True
            params['grupo_edit_link'] = True
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

        # XXX selector_grupo_edit
        if request.form['selector_button'] == 'selector_grupo_edit':
            grupo_edit_form = Grupo_Add(request.form)
            params['collapse_grupo_edit'] = True
            params['grupo_edit_link'] = True
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            grupo_edit_grupo_activo_switch = request.form.get('grupo_edit_grupo_activo_switch')
            if not grupo_edit_grupo_activo_switch:
                grupo_edit_grupo_activo_switch = False
            if grupo_edit_form.validate():
                grupo_edit = Grupo(nombre=grupo_edit_form.nombre.data, tutor=grupo_edit_form.tutor.data, centro=grupo_edit_form.centro.data)
                grupo_sql = session_sql.query(Grupo).filter(Grupo.id == current_grupo_id).first()
                if grupo_sql.nombre.lower() != grupo_edit.nombre.lower() or grupo_sql.tutor.lower() != grupo_edit.tutor.lower() or grupo_sql.centro.lower() != grupo_edit.centro.lower() or str(settings().grupo_activo_id) != str(grupo_edit_grupo_activo_switch):
                    if grupo_sql.nombre.lower() != grupo_edit.nombre.lower():
                        grupo_sql.nombre = grupo_edit.nombre
                    if grupo_sql.tutor.lower() != grupo_edit.tutor.lower():
                        grupo_sql.tutor = grupo_edit.tutor
                    if grupo_sql.centro.lower() != grupo_edit.centro.lower():
                        grupo_sql.centro = grupo_edit.centro
                    if grupo_edit_grupo_activo_switch:
                        settings().grupo_activo_id = current_grupo_id
                    else:
                        settings().grupo_activo_id = None
                    flash_toast(Markup('Grupo <strong>') + grupo_edit.nombre + Markup('</strong>') + ' actualizado', 'success')
                    session_sql.commit()
                    return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
            else:
                flash_wtforms(grupo_edit_form, flash_toast, 'warning')
            return render_template(
                'settings_grupos.html', grupo_add=Grupo_Add(), grupos=grupos(), grupo_edit=grupo_edit_form, params=params)

        # XXX selector_grupo_edit_close
        if request.form['selector_button'] == 'selector_grupo_edit_close':
            return redirect(url_for('settings_grupos_html'))

        # XXX selector_grupo_edit_rollback
        if request.form['selector_button'] == 'selector_grupo_edit_rollback':
            params['collapse_grupo_edit'] = True
            params['grupo_edit_link'] = True
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            session_sql.rollback()
            return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

        # XXX selector_grupo_delete_link
        if request.form['selector_button'] == 'selector_grupo_delete_link':
            params['collapse_grupo_edit'] = True
            params['grupo_edit_link'] = True
            params['grupo_delete_link'] = True
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

        # XXX selector_grupo_delete
        if request.form['selector_button'] == 'selector_grupo_delete':
            grupo_delete_form = Grupo_Add(request.form)
            grupo_delete(current_grupo_id)
            flash_toast(Markup('Grupo <strong>') + grupo_delete_form.nombre.data + Markup('</strong>') + ' elminado', 'success')
            return redirect(url_for('settings_grupos_html'))

        # XXX selector_grupo_delete_close
        if request.form['selector_button'] == 'selector_grupo_delete_close':
            params['collapse_grupo_edit'] = True
            params['grupo_edit_link'] = True
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
    return render_template(
        'settings_grupos.html', grupo_add=Grupo_Add(), grupo_edit=Grupo_Add(), grupos=grupos(), params=params)


# XXX admin_citas
@app.route('/admin_citas', methods=['GET', 'POST'])
@app.route('/admin_citas/<params>', methods=['GET', 'POST'])
@login_required
def admin_citas_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)

    params = {}
    citas = session_sql.query(Cita).order_by(desc('created_at')).all()
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_cita_id'] = params_old.get('current_cita_id', 0)
    params['collapse_cita_edit'] = params_old.get('collapse_cita_edit', False)
    params['cita_delete_link'] = params_old.get('cita_delete_link', False)
    params['collapse_cita_add'] = params_old.get('collapse_cita_add', False)
    params['cita_edit_link'] = params_old.get('cita_edit_link', False)

    if request.method == 'POST':
        current_cita_id = current_id_request('current_cita_id')
        params['current_cita_id'] = current_cita_id
        # XXX cita_add
        if request.form['selector_button'] == 'selector_cita_add':
            params['collapse_cita_add'] = True
            cita_add_form = Cita_Add(request.form)
            if cita_add_form.validate():
                cita_add_visible = request.form.get('cita_add_visible')
                cita_add = Cita(frase=cita_add_form.frase.data, autor=cita_add_form.autor.data,  visible=cita_add_visible)
                # NOTE checking unicidad de frase
                cita_frase_sql = session_sql.query(Cita).filter(Cita.frase == cita_add_form.frase.data).first()
                if cita_frase_sql:
                    cita_add_form.frase.errors = ['']
                    flash_toast(Markup('<strong>') + 'Cita duplicada' + Markup('</strong>'), 'warning')
                    return render_template(
                        'admin_citas.html', cita_add=cita_add_form, cita_edit=Cita_Add(), citas=citas,
                        params=params)
                else:
                    session_sql.add(cita_add)
                    session_sql.commit()
                    flash_toast('Cita agregada', 'success')
                    return redirect(url_for('admin_citas_html', params=dic_encode(params)))
            else:
                flash_wtforms(cita_add_form, flash_toast, 'warning')
            return render_template(
                'admin_citas.html', cita_add=cita_add_form, cita_edit=Cita_Add(), citas=citas,
                params=params)

        if request.form['selector_button'] == 'selector_cita_add_close':
            return redirect(url_for('admin_citas_html'))

        # XXX selector_cita_edit_link
        if request.form['selector_button'] == 'selector_cita_edit_link':
            params['cita_edit_link'] = True
            params['collapse_cita_edit'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            return redirect(url_for('admin_citas_html', params=dic_encode(params)))

        # XXX cita_edit
        if request.form['selector_button'] == 'selector_cita_edit':
            params['cita_edit_link'] = True
            params['collapse_cita_edit'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            cita_edit_form = Cita_Add(request.form)
            cita_edit_visible = request.form.get('cita_edit_visible')
            if not cita_edit_visible:
                cita_edit_visible = False
            if cita_edit_form.validate():
                cita_edit = Cita(frase=cita_edit_form.frase.data, autor=cita_edit_form.autor.data, visible=cita_edit_visible)
                cita = session_sql.query(Cita).filter(Cita.id == current_cita_id).first()
                if cita.frase.lower() != cita_edit.frase.lower() or cita.autor.lower() != cita_edit.autor.lower() or str(cita.visible) != str(cita_edit_visible):
                    if cita.frase.lower() != cita_edit.frase.lower():
                        cita.frase = cita_edit.frase
                    if cita.autor.lower() != cita_edit.autor.lower():
                        cita.autor = cita_edit.autor
                    if cita.visible != cita_edit_visible:
                        cita.visible = cita_edit_visible
                    flash_toast('Cita actualizada', 'success')
                    session_sql.commit()
                    return redirect(url_for('admin_citas_html', params=dic_encode(params)))
            else:
                flash_wtforms(cita_edit_form, flash_toast, 'warning')
            return render_template(
                'admin_citas.html', cita_add=Cita_Add(), citas=citas, cita_edit=cita_edit_form,
                cita_edit_visible=cita_edit_visible, params=params)
        # XXX selector_cita_edit_close
        if request.form['selector_button'] == 'selector_cita_edit_close':
            return redirect(url_for('admin_citas_html'))

        # XXX cita_edit_rollback
        if request.form['selector_button'] == 'selector_cita_edit_rollback':
            params['collapse_cita_edit'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            session_sql.rollback()
            return redirect(url_for('admin_citas_html', params=dic_encode(params)))

        # XXX cita_delete_link
        if request.form['selector_button'] == 'selector_cita_delete_link':
            params['collapse_cita_edit'] = True
            params['cita_edit_link'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            params['cita_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('admin_citas_html', params=dic_encode(params)))

        # XXX cita_delete
        if request.form['selector_button'] == 'selector_cita_delete':
            cita_delete_form = Cita_Add(request.form)
            cita_sql = session_sql.query(Cita).filter(Cita.id == current_cita_id).first()
            session_sql.delete(cita_sql)
            flash_toast('Cita elminada', 'success')
            session_sql.commit()
            return redirect(url_for('admin_citas_html'))

        # XXX cita_delete_close
        if request.form['selector_button'] == 'selector_cita_delete_close':
            params['collapse_cita_edit'] = True
            params['cita_edit_link'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            return redirect(url_for('admin_citas_html', params=dic_encode(params)))

    return render_template(
        'admin_citas.html', cita_add=Cita_Add(), cita_edit=Cita_Add(), citas=citas,
        params=params)


# XXX informe_no_disponible
@app.route('/informe_no_disponible', methods=['GET', 'POST'])
def informe_no_disponible_html():
    return render_template('informe_no_disponible.html')

# XXX informe


@app.route('/informe/<current_tutoria_asignatura_id>/', methods=['GET', 'POST'])
@app.route('/informe/<current_tutoria_asignatura_id>/<params>', methods=['GET', 'POST'])
def informe_html(current_tutoria_asignatura_id, params={}):
    try:
        current_tutoria_asignatura_id = hashids_decode(current_tutoria_asignatura_id)
        current_tutoria_asignatura = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.id == current_tutoria_asignatura_id).first()
        current_tutoria_asignatura.tutoria_id
    except:
        return redirect(url_for('informe_no_disponible_html'))

    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')

    if request.method == 'POST':
        tutoria_id = current_tutoria_asignatura.tutoria_id
        asignatura_id = current_tutoria_asignatura.asignatura_id
        tutoria = tutoria_by_id(tutoria_id)
        asignatura = asignatura_by_id(asignatura_id)
        grupo = invitado_grupo(tutoria_id)
        alumno = invitado_alumno(tutoria_id)
        settings = invitado_settings(tutoria_id)
        informe_sql = invitado_informe(tutoria.id, asignatura.id)

        if not informe_sql:
            informe = Informe(tutoria_id=tutoria_id, asignatura_id=asignatura_id, comentario=request.form.get('comentario'))
            session_sql.add(informe)
            for pregunta in invitado_preguntas(settings.id):
                respuesta = Respuesta(informe_id=informe.id, pregunta_id=pregunta.id, resultado=request.form.get('pregunta_' + str(hashids_encode(pregunta.id))))
                session_sql.add(respuesta)
        else:
            informe = informe_sql
            informe.comentario = comentario = request.form.get('comentario')
            for pregunta in invitado_preguntas(settings.id):
                respuesta = invitado_respuesta(informe.id, pregunta.id)
                if not respuesta:
                    respuesta_add = Respuesta(informe_id=informe.id, pregunta_id=pregunta.id, resultado=request.form.get('pregunta_' + str(hashids_encode(pregunta.id))))
                    session_sql.add(respuesta_add)
                else:
                    respuesta.resultado = request.form.get('pregunta_' + str(hashids_encode(pregunta.id)))
        session_sql.commit()  # NOTE (NO BORRAR ESTA NOTA) este era el problema de no generar los graficos, era un problema de identado

        for prueba_evaluable in invitado_pruebas_evaluables(informe.id):
            prueba_evaluable.nota = request.form.get('prueba_evaluable_nota_' + str(hashids_encode(prueba_evaluable.id)))

        if request.form['selector_button'] == 'selector_prueba_evaluable_add':
            params['anchor'] = 'anchor_pru_eva'
            prueba_evaluable_nombre = request.form.get('prueba_evaluable_nombre')
            if not prueba_evaluable_nombre or prueba_evaluable_nombre == 'agregar prueba evaluable':
                prueba_evaluable = False
            prueba_evaluable_add = Prueba_Evaluable(informe_id=informe.id, nombre=prueba_evaluable_nombre, nota=0)
            session_sql.add(prueba_evaluable_add)
            return redirect(url_for('informe_html', current_tutoria_asignatura_id=hashids_encode(current_tutoria_asignatura_id), params=dic_encode(params)))

        if request.form['selector_button'] == 'selector_prueba_evaluable_delete':
            params['anchor'] = 'anchor_pru_eva'
            prueba_evaluable_delete = invitado_pruebas_evaluables(informe.id)[-1]
            session_sql.delete(prueba_evaluable_delete)
            session_sql.commit()
            return redirect(url_for('informe_html', current_tutoria_asignatura_id=hashids_encode(current_tutoria_asignatura_id), params=dic_encode(params)))

        if request.form['selector_button'] == 'selector_informe_add':
            session_sql.commit()
            flash_toast('Infome de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' enviado', 'success')
            params = {}
            params['current_tutoria_asignatura_id'] = current_tutoria_asignatura_id
            params['alumno'] = alumno.nombre + ' ' + alumno.apellidos
            params['grupo'] = grupo.nombre
            params['fecha'] = tutoria.fecha
            params['hora'] = tutoria.hora
            params['asignatura'] = asignatura.asignatura
            params['docente'] = asignatura.nombre + ' ' + asignatura.apellidos
            params['invitado'] = True
            return redirect(url_for('informe_success_html', params=dic_encode(params)))
        return render_template(
            'informe.html', tutoria=tutoria, asignatura=asignatura,
            alumno=alumno, grupo=grupo, informe=informe, params=params)

    else:
        tutoria_id = int(current_tutoria_asignatura.tutoria_id)
        asignatura_id = current_tutoria_asignatura.asignatura_id
        tutoria = tutoria_by_id(tutoria_id)
        asignatura = asignatura_by_id(asignatura_id)
        alumno = alumno_by_id(tutoria.alumno_id)
        settings = invitado_settings(tutoria_id)
        grupo = alumno_grupo(alumno.id)
        informe = invitado_informe(tutoria_id, asignatura_id)
        return render_template(
            'informe.html', tutoria=tutoria, asignatura=asignatura,
            alumno=alumno, grupo=grupo, informe=informe, current_tutoria_asignatura_id=current_tutoria_asignatura_id,
            params=params)

# XXX informe_success


@app.route('/informe_success/<params>', methods=['GET', 'POST'])
def informe_success_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    # params_anchor_off = True  # NOTE necesario para activar el anchor sin pasarlo por params
    params['current_tutoria_asignatura_id'] = params_old.get('current_tutoria_asignatura_id', 0)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['alumno'] = params_old.get('alumno', False)
    params['grupo'] = params_old.get('grupo', False)
    params['fecha'] = params_old.get('fecha', False)
    params['hora'] = params_old.get('hora', False)
    params['asignatura'] = params_old.get('asignatura', False)
    params['docente'] = params_old.get('docente', False)
    return render_template(
        'informe_success.html', params=params)


@app.route('/email_tutoria')
def tutoria_email_html():
    return render_template('email_tutoria.html')


# XXX asignaturas
@app.route('/asignaturas', methods=['GET', 'POST'])
@app.route('/asignaturas/<params>', methods=['GET', 'POST'])
@login_required
def asignaturas_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['collapse_asignatura_add'] = params_old.get('collapse_asignatura_add', False)
    params['collapse_asignatura_edit'] = params_old.get('collapse_asignatura_edit', False)
    params['current_asignatura_id'] = params_old.get('current_asignatura_id', 0)
    params['asignatura_delete_link'] = params_old.get('asignatura_delete_link', False)
    params['asignatura_edit_link'] = params_old.get('asignatura_edit_link', False)

    stats = {}
    stats['evolucion_tutorias_exito_grupo'] = evolucion_tutorias_exito_grupo(settings().grupo_activo_id)[0]
    stats['evolucion_tutorias_exito_grupo_media'] = evolucion_tutorias_exito_grupo(settings().grupo_activo_id)[1]

    if not settings().grupo_activo_id:
        params['collapse_grupo_add'] = True
        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

    if request.method == 'POST':
        # NOTE almacena current_asignatura_id para el resto de situacones
        current_asignatura_id = current_id_request('current_asignatura_id')
        params['current_asignatura_id'] = current_asignatura_id

        # XXX selector_asignatura_add
        if request.form['selector_button'] == 'selector_asignatura_add':
            params['anchor'] = 'anchor_asi_add'
            params['collapse_asignatura_add'] = True
            asignatura_add_form = Asignatura_Add(request.form)
            if asignatura_add_form.validate():
                asignatura_asignatura = session_sql.query(Asignatura).filter(Asignatura.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Asignatura.asignatura)) == unaccent(func.lower(asignatura_add_form.asignatura.data))).first()
                asignatura_email = session_sql.query(Asignatura).filter(Asignatura.grupo_id == settings().grupo_activo_id, func.lower(Asignatura.email) == func.lower(asignatura_add_form.email.data)).first()
                # if asignatura_asignatura:
                #     flash_toast('Esta asignatura ya existe', 'warning')
                # elif asignatura_email:
                #     flash_toast('Este email ya esta asignado a otra asignatura', 'warning')
                # else:
                #     asignatura_add = Asignatura(grupo_id=settings().grupo_activo_id, nombre=asignatura_add_form.nombre.data.title(), apellidos=asignatura_add_form.apellidos.data.title(), asignatura=asignatura_add_form.asignatura.data.title(), email=asignatura_add_form.email.data.lower())
                #     session_sql.add(asignatura_add)
                #     session_sql.commit()
                #     flash_toast('Asignatura agregada', 'success')
                #     return redirect(url_for('asignaturas_html'))
                asignatura_add = Asignatura(grupo_id=settings().grupo_activo_id, nombre=asignatura_add_form.nombre.data.title(), apellidos=asignatura_add_form.apellidos.data.title(), asignatura=asignatura_add_form.asignatura.data.title(), email=asignatura_add_form.email.data.lower())
                session_sql.add(asignatura_add)
                session_sql.commit()
                flash_toast('Asignatura agregada', 'success')
                return redirect(url_for('asignaturas_html'))
            else:
                flash_wtforms(asignatura_add_form, flash_toast, 'warning')
            return render_template(
                'asignaturas.html', asignatura_add=asignatura_add_form, asignatura_edit=Asignatura_Add(),
                params=params, stats=stats)

        # XXX selector_asignatura_add_cerrar
        if request.form['selector_button'] == 'selector_asignatura_add_cerrar':
            return redirect(url_for('asignaturas_html'))

        # XXX selector_asignatura_edit_link
        if request.form['selector_button'] == 'selector_asignatura_edit_link':
            params['collapse_asignatura_edit'] = True
            params['asignatura_edit_link'] = True
            params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))
            return redirect(url_for('asignaturas_html', params=dic_encode(params)))

        # XXX selector_asignatura_edit_link_close
        if request.form['selector_button'] == 'selector_asignatura_edit_link_close':
            params['collapse_asignatura_edit'] = True
            params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))
            return redirect(url_for('asignaturas_html', params=dic_encode(params)))

        # XXX selector_asignatura_edit_close
        if request.form['selector_button'] == 'selector_asignatura_edit_close':
            return redirect(url_for('asignaturas_html'))

        # XXX selector_asignatura_edit
        if request.form['selector_button'] == 'selector_asignatura_edit':
            params['collapse_asignatura_edit'] = True
            params['asignatura_edit_link'] = True
            asignatura_edit_form = Asignatura_Add(request.form)

            # XXX asignar alumnos
            # ****************************************
            alumnos_id_lista_encoded = request.form.getlist('alumno')
            alumnos_id_lista = []
            for alumno_id_encoded in alumnos_id_lista_encoded:
                alumnos_id_lista.append(hashids_decode(alumno_id_encoded))
            collapse_asignatura_edit_alumnos_contador = 0
            for alumno in alumnos_not_sorted():
                if alumno.id in alumnos_id_lista:
                    if not association_alumno_asignatura_check(alumno.id, current_asignatura_id):
                        alumno_asignatura_add = Association_Alumno_Asignatura(alumno_id=alumno.id, asignatura_id=current_asignatura_id)
                        session_sql.add(alumno_asignatura_add)
                        collapse_asignatura_edit_alumnos_contador += 1
                else:
                    if association_alumno_asignatura_check(alumno.id, current_asignatura_id):
                        alumno_asignatura_delete = session_sql.query(Association_Alumno_Asignatura).filter_by(alumno_id=alumno.id, asignatura_id=current_asignatura_id).first()
                        session_sql.delete(alumno_asignatura_delete)
                        collapse_asignatura_edit_alumnos_contador += 1

            if not asignatura_alumnos(current_asignatura_id):
                params['collapse_asignatura_edit'] = True
                params['collapse_asignaturas_edit_alumnos'] = True
                flash_toast('Debería asignar alumnos a ' + Markup('<strong>') + asignatura_edit_form.asignatura.data + Markup('</strong>'), 'warning')
            else:
                if collapse_asignatura_edit_alumnos_contador != 0:
                    params['collapse_asignatura_edit'] = True
                    params['collapse_asignaturas_edit_alumnos'] = True
                    flash_toast('Alumnos asignados', 'success')
                    collapse_asignatura_edit_alumnos_contador = 0
            session_sql.commit()  # NOTE agregado en caso de no modificar datos del alumno y solo asignacion de asignaturas
            # ****************************************

            if asignatura_edit_form.validate():
                params['collapse_asignatura_edit'] = True
                params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))

                # # NOTE unicidad del nombre de asignatura
                # asignatura_asignatura_unicidad = session_sql.query(Asignatura).filter(Asignatura.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Asignatura.asignatura)) == unaccent(func.lower(asignatura_edit_form.asignatura.data))).all()
                # asignatura_asignatura_unicidad_lista = []
                # for asignatura in asignatura_asignatura_unicidad:
                #     if asignatura.id != current_asignatura_id:
                #         asignatura_asignatura_unicidad_lista.append(asignatura.id)
                # if len(asignatura_asignatura_unicidad_lista) != 0:
                #     asignatura_edit_form.asignatura.errors = ['ya existe como asignatura.']
                #     flash_toast(Markup('<strong>') + asignatura_edit_form.asignatura.data + Markup('</strong>') + ' ya existe como asignatura.', 'warning')

                # NOTE unicidad del email
                # asignatura_email_unicidad = session_sql.query(Asignatura).filter(Asignatura.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Asignatura.email)) == unaccent(func.lower(asignatura_edit_form.email.data))).all()
                # if asignatura_email_unicidad:
                #     asignatura_email_unicidad_lista = []
                #     for asignatura in asignatura_email_unicidad:
                #         if asignatura.id != current_asignatura_id:
                #             asignatura_email_unicidad_lista.append(asignatura.id)
                #     if len(asignatura_email_unicidad_lista) != 0:
                #         asignatura_edit_form.email.errors = ['email asignado a otra asignatura.']
                #         flash_toast('Este email ya esta asignado a otra asignatura.', 'warning')

                asignatura_edit = Asignatura(grupo_id=settings().grupo_activo_id, nombre=asignatura_edit_form.nombre.data.title(), apellidos=asignatura_edit_form.apellidos.data.title(), asignatura=asignatura_edit_form.asignatura.data.title(), email=asignatura_edit_form.email.data)
                asignatura_sql = session_sql.query(Asignatura).filter(Asignatura.id == current_asignatura_id).first()
                if asignatura_sql.asignatura.lower() != asignatura_edit_form.asignatura.data.lower() or asignatura_sql.nombre.lower() != asignatura_edit_form.nombre.data.lower() or asignatura_sql.apellidos.lower() != asignatura_edit_form.apellidos.data.lower() or asignatura_sql.email.lower() != asignatura_edit_form.email.data.lower():
                    params['collapse_asignatura_edit'] = False
                    if asignatura_sql.asignatura.lower() != asignatura_edit_form.asignatura.data.lower():
                        asignatura_sql.asignatura = asignatura_edit_form.asignatura.data.title()
                        flash_toast(Markup('<strong>') + asignatura_edit_form.asignatura.data + Markup('</strong>') + ' actualizado', 'success')
                    if asignatura_sql.nombre.lower() != asignatura_edit_form.nombre.data.lower():
                        asignatura_sql.nombre = asignatura_edit_form.nombre.data.title()
                        flash_toast(Markup('<strong>') + asignatura_edit_form.nombre.data + Markup('</strong>') + ' actualizado', 'success')
                    if asignatura_sql.apellidos.lower() != asignatura_edit_form.apellidos.data.lower():
                        asignatura_sql.apellidos = asignatura_edit_form.apellidos.data.title()
                        flash_toast(Markup('<strong>') + asignatura_edit_form.apellidos.data + Markup('</strong>') + ' actualizado', 'success')
                    if asignatura_sql.email.lower() != asignatura_edit_form.email.data.lower():
                        asignatura_sql.email = asignatura_edit_form.email.data
                        flash_toast(Markup('<strong>') + asignatura_edit_form.email.data + Markup('</strong>') + ' actualizado', 'success')
                session_sql.commit()
                return redirect(url_for('asignaturas_html', params=dic_encode(params)))
            else:
                flash_wtforms(asignatura_edit_form, flash_toast, 'warning')
            return render_template(
                'asignaturas.html', asignatura_add=Asignatura_Add(), asignatura_edit=asignatura_edit_form,
                params=params, stats=stats)

        # XXX asignatura_edit_rollback
        if request.form['selector_button'] == 'selector_asignatura_edit_rollback':
            params['asignatura_edit_link'] = True
            params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))
            session_sql.rollback()
            return redirect(url_for('asignaturas_html', params=dic_encode(params)))

        # XXX asignatura_delete_link
        if request.form['selector_button'] == 'selector_asignatura_delete_link':
            params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))
            params['asignatura_edit_link'] = True
            params['asignatura_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('asignaturas_html', params=dic_encode(params)))

        # XXX asignatura_delete
        if request.form['selector_button'] == 'selector_asignatura_delete':
            asignatura_delete_form = Asignatura_Add(request.form)
            asignatura_delete(current_asignatura_id)
            flash_toast('Asignatura elminada', 'success')
            return redirect(url_for('asignaturas_html'))

        # XXX asignatura_delete_close
        if request.form['selector_button'] == 'selector_asignatura_delete_close':
            params['asignatura_edit_link'] = True
            params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))
            return redirect(url_for('asignaturas_html', params=dic_encode(params)))

    return render_template(
        'asignaturas.html', asignatura_add=Asignatura_Add(), asignatura_edit=Asignatura_Add(),
        asignaturas=asignaturas, params=params, stats=stats)


@app.route('/user_add', methods=['GET', 'POST'])
def user_add_html():
    params = {}
    user_add_form = User_Add(request.form)
    if request.method == 'POST':
        if user_add_form.validate():
            user_username = session_sql.query(User).filter(func.lower(User.username) == func.lower(user_add_form.username.data)).first()
            user_email = session_sql.query(User).filter(func.lower(User.email) == func.lower(user_add_form.email.data)).first()
            if user_username:
                flash_toast(Markup('<strong>') + user_add_form.username.data + Markup('</strong>') + ' ya esta registrado', 'warning')
            elif user_email:
                flash_toast(Markup('<strong>') + user_add_form.email.data + Markup('</strong>') + ' ya esta registrado', 'warning')
            else:
                hashed_password = generate_password_hash(user_add_form.password.data, method='sha256')
                user_add = User(username=user_add_form.username.data, password=hashed_password, email=user_add_form.email.data)
                session_sql.add(user_add)
                session_sql.flush()
                session_sql.refresh(user_add)
                # crea el registro en Settings.
                settings_add = Settings(user_id=user_add.id)
                session_sql.add(settings_add)
                preguntas_active_default(user_add.id)  # inserta las preguntas activas by default
                settings_add.diferencial = settings_admin().diferencial
                params['current_user_id'] = user_add.id

                if user_add.email == 'antonioelmatematico@gmail.com':
                    settings_add.role = 'admin'
                    settings_add.email_validated = True
                session_sql.commit()
                send_email_validate_asincrono(user_add.id)
                return redirect(url_for('login_validacion_email_html', params=dic_encode(params)))
        else:
            flash_wtforms(user_add_form, flash_toast, 'warning')
        return render_template('user_add.html', user_add=user_add_form)
    return render_template('user_add.html', user_add=User_Add())


@app.route('/login_validacion_email/<params>', methods=['GET', 'POST'])
@app.route('/login_validacion_email', methods=['GET', 'POST'])
def login_validacion_email_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['email_validated_intentos'] = params_old.get('email_validated_intentos', 5)
    params['current_user_id'] = params_old.get('current_user_id', 0)
    current_user_id = params['current_user_id']

    if request.method == 'POST':
        params['current_user_id'] = current_id_request('current_user_id')
        current_user_id = params['current_user_id']
        email_validated_intentos_add = settings_by_id(current_user_id).email_validated_intentos + 1
        settings_edit = settings_by_id(current_user_id)
        settings_edit.email_validated_intentos = email_validated_intentos_add
        session_sql.commit()
        params['email_validated_intentos'] = email_validated_intentos_add
        send_email_validate_asincrono(current_user_id)
        return redirect(url_for('login_validacion_email_html', params=dic_encode(params)))
    else:
        if current_user_id != 0:
            params['email_validated_intentos'] = settings_by_id(current_user_id).email_validated_intentos

    return render_template('login_validacion_email.html', params=params)


@app.route('/email_validate/<params>')
def email_validate_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['current_user_id'] = params_old.get('current_user_id', False)
    current_user_id = params['current_user_id']
    params['email_robinson'] = params_old.get('email_robinson', False)
    user_sql = session_sql.query(User).filter(User.id == current_user_id).first()
    if user_sql:
        if params['email_robinson']:
            settings_by_id(user_sql.id).email_robinson = True
            session_sql.commit()
            return redirect(url_for('lista_robinson_html'))
        else:
            settings_by_id(user_sql.id).email_validated = True
            settings_by_id(user_sql.id).email_robinson = False
            if settings_by_id(user_sql.id).email_validated_intentos != 1:
                settings_by_id(user_sql.id).email_validated_intentos = 1
            session_sql.commit()
            login_user(user_sql, remember=True)
            flash_toast('Enhorabuena, cuenta activada.', 'success')
            flash_toast('Bienvenido ' + current_user.username, 'success')
            return redirect(url_for('wellcome_html'))
    else:
        return redirect(url_for('login_html'))


@app.route('/lista_robinson')
def lista_robinson_html():
    params = {}
    return render_template('lista_robinson.html', params=params)


@app.route('/password_reset_request', methods=['GET', 'POST'])
@app.route('/password_reset_request/<params>', methods=['GET', 'POST'])
def password_reset_request_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['user_check'] = params_old.get('user_check', False)
    params['email_robinson'] = params_old.get('email_robinson', False)
    if request.method == 'POST':
        password_reset_request_form = Password_Reset_Request(request.form)
        if password_reset_request_form.validate():
            user_sql = session_sql.query(User).filter_by(username=password_reset_request_form.username.data, email=password_reset_request_form.email.data).first()
            if user_sql:
                if settings_by_id(user_sql.id).email_robinson:
                    params['email_robinson'] = True
                    flash_toast('Usuario en lista Robinson.', 'warning')
                    return redirect(url_for('password_reset_request_html', params=dic_encode(params)))
                send_email_password_reset_request_asincrono(user_sql.id)
                params['user_check'] = True
                return redirect(url_for('password_reset_request_html', params=dic_encode(params)))
            else:
                flash_toast('Usurio no registrado con este email.', 'warning')
        else:
            flash_wtforms(password_reset_request_form, flash_toast, 'warning')
        return render_template('password_reset_request.html', password_reset_request=password_reset_request_form, params=params)
    return render_template('password_reset_request.html', password_reset_request=Password_Reset_Request(), params=params)


@app.route('/password_reset', methods=['GET', 'POST'])
@app.route('/password_reset/<params>', methods=['GET', 'POST'])
def password_reset_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_user_id'] = params_old.get('current_user_id', 0)
    if request.method == 'POST':
        password_reset_form = Password_Reset(request.form)
        if password_reset_form.validate():
            current_user_id = current_id_request('current_user_id')
            params['current_user_id'] = current_user_id
            user_sql = user_by_id(current_user_id)
            if user_sql:
                hashed_password = generate_password_hash(password_reset_form.password.data, method='sha256')
                user_sql.password = hashed_password
                settings_by_id(current_user_id).email_robinson = False
                params['password_reset'] = True
                session_sql.commit
                return redirect(url_for('login_html', params=dic_encode(params)))
            else:
                flash_toast('Este enlace ha caducado.', 'warning')
        else:
            flash_wtforms(password_reset_form, flash_toast, 'warning')
        return render_template('password_reset.html', password_reset=password_reset_form, params=params)
    return render_template('password_reset.html', password_reset=Password_Reset(), params=params)


# XXX login


@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/<params>', methods=['GET', 'POST'])
def login_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['ban'] = params_old.get('ban', False)
    params['email_validated'] = params_old.get('email_validated', False)
    params['login_fail'] = params_old.get('login_fail', False)
    params['password_reset'] = params_old.get('password_reset', False)
    params['email_robinson'] = params_old.get('email_robinson', False)
    session.clear()
    login_form = User_Login(request.form)
    if request.method == 'POST':
        if login_form.validate():
            user_sql = session_sql.query(User).filter_by(username=login_form.username.data).first()
            if params['ban']:
                return render_template('login.html', user_login=login_form, params=params)

            if user_sql:
                if check_password_hash(user_sql.password, login_form.password.data):
                    login_user(user_sql, remember=login_form.remember.data)
                    settings = settings_by_id(user_sql.id)
                    settings.visit_last = datetime.datetime.now()
                    settings.visit_number = settings.visit_number + 1
                    session_sql.commit()
                    if settings.ban:
                        params['ban'] = True
                        params['login_fail'] = False
                        logout_user()
                        return redirect(url_for('login_html', params=dic_encode(params)))
                    if settings.email_robinson:
                        params['email_robinson'] = True
                        params['login_fail'] = False
                        logout_user()
                        return redirect(url_for('login_html', params=dic_encode(params)))
                    if not settings.email_validated:
                        params['current_user_id'] = user_sql.id
                        params['login_fail'] = False
                        params['email_validated_intentos'] = settings.email_validated_intentos
                        settings.email_validated_intentos = settings.email_validated_intentos + 1
                        logout_user()
                        session_sql.commit()
                        return redirect(url_for('login_validacion_email_html', params=dic_encode(params)))
                    else:
                        pass
                    # NOTE sincronizar con google calendar (ahora esta en /alumnos)
                    # tutoria_calendar_sync()
                    flash_toast('Bienvenido ' + Markup('<strong>') + login_form.username.data + Markup('</strong>'), 'success')
                    if not settings.grupo_activo_id:
                        params['login'] = True  # NOTE Para activar como activo el primer grupo creado y redirect a alumnos (por facilidad para un nuevo usuario)
                        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
                    return redirect(url_for('alumnos_html'))
                else:
                    login_form.password.errors = ['']
                    flash_toast('Contraseña incorrecta', 'warning')
                    params['login_fail'] = True
                    return render_template('login.html', user_login=login_form, params=params)
            else:
                login_form.username.errors = ['']
                flash_toast('Usuario no registrado', 'warning')
                params['login_fail'] = True
                return render_template('login.html', user_login=login_form, params=params)
        else:
            flash_wtforms(login_form, flash_toast, 'warning')
            params['login_fail'] = True
            return render_template('login.html', user_login=login_form, params=params)
    return render_template('login.html', user_login=User_Login(), params=params)


@app.route('/logout')
def logout_html():
    params = {}
    logout_user()
    flash_toast('Session cerrada', 'success')
    return render_template('logout.html', params=params)
