from app import app
from functions import *
import functions
# *************************************

# Fuerza el reload de los archivos de static
# **********************************************


@app.url_defaults
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
# **********************************************
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
    try:
        g.settings_current_user = session_sql.query(Settings).filter(Settings.id == current_user.id).first()
    except:
        pass
    try:
        g.settings_global = session_sql.query(Settings_Global).first()
    except:
        pass


@app.after_request
def after_request_html(response):
    Session_SQL.remove()
    return response


@app.route('/getos')
def getos():
    return (os.name)


@app.errorhandler(404)
def page_not_found_html(warning):
    return render_template('page_not_found.html')


@app.errorhandler(500)
def internal_server_error_html(critical):
    abort_asincrono(500)
    return render_template('internal_server_error.html')


@app.route('/')
def index_html():
    # return redirect(url_for('alumnos_html'))
    return redirect(url_for('tutorias_html'))


@app.route('/tutorias', methods=['GET', 'POST'])
@app.route('/tutorias/<params>', methods=['GET', 'POST'])
@login_required
def tutorias_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_alumno_id'] = params_old.get('current_alumno_id', 0)
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
    params['tutoria_delete_confirmar'] = params_old.get('tutoria_delete_confirmar', False)
    params['tutorias_deleted_vaciar_papelera'] = params_old.get('tutorias_deleted_vaciar_papelera', False)
    params['tutoria_restaurar'] = params_old.get('tutoria_restaurar', False)
    params['alumno_delete_confirmar'] = params_old.get('alumno_delete_confirmar', False)
    params['current_alumno_id'] = params_old.get('current_alumno_id', 0)
    params['tutoria_solicitar'] = params_old.get('tutoria_solicitar', False)
    params['alumnos_tutorias_solicitar'] = params_old.get('alumnos_tutorias_solicitar', False)
    params['alumno_apellidos_nombre'] = params_old.get('alumno_apellidos_nombre', False)

    current_alumno_id = params['current_alumno_id']
    current_tutoria_id = params['current_tutoria_id']

    alumnos = session_sql.query(Alumno).filter_by(grupo_id=g.settings_current_user.grupo_activo_id).all()  # FIXME habra que filtrar por grupo_activo
    alumnos_autocomplete = []

    if params['tutorias_deleted_vaciar_papelera']:
        params['tutorias_deleted_vaciar_papelera'] = False
        tutorias = tutorias_by_grupo_id(g.settings_current_user.grupo_activo_id, deleted=True)
        for tutoria in tutorias:
            session_sql.delete(tutoria)
        session_sql.commit()
        flash_toast('Papelera vaciada', 'success')
        return redirect(url_for('tutorias_html', params=dic_encode(params)))

    if params['tutoria_restaurar']:
        params['tutoria_restaurar'] = False
        tutoria = tutoria_by_id(current_tutoria_id)
        tutoria.deleted = False
        session_sql.commit()
        if g.settings_current_user.calendar:
            try:
                credentials = oauth2client.client.Credentials.new_from_json(g.settings_current_user.oauth2_credentials)
                http = httplib2.Http()
                http = credentials.authorize(http)
                service = discovery.build('calendar', 'v3', http=http)
            except:
                return redirect(url_for('oauth2callback_calendar'))
            alumno_nombre = alumno_by_tutoria_id(current_tutoria_id).nombre
            calendar_datetime_utc_start_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute).replace(tzinfo='Europe/Madrid'))
            calendar_datetime_utc_end_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute + g.settings_current_user.tutoria_duracion).replace(tzinfo='Europe/Madrid'))
            tutoria_calendar_add(service, tutoria, calendar_datetime_utc_start_arrow, calendar_datetime_utc_end_arrow, alumno_nombre)
        flash_toast('Tutoria restaurada', 'success')
        return redirect(url_for('tutorias_html', params=dic_encode(params)))

    if params['tutoria_delete_confirmar']:
        params['tutoria_delete_confirmar'] = False
        tutoria = tutoria_by_id(current_tutoria_id)
        session_sql.delete(tutoria)
        session_sql.commit()
        flash_toast('Tutoria eliminada', 'success')
        return redirect(url_for('tutorias_html', params=dic_encode(params)))

    if params['alumnos_tutorias_solicitar']:
        params['alumnos_tutorias_solicitar'] = False
        params['tutoria_solicitar'] = True
        alumno = alumno_by_id(current_alumno_id)
        params['alumno_apellidos_nombre'] = alumno.apellidos + ', ' + alumno.nombre
        print('alumno: ', params['alumno_apellidos_nombre'])
        return redirect(url_for('tutorias_html', params=dic_encode(params)))

    if request.method == 'POST':
        current_alumno_id = request.form.get('alumno_id')

        if request.form['selector_button'] == 'selector_tutoria_add':
            params['tutoria_solicitar'] = True
            if not current_alumno_id:
                flash_toast('Debes asignar un alumno', 'warning')
                return redirect(url_for('tutorias_html', params=dic_encode(params)))
            current_tutoria_id = current_id_request('current_tutoria_id')
            params['current_tutoria_id'] = current_tutoria_id
            params['anchor'] = 'anchor_alu_' + str(hashids_encode(current_alumno_id))
            params['collapse_alumno'] = True
            params['collapse_tutoria_add'] = True
            tutoria_add_form = Tutoria_Add(current_alumno_id=current_alumno_id, fecha=request.form.get('fecha'), hora=request.form.get('hora'))

            # NOTE check si hay asignaturas asignadas al grupo
            if not asignaturas_not_sorted():
                params['collapse_asignatura_add'] = True
                flash_toast('Tutoria no solicitada' + Markup('<br>') + 'Debes asignar alguna asignatura', 'warning')
                return redirect(url_for('asignaturas_html', params=dic_encode(params)))

            # NOTE check si hay asignaturas asignadas al alumno
            if not asignaturas_alumno_by_alumno_id(current_alumno_id):
                params['collapse_alumno_edit'] = True
                params['alumno_edit_link'] = True
                params['collapse_alumno_edit_asignaturas'] = True
                flash_toast('Tutoria no solicitada' + Markup('<br>') + 'Debes asignar alguna asignatura', 'warning')
                return redirect(url_for('tutorias_html', params=dic_encode(params)))

            # NOTE check si hay preguntas asignadas en el cuestionario
            if not informe_preguntas():
                params['current_alumno_id'] = current_alumno_id
                flash_toast('Tutoria no solicitada' + Markup('<br>') + 'Debes asignar preguntas al cuestionario', 'warning')
                return redirect(url_for('settings_cuestionario_html', params=dic_encode(params)))

            else:
                if tutoria_add_form.validate():
                    tutoria_add_form_fecha = datetime.datetime.strptime(tutoria_add_form.fecha.data, '%d-%m-%Y').strftime('%Y-%m-%d')
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
                            flash_toast('Ya existe esta tutoría' + Markup('<br>') + 'Es aconsejable editarla', 'warning')
                            # FIXME: parametros_url
                            params['current_tutoria_id'] = tutoria_sql.id
                            return redirect(url_for('tutorias_html', params=dic_encode(params)))
                        else:
                            session_sql.add(tutoria_add)
                            session_sql.flush()
                            tutoria_id = tutoria_add.id
                            # NOTE si se desea eliminar el commit hay que usar el FLUSH y recuperar la fecha con datetime.datetime.strptime(tutoria_add.fecha, '%Y-%m-%d').strftime('%d')
                            # tutoria_dia_semana = translate_fecha(datetime.datetime.strptime(tutoria_add.fecha, '%Y-%m-%d').strftime('%A'))
                            # tutoria_dia_mes = datetime.datetime.strptime(tutoria_add.fecha, '%Y-%m-%d').strftime('%d')
                            session_sql.commit()  # NOTE necesario para simplificar y unificar como traducir la fecha
                            tutoria = tutoria_by_id(tutoria_id)
                            # NOTE anular email
                            send_email_tutoria_asincrono(alumno, tutoria)  # NOTE anular temporalemente para pruebas de envio de mails.
                            params['tutoria_solicitar'] = False
                            flash_toast('Tutoria generada.' + Markup('<br>') + 'Enviando emails al equipo educativo.', 'info')
                            params['current_alumno_id'] = current_alumno_id
                            params['collapse_alumno'] = True
                            params['collapse_tutorias'] = True
                            params['anchor'] = 'anchor_top'
                            # NOTE comprobar permisos de oauth2
                            if g.settings_current_user.calendar:
                                try:
                                    credentials = oauth2client.client.Credentials.new_from_json(g.settings_current_user.oauth2_credentials)
                                    http = httplib2.Http()
                                    http = credentials.authorize(http)
                                    service = discovery.build('calendar', 'v3', http=http)
                                except:
                                    return redirect(url_for('oauth2callback_calendar'))

                               # NOTE agregar eventos a la agenda
                                tutoria_hora = datetime.datetime.strptime(tutoria_add_form.hora.data, '%H:%M')
                                tutoria_fecha = tutoria_add_form.fecha.data
                                alumno_nombre = alumno.nombre

                                calendar_datetime_utc_start = (datetime.datetime.strptime(tutoria_fecha, '%d-%m-%Y') + datetime.timedelta(hours=tutoria_hora.hour) + datetime.timedelta(minutes=tutoria_hora.minute)).timestamp()
                                calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start).replace(tzinfo='Europe/Madrid'))
                                calendar_datetime_utc_end = (datetime.datetime.strptime(tutoria_fecha, '%d-%m-%Y') + datetime.timedelta(hours=tutoria_hora.hour) + datetime.timedelta(minutes=(tutoria_hora.minute + g.settings_current_user.tutoria_duracion))).timestamp()
                                calendar_datetime_utc_end_arrow = str(arrow.get(calendar_datetime_utc_end).replace(tzinfo='Europe/Madrid'))

                                tutoria_calendar_add(service, tutoria_add, calendar_datetime_utc_start_arrow, calendar_datetime_utc_end_arrow, alumno_nombre)
                            return redirect(url_for('tutorias_html', params=dic_encode(params)))
                else:
                    flash_wtforms(tutoria_add_form, flash_toast, 'warning')
            return render_template(
                'tutorias.html', alumno_add=Alumno_Add(), alumno_edit=Alumno_Add(),
                tutoria_add=tutoria_add_form, params=params)

    # XXX purgar papelera tutorias (en el futuro sera un servicio que se ejecute por las noches cuando el servidor tenga pocas visitas)
    if g.settings_current_user.role == 'admin':
        purgar_papelera_tutorias()

    # XXX sincronizar con google calendar
    tutoria_calendar_sync()

    # XXX tutorias_timeout
    tutorias_timeout()
    return render_template('tutorias.html', alumnos_autocomplete=alumnos, tutoria_add=Tutoria_Add(), params=params)


# XXX pruebas

@app.route('/test', methods=['GET', 'POST'])
@login_required
def test_html():

    # XXX alumno_add
    if request.method == 'POST':
        if request.form['selector_button'] == 'selector_alumno_add':
            alumno_add_form = Alumno_Add(grupo_id=6, nombre=request.form.get('nombre'), apellidos=request.form.get('apellidos'))
            if alumno_add_form.validate():
                alumno_add = Alumno(grupo_id=6, apellidos=alumno_add_form.apellidos.data, nombre=alumno_add_form.nombre.data)
                session_sql.add(alumno_add)
                session_sql.commit()
                flash_toast(alumno_add_form.nombre.data + ' agregado', 'success')
                return redirect(url_for('test_html'))
            else:
                flash_wtforms(alumno_add_form, flash_toast, 'warning')
                return render_template('test.html', alumno_add=alumno_add_form)
    return render_template('test.html', alumno_add=Alumno_Add())


@app.route('/pagina_2', methods=['GET', 'POST'])
@login_required
def pagina_2_html():

    return redirect(url_for('test_html', params=params))


@app.route('/oauth2callback_calendar')
def oauth2callback_calendar():
    flow = client.flow_from_clientsecrets('static/credentials/client_secret.json', scope='https://www.googleapis.com/auth/calendar', redirect_uri=index_link + 'oauth2callback_calendar')
    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        g.settings_current_user.oauth2_credentials = credentials.to_json()
        session_sql.commit()
    return redirect(url_for('settings_opciones_html'))


@app.route('/oauth2callback_gmail')
def oauth2callback_gmail():
    flow = client.flow_from_clientsecrets('static/credentials/client_secret.json', scope='https://www.googleapis.com/auth/gmail.send', redirect_uri=index_link + 'oauth2callback_gmail')
    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        g.settings_global.oauth2_credentials = credentials.to_json()
        session_sql.commit()
    return redirect(url_for('admin_settings_global_html'))


# XXX admin_settings_global
@app.route('/admin_settings_global', methods=['GET', 'POST'])
@app.route('/admin_settings_global/<params>', methods=['GET', 'POST'])
@login_required
def admin_settings_global_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    tutorias_clenaup_count = session_sql.query(Tutoria).filter(Tutoria.fecha < g.current_date - datetime.timedelta(days=30 * g.settings_global.periodo_cleanup_tutorias)).count()
    # session.clear()
    if request.method == 'POST':
        periodo_cleanup_tutorias = int(request.form.get('periodo_cleanup_tutorias'))
        cleanup_tutorias_automatic = request.form.get('cleanup_tutorias_automatic')
        gmail_sender = request.form.get('gmail_sender')
        if not cleanup_tutorias_automatic:
            cleanup_tutorias_automatic = False

        # XXX selector_autorizar_credencial
        if request.form['selector_button'] == 'selector_autorizar_credencial':
            return redirect(url_for('oauth2callback_gmail'))

            # XXX selector_cleanup_update
        if request.form['selector_button'] == 'selector_cleanup_update':
            if g.settings_global.periodo_cleanup_tutorias != periodo_cleanup_tutorias:
                g.settings_global.periodo_cleanup_tutorias = periodo_cleanup_tutorias
                session_sql.commit()
                flash_toast('Tutorias CleanUp actualizado', 'success')
            return redirect(url_for('admin_settings_global_html'))

        # XXX selector_global_set_edit
        if request.form['selector_button'] == 'selector_global_set_edit':
            commit_action = False
            if g.settings_global.periodo_cleanup_tutorias != int(periodo_cleanup_tutorias):
                g.settings_global.periodo_cleanup_tutorias = periodo_cleanup_tutorias
                commit_action = True
            if g.settings_global.periodo_participacion_recent != int(request.form.get('periodo_participacion_recent')):
                g.settings_global.periodo_participacion_recent = request.form.get('periodo_participacion_recent')
                commit_action = True
            if g.settings_global.diferencial_default != int(request.form.get('diferencial_default')):
                g.settings_global.diferencial_default = request.form.get('diferencial_default')
                commit_action = True
            if str(g.settings_global.cleanup_tutorias_automatic) != str(cleanup_tutorias_automatic):
                g.settings_global.cleanup_tutorias_automatic = cleanup_tutorias_automatic
                commit_action = True
            if str(g.settings_global.periodo_deleted_tutorias) != str(request.form.get('periodo_deleted_tutorias')):
                g.settings_global.periodo_deleted_tutorias = request.form.get('periodo_deleted_tutorias')
                commit_action = True

            settings_global_edit_form = Settings_Global_Add(gmail_sender=gmail_sender)
            if settings_global_edit_form.validate():
                settings_global_edit = Settings_Global_Add(gmail_sender=gmail_sender)
                if g.settings_global.gmail_sender != gmail_sender:
                    g.settings_global.gmail_sender = gmail_sender
                    commit_action = True
            else:
                flash_wtforms(settings_global_edit_form, flash_toast, 'warning')
                return render_template('admin_settings_global.html',
                                       settings_global_edit=settings_global_edit_form)
            if commit_action:
                session_sql.commit()
                flash_toast('Global Set actualizado', 'success')
            return redirect(url_for('admin_settings_global_html'))

        if request.form['selector_button'] == 'selector_cleanup_tutorias':
            if g.settings_global.periodo_cleanup_tutorias != periodo_cleanup_tutorias:
                g.settings_global.periodo_cleanup_tutorias = periodo_cleanup_tutorias
            cleanpup_tutorias(periodo_cleanup_tutorias)
            return redirect(url_for('admin_settings_global_html'))

    return render_template('admin_settings_global.html',
                           settings_global_edit=Settings_Global_Add(), tutorias_clenaup_count=tutorias_clenaup_count)


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

    emails_validados_count_sql = emails_validados_count()
    stats['emails_validados'] = emails_validados_count_sql[0]
    stats['emails_validados_percent'] = emails_validados_count_sql[1]

    emails_no_robinson_count_sql = emails_no_robinson_count()
    stats['emails_no_robinson'] = emails_no_robinson_count_sql[0]
    stats['emails_no_robinson_percent'] = emails_no_robinson_count_sql[1]

    emails_no_ban_count_sql = emails_no_ban_count()
    stats['emails_no_ban'] = emails_no_ban_count_sql[0]
    stats['emails_no_ban_percent'] = emails_no_ban_count_sql[1]

    tutoria_timeout_count_sql = tutoria_timeout_count()
    stats['tutoria_timeout'] = tutoria_timeout_count_sql[0]
    stats['tutoria_timeout_percent'] = tutoria_timeout_count_sql[1]

    evolucion_equipo_educativo_count_sql = evolucion_equipo_educativo_count()
    stats['evolucion_equipo_educativo'] = evolucion_equipo_educativo_count_sql[0]
    stats['evolucion_equipo_educativo_percent'] = evolucion_equipo_educativo_count_sql[1]

    stats['tutorias_all_count'] = tutorias_all_count()
    tutorias_con_respuesta_count_sql = tutorias_con_respuesta_count()
    stats['tutorias_con_respuesta'] = tutorias_con_respuesta_count_sql[0]
    stats['tutorias_con_respuesta_percent'] = tutorias_con_respuesta_count_sql[1]

    stats['tutorias_con_acuerdo_count'] = tutorias_con_acuerdo_count()

    preguntas_por_cuestionario_sql = preguntas_por_cuestionario()
    stats['preguntas_por_cuestionario_min'] = preguntas_por_cuestionario_sql[0]
    stats['preguntas_por_cuestionario_media'] = preguntas_por_cuestionario_sql[1]
    stats['preguntas_por_cuestionario_max'] = preguntas_por_cuestionario_sql[2]
    stats['preguntas_por_cuestionario_percent'] = preguntas_por_cuestionario_sql[3]

    profesores_por_usuario_sql = profesores_por_usuario()
    stats['profesores_all_count'] = profesores_all_cunt()
    stats['profesores_por_usuario_min'] = profesores_por_usuario_sql[0]
    stats['profesores_por_usuario_media'] = profesores_por_usuario_sql[1]
    stats['profesores_por_usuario_max'] = profesores_por_usuario_sql[2]

    profesores_actividad_count_sql = profesores_actividad_count()
    stats['profesores_actividad'] = profesores_actividad_count_sql[0]
    stats['profesores_actividad_percent'] = profesores_actividad_count_sql[1]
    stats['profesores_activos_evolucion'] = profesores_actividad_count_sql[2]
    stats['profesores_activos_evolucion_frecuencia'] = profesores_actividad_count_sql[3]
    stats['profesores_activos_evolucion_frecuencia_absoluta'] = profesores_actividad_count_sql[4]
    stats['profesores_activos_evolucion_media'] = profesores_actividad_count_sql[5]

    tutorias_por_usuario_count_sql = tutorias_por_usuario_count()
    stats['tutorias_por_usuario_min'] = tutorias_por_usuario_count_sql[0]
    stats['tutorias_por_usuario_media'] = tutorias_por_usuario_count_sql[1]
    stats['tutorias_por_usuario_max'] = tutorias_por_usuario_count_sql[2]

    stats['cuestionario_actividad'] = cuestionario_actividad()

    informes_con_comentario_count_sql = informes_con_comentario_count()
    stats['informes_con_comentario'] = informes_con_comentario_count_sql[0]
    stats['informes_con_comentario_percent'] = informes_con_comentario_count_sql[1]

    informes_con_pruebas_evalubles_count_sql = informes_con_pruebas_evalubles_count()
    stats['informes_con_pruebas_evalubles'] = informes_con_pruebas_evalubles_count_sql[0]
    stats['informes_con_pruebas_evalubles_percent'] = informes_con_pruebas_evalubles_count_sql[1]
    stats['pruebas_evaluables_evolucion'] = informes_con_pruebas_evalubles_count_sql[2]

    stats['diferencial_media'] = diferencial_media()

    stats['tutores_over_all'] = (20 * stats['emails_validados_percent'] + 20 * stats['emails_no_ban_percent'] + 10 * stats['emails_no_robinson_percent'] + 40 * stats['preguntas_por_cuestionario_percent'] + 10 * stats['evolucion_equipo_educativo_percent']) / 100
    stats['profesores_over_all'] = (50 * stats['tutorias_con_respuesta_percent'] + 30 * stats['profesores_actividad_percent'] + 10 * stats['informes_con_pruebas_evalubles_percent'] + 10 * stats['informes_con_comentario_percent']) / 100
    # --------------------------------
    return render_template(
        'admin_estadisticas.html', params=params, stats=stats)


# XXX admin_usuario_ficha
@app.route('/admin_usuario_ficha', methods=['GET', 'POST'])
@app.route('/admin_usuario_ficha/<params>', methods=['GET', 'POST'])
@login_required
def admin_usuario_ficha_html(params={}):
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
    params['admin_usuario_data_delete_confirmar'] = params_old.get('admin_usuario_data_delete_confirmar', False)
    current_usuario_id = params['current_usuario_id']

    try:
        usuario = user_by_id(current_usuario_id)
    except:
        abort(404)

    if params['admin_usuario_data_delete_confirmar']:
        session_sql.delete(usuario)
        session_sql.commit()
        flash_toast('Usuario elminado', 'success')
        return redirect(url_for('admin_usuarios_html'))

    if request.method == 'POST':
        usuario_edit_form = Usuario_Edit(request.form)
        current_usuario_id = current_id_request('current_usuario_id')
        params['current_usuario_id'] = current_usuario_id
        usuario = user_by_id(current_usuario_id)
        settings_sql = settings_by_id(current_usuario_id)

        # XXX selector_usuario_edit_link
        if request.form['selector_button'] == 'selector_usuario_edit_link':
            params['usuario_edit_link'] = True
            return redirect(url_for('admin_usuario_ficha_html', params=dic_encode(params)))

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

            settings_sql.role = usuario_edit_form.role.data
            settings_sql.ban = settings_edit_ban
            settings_sql.email_validated = settings_email_validated
            settings_sql.email_robinson = settings_email_robinson
            if session_sql.dirty:
                flash_toast('Opciones actualizadas', 'success')
                session_sql.commit()

            if usuario_edit_form.validate():
                usuario_password_new = usuario_edit_form.password.data
                if usuario_password_new:
                    hashed_password = generate_password_hash(usuario_password_new, method='sha256')
                    usuario.password = hashed_password
                    session_sql.flush()

                # NOTE usuario_username_unicidad
                usuario_username_duplicado = session_sql.query(User).filter(User.username == usuario_edit_form.username.data).all()
                for usuario_duplicado in usuario_username_duplicado:
                    if usuario_duplicado.id != usuario.id:
                        flash_toast('Usuario ya registrado', 'warning')
                        return render_template(
                            'admin_usuario_ficha.html', usuario_edit=usuario_edit_form, params=params)
                else:
                    usuario.username = usuario_edit_form.username.data
                    session_sql.flush()

                # NOTE usuario_email_unicidad
                usuario_email_duplicado = session_sql.query(User).filter(User.email == usuario_edit_form.email.data).all()
                for usuario_duplicado in usuario_email_duplicado:
                    if usuario_duplicado.id != usuario.id:
                        flash_toast('Email ya registrado', 'warning')
                        return render_template(
                            'admin_usuario_ficha.html', usuario_edit=usuario_edit_form, params=params)
                else:
                    usuario.email = usuario_edit_form.email.data
                    session_sql.flush()

                if session_sql.dirty:
                    flash_toast('Usuario actualizado', 'success')
                    session_sql.commit()

                return redirect(url_for('admin_usuario_ficha_html', params=dic_encode(params)))
            else:
                flash_wtforms(usuario_edit_form, flash_toast, 'warning')
            return render_template(
                'admin_usuario_ficha.html', usuario_edit=usuario_edit_form, usuario=user_by_id(current_usuario_id), params=params)

    return render_template(
        'admin_usuario_ficha.html', usuario_edit=Usuario_Edit(), usuario=usuario, params=params)


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


# XXX alumnos
@app.route('/alumnos', methods=['GET', 'POST'])
@app.route('/alumnos/<params>', methods=['GET', 'POST'])
@login_required
def alumnos_html(params={}):
    try:
        params_old = dic_decode(params)
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
    params['collapse_tutorias'] = params_old.get('collapse_tutorias', False)
    params['collapse_tutoria_no_activas'] = params_old.get('collapse_tutoria_no_activas', False)
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
    current_tutoria_id = params['current_tutoria_id']
    params['tutoria_delete_confirmar'] = params_old.get('tutoria_delete_confirmar', False)
    params['tutorias_deleted_vaciar_papelera'] = params_old.get('tutorias_deleted_vaciar_papelera', False)
    params['tutoria_restaurar'] = params_old.get('tutoria_restaurar', False)
    params['alumno_delete_confirmar'] = params_old.get('alumno_delete_confirmar', False)
    params['current_alumno_id'] = params_old.get('current_alumno_id', 0)
    current_alumno_id = params['current_alumno_id']

    if not g.settings_current_user.grupo_activo_id or not grupos():
        params['collapse_grupo_add'] = True
        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

    if params['alumno_delete_confirmar']:
        params['alumno_delete_confirmar'] = False
        alumno_delete_sql = alumno_by_id(current_alumno_id)
        session_sql.delete(alumno_delete_sql)
        session_sql.commit()
        flash_toast(Markup('<strong>') + alumno_delete_sql.nombre + Markup('</strong>') + ' elminado', 'success')
        return redirect(url_for('alumnos_html', params=dic_encode(params)))

    if request.method == 'POST':
        current_alumno_id = current_id_request('current_alumno_id')
        params['current_alumno_id'] = current_alumno_id
        # XXX alumno_add
        if request.form['selector_button'] == 'selector_alumno_add':
            params['collapse_alumno_add'] = True
            alumno_add_form = Alumno_Add(request.form)
            if alumno_add_form.validate():
                alumno = session_sql.query(Alumno).filter(Alumno.grupo_id == g.settings_current_user.grupo_activo_id, unaccent(func.lower(Alumno.apellidos)) == unaccent(func.lower(alumno_add_form.apellidos.data)), unaccent(func.lower(Alumno.nombre)) == unaccent(func.lower(alumno_add_form.nombre.data))).first()
                if alumno:
                    alumno_add_form.nombre.errors = ['']
                    alumno_add_form.apellidos.errors = ['']
                    params['anchor'] = 'anchor_alu_add'
                    flash_toast(Markup('<strong>') + alumno_add_form.nombre.data.title() + Markup('</strong>') + ' ' + Markup('<strong>') + alumno_add_form.apellidos.data.title() + Markup('</strong>') + ' ya esta registrado', 'warning')
                    return render_template(
                        'alumnos.html', alumno_add=alumno_add_form, alumno_edit=Alumno_Add(), params=params)
                else:
                    params['collapse_alumno_add'] = False
                    alumno_add = Alumno(grupo_id=g.settings_current_user.grupo_activo_id, apellidos=alumno_add_form.apellidos.data.title(), nombre=alumno_add_form.nombre.data.title())
                    session_sql.add(alumno_add)
                    session_sql.commit()
                    flash_toast(Markup('<strong>') + alumno_add_form.nombre.data.title() + Markup('</strong>') + ' agregado', 'success')
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))
            else:
                params['anchor'] = 'anchor_alu_add'
                flash_wtforms(alumno_add_form, flash_toast, 'warning')
                return render_template(
                    'alumnos.html', alumno_add=alumno_add_form, alumno_edit=Alumno_Add(), params=params)

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
                        alumno_sql = session_sql.query(Alumno).filter(Alumno.grupo_id == g.settings_current_user.grupo_activo_id, unaccent(func.lower(Alumno.apellidos)) == unaccent(func.lower(alumno_apellidos)), unaccent(func.lower(Alumno.nombre)) == unaccent(func.lower(alumno_nombre))).first()
                        if alumno_sql:
                            alumno_repetido_contador = alumno_repetido_contador + 1
                        else:
                            alumno_add_contador = alumno_add_contador + 1
                            alumno_add = Alumno(grupo_id=g.settings_current_user.grupo_activo_id, apellidos=alumno_apellidos, nombre=alumno_nombre)
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
            if not asignaturas_alumno_by_alumno_id(current_alumno_id):
                params['collapse_alumno_edit_asignaturas'] = True
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

        # XXX selector_alumno_edit_link_close
        if request.form['selector_button'] == 'selector_alumno_edit_link_close':
            params['collapse_alumno'] = True
            params['collapse_alumno_edit'] = True
            params['anchor'] = 'anchor_ficha_' + str(hashids_encode(current_alumno_id))
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
            if not asignaturas_alumno_by_alumno_id(current_alumno_id):
                params['collapse_alumno_edit_asignaturas'] = True
                flash_toast('Debería asignar asignaturas a ' + Markup('<strong>') + alumno_edit_form.nombre.data + Markup('</strong>'), 'warning')
            else:
                if collapse_alumno_edit_asignaturas_contador != 0:
                    params['collapse_alumno_edit_asignaturas'] = True
                    session_sql.commit()
                    flash_toast('Asignadas asignaturas a ' + Markup('<strong>') + alumno_edit_form.nombre.data + Markup('</strong>'), 'success')
                    collapse_alumno_edit_asignaturas_contador = 0

            if alumno_edit_form.validate():
                alumno_edit = Alumno(grupo_id=g.settings_current_user.grupo_activo_id, nombre=alumno_edit_form.nombre.data.title(), apellidos=alumno_edit_form.apellidos.data.title())
                alumno_sql = session_sql.query(Alumno).filter_by(id=current_alumno_id).first()
                alumno_sql.nombre = alumno_edit.nombre.title()
                alumno_sql.apellidos = alumno_edit.apellidos.title()
                if session_sql.dirty:
                    flash_toast('Alumno actualizado', 'success')
                    session_sql.commit()
                return redirect(url_for('alumnos_html', params=dic_encode(params)))
            else:
                flash_wtforms(alumno_edit_form, flash_toast, 'warning')
            return render_template('alumnos.html',
                                   alumno_add=Alumno_Add(), alumno_edit=alumno_edit_form, grupo_add=Grupo_Add(), params=params)

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

    return render_template(
        'alumnos.html', alumno_add=Alumno_Add(), alumno_edit=Alumno_Add(),
        asignatura_add=Asignatura_Add(), params=params)

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

    params['current_categoria_id'] = params_old.get('current_categoria_id', 0)
    params['collapse_categoria_edit'] = params_old.get('collapse_categoria_edit', False)
    params['categoria_delete_link'] = params_old.get('categoria_delete_link', False)
    params['collapse_categoria_add'] = params_old.get('collapse_categoria_add', False)
    params['categoria_edit_link'] = params_old.get('categoria_edit_link', False)

    params['current_pregunta_id'] = params_old.get('current_pregunta_id', 0)
    params['collapse_pregunta_edit'] = params_old.get('collapse_pregunta_edit', False)
    params['pregunta_delete_link'] = params_old.get('pregunta_delete_link', False)
    params['collapse_pregunta_add'] = params_old.get('collapse_pregunta_add', False)
    params['pregunta_edit_link'] = params_old.get('pregunta_edit_link', False)

    if request.method == 'POST':
        current_categoria_id = current_id_request('current_categoria_id')
        params['current_categoria_id'] = current_categoria_id
        current_pregunta_id = current_id_request('current_pregunta_id')
        params['current_pregunta_id'] = current_pregunta_id

        # XXX categoria_add
        if request.form['selector_button'] == 'selector_categoria_add':
            params['collapse_categoria_add'] = True
            params['anchor'] = 'anchor_cat_add'
            categoria_add_form = Categoria_Add(request.form)
            if categoria_add_form.validate():
                categoria_add = Categoria(enunciado=categoria_add_form.enunciado.data, orden=categoria_add_form.orden.data, color=categoria_add_form.color.data)
                # NOTE checking unicidad de enunciado y orden
                categoria_enunciado_sql = session_sql.query(Categoria).filter(Categoria.enunciado == categoria_add_form.enunciado.data).first()
                categoria_orden_sql = session_sql.query(Categoria).filter(Categoria.orden == categoria_add_form.orden.data).first()
                if categoria_enunciado_sql or categoria_orden_sql:
                    if categoria_enunciado_sql:
                        categoria_add_form.enunciado.errors = ['']
                        flash_toast('Enunciado duplicado', 'warning')
                    if categoria_orden_sql:
                        categoria_add_form.orden.errors = ['']
                        flash_toast('Orden duplicado', 'warning')
                    return render_template('admin_cuestionario.html',
                                           categoria_add=categoria_add_form, categoria_edit=Categoria_Add(),
                                           pregunta_add=Pregunta_Add(), pregunta_edit=Pregunta_Add(),
                                           params=params)
                else:
                    session_sql.add(categoria_add)
                    session_sql.commit()
                    flash_toast('Categoria agregada', 'success')
                    return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))
            else:
                params['collapse_categoria_add'] = True
                flash_wtforms(categoria_add_form, flash_toast, 'warning')
            return render_template('admin_cuestionario.html',
                                   categoria_add=categoria_add_form, categoria_edit=Categoria_Add(),
                                   pregunta_add=Pregunta_Add(), pregunta_edit=Pregunta_Add(), params=params)

        # XXX selector_categoria_add_close
        if request.form['selector_button'] == 'selector_categoria_add_close':
            return redirect(url_for('admin_cuestionario_html'))

        # XXX selector_categoria_edit_link
        if request.form['selector_button'] == 'selector_categoria_edit_link':
            params['categoria_edit_link'] = True
            params['collapse_categoria_edit'] = True
            params['anchor'] = 'anchor_cat_' + str(hashids_encode(current_categoria_id))
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX categoria_edit
        if request.form['selector_button'] in ['selector_categoria_edit', 'selector_move_down_categoria', 'selector_move_up_categoria']:
            params['current_categoria_id'] = current_categoria_id
            params['collapse_categoria_edit'] = True
            params['categoria_edit_link'] = True
            params['anchor'] = 'anchor_cat_' + str(hashids_encode(current_categoria_id))
            move_up = False
            move_down = False
            categoria_edit_form = Categoria_Add(request.form)
            if categoria_edit_form.validate():
                categoria_edit = Categoria(enunciado=categoria_edit_form.enunciado.data,
                                           orden=categoria_edit_form.orden.data, color=categoria_edit_form.color.data)
                categoria = session_sql.query(Categoria).filter(Categoria.id == current_categoria_id).first()
                if categoria.enunciado.lower() != categoria_edit.enunciado.lower() or categoria.orden != categoria_edit.orden or categoria.color != categoria_edit.color:
                    if categoria.enunciado.lower() != categoria_edit.enunciado.lower():
                        categoria.enunciado = categoria_edit.enunciado
                    if categoria.orden != categoria_edit.orden:
                        categoria.orden = categoria_edit.orden
                    if categoria.color != categoria_edit.color:
                        categoria.color = categoria_edit.color
                    flash_toast('Categoria actualizada', 'success')
                if request.form['selector_button'] == 'selector_move_down_categoria':
                    for k in range(1, 500):
                        categoria_down = session_sql.query(Categoria).filter(Categoria.orden == (categoria.orden + k)).first()
                        if categoria_down:
                            move_down = int(str(categoria.orden + k))
                            categoria.orden = categoria.orden + k
                            categoria_down.orden = categoria.orden - k
                            flash_toast('Categoria bajada', 'success')
                            break

                if request.form['selector_button'] == 'selector_move_up_categoria':
                    for k in range(1, 500):
                        categoria_down = session_sql.query(Categoria).filter(Categoria.orden == (categoria.orden - k)).first()
                        if categoria_down:
                            move_up = int(str(categoria.orden - k))
                            categoria.orden = categoria.orden - k
                            categoria_down.orden = categoria.orden + k
                            flash_toast('Categoria subida', 'success')
                            break

                session_sql.commit()
                return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))
            else:
                flash_wtforms(categoria_edit_form, flash_toast, 'warning')
            return render_template('admin_cuestionario.html',
                                   pregunta_add=Pregunta_Add(), pregunta_edit=Pregunta_Add(),
                                   categoria_add=Categoria_Add(), categoria_edit=categoria_edit_form,
                                   move_down=move_down, move_up=move_up, params=params)

        # XXX selector_categoria_edit_close
        if request.form['selector_button'] == 'selector_categoria_edit_close':
            return redirect(url_for('admin_cuestionario_html'))

        # XXX selector_categoria_edit_rollback
        if request.form['selector_button'] == 'selector_categoria_edit_rollback':
            current_categoria_id = current_id_request('current_categoria_id')
            params['current_categoria_id'] = current_categoria_id
            params['collapse_categoria_edit'] = True
            params['anchor'] = 'anchor_cat_' + str(hashids_encode(current_categoria_id))
            session_sql.rollback()
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX selector_categoria_delete_link
        if request.form['selector_button'] == 'selector_categoria_delete_link':
            current_categoria_id = current_id_request('current_categoria_id')
            params['current_categoria_id'] = current_categoria_id
            params['collapse_categoria_edit'] = True
            params['anchor'] = 'anchor_cat_' + str(hashids_encode(current_categoria_id))
            params['categoria_edit_link'] = True
            params['categoria_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX categoria_delete
        if request.form['selector_button'] == 'selector_categoria_delete':
            categoria_delete_form = Categoria_Add(request.form)
            current_categoria_id = current_id_request('current_categoria_id')
            categoria_delete = categoria_by_id(current_categoria_id)
            session_sql.delete(categoria_delete)
            session_sql.commit()
            flash_toast('Categoria elminada', 'success')
            return redirect(url_for('admin_cuestionario_html'))

        # XXX categoria_delete_close
        if request.form['selector_button'] == 'selector_categoria_delete_close':
            current_categoria_id = current_id_request('current_categoria_id')
            params['current_categoria_id'] = current_categoria_id
            params['collapse_categoria_edit'] = True
            params['anchor'] = 'anchor_cat_' + str(hashids_encode(current_categoria_id))
            return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))

        # XXX pregunta_add
        if request.form['selector_button'] == 'selector_pregunta_add':
            params['collapse_pregunta_add'] = True
            params['anchor'] = 'anchor_pre_add'
            pregunta_add_form = Pregunta_Add(request.form)
            if pregunta_add_form.validate():
                pregunta_add = Pregunta(enunciado=pregunta_add_form.enunciado.data, enunciado_ticker=pregunta_add_form.enunciado_ticker.data,
                                        categoria_id=pregunta_add_form.categoria_id.data, orden=pregunta_add_form.orden.data,
                                        visible=pregunta_add_form.visible.data, active_default=pregunta_add_form.active_default.data)
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
                        'admin_cuestionario.html',
                        pregunta_add=pregunta_add_form, pregunta_edit=Pregunta_Add(),
                        categoria_add=Categoria_Add(), categoria_edit=Categoria_Add(), params=params)
                else:
                    session_sql.add(pregunta_add)
                    session_sql.commit()
                    flash_toast('Pregunta agregada', 'success')
                    return redirect(url_for('admin_cuestionario_html', params=dic_encode(params)))
            else:
                params['collapse_pregunta_add'] = True
                flash_wtforms(pregunta_add_form, flash_toast, 'warning')
            return render_template(
                'admin_cuestionario.html',
                pregunta_add=pregunta_add_form, pregunta_edit=Pregunta_Add(),
                categoria_add=Categoria_Add(), categoria_edit=Categoria_Add(), params=params)

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
        if request.form['selector_button'] in ['selector_pregunta_edit', 'selector_move_down_pregunta', 'selector_move_up_pregunta']:
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
                                         categoria_id=pregunta_edit_form.categoria_id.data, orden=pregunta_edit_form.orden.data, visible=visible, active_default=active_default)
                pregunta = session_sql.query(Pregunta).filter(Pregunta.id == current_pregunta_id).first()
                if pregunta.enunciado.lower() != pregunta_edit.enunciado.lower() or pregunta.enunciado_ticker.lower() != pregunta_edit.enunciado_ticker.lower() or pregunta.categoria_id != pregunta_edit.categoria_id or pregunta.orden != pregunta_edit.orden or str(pregunta.visible) != str(visible) or str(pregunta.active_default) != str(active_default):
                    if pregunta.enunciado.lower() != pregunta_edit.enunciado.lower():
                        pregunta.enunciado = pregunta_edit.enunciado
                    if pregunta.enunciado_ticker.lower() != pregunta_edit.enunciado_ticker.lower():
                        pregunta.enunciado_ticker = pregunta_edit.enunciado_ticker
                    if pregunta.categoria_id != pregunta_edit.categoria_id:
                        pregunta.categoria_id = pregunta_edit.categoria_id
                    if pregunta.orden != pregunta_edit.orden:
                        pregunta.orden = pregunta_edit.orden
                    if pregunta.visible != visible:
                        pregunta.visible = visible
                    if pregunta.active_default != active_default:
                        pregunta.active_default = active_default
                    flash_toast('Pregunta actualizada', 'success')

                if request.form['selector_button'] == 'selector_move_down_pregunta':
                    for k in range(1, 500):
                        pregunta_down = session_sql.query(Pregunta).filter(Pregunta.orden == (pregunta.orden + k)).first()
                        if pregunta_down:
                            move_down = int(str(pregunta.orden + k))
                            pregunta.orden = pregunta.orden + k
                            pregunta_down.orden = pregunta.orden - k
                            flash_toast('Pregunta bajada', 'success')
                            break

                if request.form['selector_button'] == 'selector_move_up_pregunta':
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
                'admin_cuestionario.html',
                pregunta_add=Pregunta_Add(), pregunta_edit=pregunta_edit_form,
                categoria_add=Categoria_Add(), categoria_edit=Categoria_Add(),
                move_down=move_down, move_up=move_up, visible=visible,
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
            pregunta_delete = pregunta_by_id(current_pregunta_id)
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
        'admin_cuestionario.html',
        pregunta_add=Pregunta_Add(), categoria_add=Categoria_Add(),
        pregunta_edit=Pregunta_Add(), categoria_edit=Categoria_Add(),
        params=params)


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
            for pregunta in preguntas():
                if pregunta.id in preguntas_id_lista:
                    association_settings_pregunta_sql = session_sql.query(Association_Settings_Pregunta).filter_by(pregunta_id=pregunta.id, settings_id=g.settings_current_user.id).first()
                    if not association_settings_pregunta_sql:
                        association_settings_pregunta_add = Association_Settings_Pregunta(pregunta_id=pregunta.id, settings_id=g.settings_current_user.id)
                        session_sql.add(association_settings_pregunta_add)
                        contador += 1
                else:
                    association_settings_pregunta_sql = session_sql.query(Association_Settings_Pregunta).filter_by(pregunta_id=pregunta.id, settings_id=g.settings_current_user.id).first()
                    if association_settings_pregunta_sql:
                        session_sql.delete(association_settings_pregunta_sql)
                        contador += 1
            session_sql.commit()
            if not g.settings_current_user.preguntas:
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

@app.route('/analisis_paper', methods=['GET', 'POST'])
@app.route('/analisis_paper/<params>', methods=['GET', 'POST'])
@login_required
def analisis_paper_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}

    params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
    current_tutoria_id = params['current_tutoria_id']

    grupo = grupo_by_tutoria_id(current_tutoria_id)
    tutoria = tutoria_by_id(current_tutoria_id)
    alumno = alumno_by_tutoria_id(current_tutoria_id)

    if not tutoria or not alumno:
        return redirect(url_for('analisis_tutoria_no_disponible_html'))

    stats = analisis_tutoria(current_tutoria_id)
    stats['analisis_paper'] = True
    grupo_stats = respuestas_grupo_stats(current_tutoria_id, stats['preguntas_con_respuesta_lista'], stats['asignaturas_recibidas_lista'])
    respuestas_tutoria_media_stats = respuestas_tutoria_media(current_tutoria_id)
    evolucion_stats = evolucion_tutorias(alumno.id)
    comentarios_stats = tutoria_comentarios(current_tutoria_id, stats['asignaturas_recibidas_lista'])

    return render_template('analisis_paper.html',
                           params=params, tutoria=tutoria, alumno=alumno, grupo=grupo,
                           stats=stats, grupo_stats=grupo_stats,
                           respuestas_tutoria_media_stats=respuestas_tutoria_media_stats, evolucion_stats=evolucion_stats, comentarios_stats=comentarios_stats)


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
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
    current_tutoria_id = params['current_tutoria_id']
    params['show_analisis_cuestionario_detallado'] = params_old.get('show_analisis_cuestionario_detallado', False)
    params['show_analisis_comparativo_detallado'] = params_old.get('show_analisis_comparativo_detallado', False)
    params['show_analisis_asignaturas_detallado'] = params_old.get('show_analisis_asignaturas_detallado', False)
    params['tutoria_delete_confirmar'] = params_old.get('tutoria_delete_confirmar', False)
    params['comentario_edit'] = params_old.get('comentario_edit', False)
    params['current_informe_id'] = params_old.get('current_informe_id', 0)
    grupo = grupo_by_tutoria_id(current_tutoria_id)
    tutoria = tutoria_by_id(current_tutoria_id)
    alumno = alumno_by_tutoria_id(current_tutoria_id)

    if not tutoria or not alumno:
        return redirect(url_for('analisis_tutoria_no_disponible_html'))

    if params['tutoria_delete_confirmar']:
        params['tutoria_delete_confirmar'] = False
        tutoria = tutoria_by_id(current_tutoria_id)
        alumno_sql = alumno_by_id(tutoria.alumno_id)
        tutoria_calendar_delete(event_id=tutoria.calendar_event_id)
        tutoria.deleted = True
        tutoria.deleted_at = g.current_date
        session_sql.commit()
        flash_toast('Tutoria enviada a la papelera', 'success')
        return redirect(url_for('tutorias_html'))

    stats = analisis_tutoria(current_tutoria_id)
    comentarios_stats = tutoria_comentarios(current_tutoria_id, stats['asignaturas_recibidas_lista'])
    grupo_stats = respuestas_grupo_stats(current_tutoria_id, stats['preguntas_con_respuesta_lista'], stats['asignaturas_recibidas_lista'])
    if g.settings_current_user.show_analisis_asignaturas_detallado:
        respuestas_tutoria_media_stats = respuestas_tutoria_media(current_tutoria_id)
    else:
        respuestas_tutoria_media_stats = False
    evolucion_stats = evolucion_tutorias(alumno.id)

    return render_template('analisis.html',
                           params=params, tutoria=tutoria, alumno=alumno, grupo=grupo,
                           stats=stats, grupo_stats=grupo_stats,
                           respuestas_tutoria_media_stats=respuestas_tutoria_media_stats, evolucion_stats=evolucion_stats, comentarios_stats=comentarios_stats)


# XXX analisis_tutoria_edit
@app.route('/analisis_tutoria_edit', methods=['GET', 'POST'])
@app.route('/analisis_tutoria_edit/<params>', methods=['GET', 'POST'])
@login_required
def analisis_tutoria_edit_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params['informe_comentario_edit'] = params_old.get('informe_comentario_edit', False)

    # XXX informe_comentario_edit
    if params['informe_comentario_edit']:
        params['current_informe_id'] = params_old.get('current_informe_id', 0)
        params['current_tutoria_id'] = params_old.get('current_tutoria_id', 0)
        current_informe_id = params['current_informe_id']
        current_tutoria_id = params['current_tutoria_id']
        informe = informe_by_id(current_informe_id)
        # NOTE no evalua porque necesita request POST
        informe.comentario_editado = request.form.get('comentario_editado_' + str(hashids_encode(int(current_informe_id))))
        if session_sql.dirty:
            session_sql.commit()
        params['comentario_edit'] = True
        params['anchor'] = 'anchor_comentario_edit_' + str(hashids_encode(current_informe_id))
        return redirect(url_for('analisis_html', params=dic_encode(params)))

    if request.method == 'POST':
        current_tutoria_id = current_id_request('current_tutoria_id')
        params['current_tutoria_id'] = current_tutoria_id
        tutoria_sql = tutoria_by_id(current_tutoria_id)

        # XXX comentario_edit
        if 'selector_comentario_edit' in request.form['selector_button']:
            # NOTE NO BORRAR muy util para capturar valores de un formulario multiple
            # ************************************************************************
            # comentario_editado_dic={}
            # f = request.form
            # for key in f.keys():
            #     for value in f.getlist(key):
            #         if not key.find('comentario_editado_')==-1:
            #             print(key, ":", value)
            #             comentario_editado_dic[key]=value
            # print('comentario_editado_dic:',comentario_editado_dic)
            # ---------------------------------------------------------------------------

            current_informe_id = hashids_decode(request.form['selector_button'].replace('selector_comentario_edit_', ''))
            informe = informe_by_id(current_informe_id)
            informe.comentario_editado = request.form.get('comentario_edit_' + str(hashids_encode(current_informe_id)))
            if session_sql.dirty:
                session_sql.commit()
            params['comentario_edit'] = True
            params['anchor'] = 'anchor_comentario_edit_' + str(hashids_encode(current_informe_id))
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX comentario_restaurar
        if 'selector_comentario_restaurar' in request.form['selector_button']:
            current_informe_id = hashids_decode(request.form['selector_button'].replace('selector_comentario_restaurar_', ''))
            informe = informe_by_id(current_informe_id)
            informe.comentario_editado = ''
            if session_sql.dirty:
                session_sql.commit()
            params['comentario_edit'] = True
            params['anchor'] = 'anchor_comentario_edit_' + str(hashids_encode(current_informe_id))
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX selector_tutoria_restaurar
        if request.form['selector_button'] == 'selector_tutoria_restaurar':
            tutoria_sql.deleted = False
            session_sql.commit()
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX settings_show_analisis_comparativo_detallado
        if request.form['selector_button'] == 'settings_show_analisis_comparativo_detallado':
            settings_show_analisis_comparativo_detallado = str(request.form.get('settings_show_analisis_comparativo_detallado'))
            if settings_show_analisis_comparativo_detallado == 'True':
                settings_show_analisis_comparativo_detallado = False
            else:
                settings_show_analisis_comparativo_detallado = True
            g.settings_current_user.show_analisis_comparativo_detallado = settings_show_analisis_comparativo_detallado
            session_sql.commit()
            params['anchor'] = 'anchor_comp'
            params['show_analisis_comparativo_detallado'] = True
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX settings_show_analisis_cuestionario_detallado
        if request.form['selector_button'] == 'settings_show_analisis_cuestionario_detallado':
            settings_show_analisis_cuestionario_detallado = str(request.form.get('settings_show_analisis_cuestionario_detallado'))
            if settings_show_analisis_cuestionario_detallado == 'True':
                settings_show_analisis_cuestionario_detallado = False
            else:
                settings_show_analisis_cuestionario_detallado = True
            g.settings_current_user.show_analisis_cuestionario_detallado = settings_show_analisis_cuestionario_detallado
            session_sql.commit()
            params['anchor'] = 'anchor_cues'
            params['show_analisis_cuestionario_detallado'] = True
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX settings_show_analisis_asignaturas_detallado
        if request.form['selector_button'] == 'settings_show_analisis_asignaturas_detallado':
            settings_show_analisis_asignaturas_detallado = str(request.form.get('settings_show_analisis_asignaturas_detallado'))
            if settings_show_analisis_asignaturas_detallado == 'True':
                settings_show_analisis_asignaturas_detallado = False
            else:
                settings_show_analisis_asignaturas_detallado = True
            g.settings_current_user.show_analisis_asignaturas_detallado = settings_show_analisis_asignaturas_detallado
            session_sql.commit()
            params['anchor'] = 'anchor_deta'
            params['show_analisis_asignaturas_detallado'] = True
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX settings_informe_comentario_edit_mode
        if request.form['selector_button'] == 'settings_informe_comentario_edit_mode':
            settings_informe_comentario_edit_mode = str(request.form.get('settings_informe_comentario_edit_mode'))
            if settings_informe_comentario_edit_mode == 'True':
                settings_informe_comentario_edit_mode = False
            else:
                settings_informe_comentario_edit_mode = True
            g.settings_current_user.informe_comentario_edit_mode = settings_informe_comentario_edit_mode
            session_sql.commit()
            params['anchor'] = 'anchor_deta'
            params['informe_comentario_edit_mode'] = True
            params['comentario_edit'] = True
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_acuerdo_save
        if request.form['selector_button'] == 'selector_acuerdo_save':
            acuerdo = request.form.get('acuerdo')
            tutoria_sql = tutoria_by_id(current_tutoria_id)
            tutoria_sql.acuerdo = acuerdo
            session_sql.commit()
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_edit_close
        if request.form['selector_button'] == 'selector_tutoria_edit_close':
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
                flash_toast('Tutoria activada', 'success')
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX selector_tutoria_delete_archivar
        if request.form['selector_button'] == 'selector_tutoria_delete_archivar':
            tutoria_to_move = tutoria_by_id(current_tutoria_id)
            tutoria_to_move.activa = False
            session_sql.commit()
            flash_toast('Tutoria archivada', 'success')
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_edit
        if request.form['selector_button'] == 'selector_tutoria_edit':
            params['tutoria_edit_link'] = True
            tutoria_sql = session_sql.query(Tutoria).filter(Tutoria.id == current_tutoria_id).first()
            tutoria_edit_form = Tutoria_Add(current_tutoria_id=current_tutoria_id, fecha=request.form.get('fecha'), hora=request.form.get('hora'))
            if tutoria_edit_form.validate():
                tutoria_edit_form_fecha = datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%d-%m-%Y').strftime('%Y-%m-%d')
                if datetime.datetime.strptime(tutoria_edit_form_fecha, '%Y-%m-%d').date() < g.current_date:
                    tutoria_edit_form.fecha.errors = ['Tutoría no actualizada.']
                    flash_wtforms(tutoria_edit_form, flash_toast, 'warning')
                    flash_toast('Debe indicar una fecha posterior', 'warning')
                    return redirect(url_for('analisis_html', params=dic_encode(params)))
                else:
                    if g.settings_current_user.calendar:
                        try:
                            credentials = oauth2client.client.Credentials.new_from_json(g.settings_current_user.oauth2_credentials)
                            http = httplib2.Http()
                            http = credentials.authorize(http)
                            service = discovery.build('calendar', 'v3', http=http)
                        except:
                            return redirect(url_for('oauth2callback_calendar'))

                    # Actualiza google calendar
                    tutoria_edit_form_hora = datetime.datetime.strptime(tutoria_edit_form.hora.data, '%H:%M')
                    calendar_datetime_utc_start = (datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%d-%m-%Y') + datetime.timedelta(hours=(tutoria_edit_form_hora.hour)) + datetime.timedelta(minutes=tutoria_edit_form_hora.minute)).timestamp()
                    calendar_datetime_utc_start_arrow = str(arrow.get(calendar_datetime_utc_start).replace(tzinfo='Europe/Madrid'))

                    calendar_datetime_utc_end = (datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%d-%m-%Y') + datetime.timedelta(hours=(tutoria_edit_form_hora.hour)) + datetime.timedelta(minutes=(tutoria_edit_form_hora.minute + g.settings_current_user.tutoria_duracion))).timestamp()
                    calendar_datetime_utc_end_arrow = str(arrow.get(calendar_datetime_utc_end).replace(tzinfo='Europe/Madrid'))

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
            settings_show_analisis_avanzado = request.form.get('settings_show_analisis_avanzado')

            if not settings_edit_tutoria_timeout:
                settings_edit_tutoria_timeout = False
            if not settings_show_asignaturas_analisis:
                settings_show_asignaturas_analisis = False
            if not settings_edit_calendar:
                settings_edit_calendar = False
                g.settings_current_user.calendar_sincronizado = False
                g.settings_current_user.oauth2_credentials = ''
            if not settings_show_analisis_avanzado:
                settings_show_analisis_avanzado = False

            g.settings_current_user.tutoria_timeout = settings_edit_tutoria_timeout
            g.settings_current_user.show_asignaturas_analisis = settings_show_asignaturas_analisis
            g.settings_current_user.tutoria_duracion = settings_tutoria_duracion
            g.settings_current_user.diferencial = settings_diferencial
            g.settings_current_user.calendar = settings_edit_calendar
            g.settings_current_user.show_analisis_avanzado = settings_show_analisis_avanzado
            session_sql.commit()
            flash_toast('Configuracion actualizada', 'success')

            if g.settings_current_user.calendar:
                try:
                    credentials = oauth2client.client.Credentials.new_from_json(g.settings_current_user.oauth2_credentials)
                    g.settings_current_user.oauth2_credentials = credentials.to_json()
                    session_sql.commit()
                    http = credentials.authorize(httplib2.Http())
                    service = discovery.build('calendar', 'v3', http=http)
                except:
                    return redirect(url_for('oauth2callback_calendar'))
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
                grupo_add = Grupo(settings_id=g.settings_current_user.id, nombre=grupo_add_form.nombre.data, tutor_nombre=grupo_add_form.tutor_nombre.data.title(), tutor_apellidos=grupo_add_form.tutor_apellidos.data.title(),
                                  centro=grupo_add_form.centro.data, curso_academico=grupo_add_form.curso_academico.data)
                # NOTE checking unicidad de nombre, centro, fecha y usuario
                unicidad_de_grupo_sql = session_sql.query(Settings).filter(Settings.id == g.settings_current_user.id).join(Grupo).filter(Grupo.nombre == grupo_add_form.nombre.data, Grupo.curso_academico == grupo_add_form.curso_academico.data, Grupo.centro == grupo_add_form.centro.data).first()
                if unicidad_de_grupo_sql:
                    grupo_add_form.nombre.errors = ['']
                    flash_toast(Markup('<strong>') + grupo_add.nombre + Markup('</strong> ya existe en ') + str(grupo_add.curso_academico) + Markup(' | ') + str(int(grupo_add.curso_academico) + 1) + Markup('<br> Cambie el nombre'), 'warning')
                    return render_template(
                        'settings_grupos.html', grupo_add=grupo_add_form, grupo_edit=Grupo_Add(), grupos=grupos(), params=params)
                else:
                    # NOTE set grupo_activo
                    session_sql.add(grupo_add)
                    session_sql.flush()
                    if grupo_add_grupo_activo:
                        g.settings_current_user.grupo_activo_id = grupo_add.id
                        flash_toast(Markup('Grupo <strong>') + grupo_add_form.nombre.data + Markup('</strong>') + ' agregado' + Markup('<br>Ahora este tu grupo activo'), 'success')
                    else:
                        if g.settings_current_user.grupo_activo_id:
                            flash_toast(Markup('Grupo <strong>') + grupo_add_form.nombre.data + Markup('</strong>') + ' agregado' + Markup('<br>Si deseas usar este grupo debes activarlo'), 'success')
                        else:
                            g.settings_current_user.grupo_activo_id = grupo_add.id

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
                grupo_edit = Grupo(nombre=grupo_edit_form.nombre.data, tutor_nombre=grupo_edit_form.tutor_nombre.data.title(), tutor_apellidos=grupo_edit_form.tutor_apellidos.data.title(), centro=grupo_edit_form.centro.data)
                grupo_sql = session_sql.query(Grupo).filter(Grupo.id == current_grupo_id).first()
                if grupo_sql.nombre.lower() != grupo_edit.nombre.lower() or grupo_sql.tutor_nombre.lower() != grupo_edit.tutor_nombre.lower() or grupo_sql.tutor_apellidos.lower() != grupo_edit.tutor_apellidos.lower() or grupo_sql.centro.lower() != grupo_edit.centro.lower() or str(g.settings_current_user.grupo_activo_id) != str(grupo_edit_grupo_activo_switch):
                    if grupo_sql.nombre.lower() != grupo_edit.nombre.lower():
                        grupo_sql.nombre = grupo_edit.nombre
                    if grupo_sql.tutor_nombre.lower() != grupo_edit.tutor_nombre.lower():
                        grupo_sql.tutor_nombre = grupo_edit.tutor_nombre
                    if grupo_sql.tutor_apellidos.lower() != grupo_edit.tutor_apellidos.lower():
                        grupo_sql.tutor_apellidos = grupo_edit.tutor_apellidos
                    if grupo_sql.centro.lower() != grupo_edit.centro.lower():
                        grupo_sql.centro = grupo_edit.centro
                    if grupo_edit_grupo_activo_switch:
                        g.settings_current_user.grupo_activo_id = current_grupo_id
                    else:
                        g.settings_current_user.grupo_activo_id = None
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


@app.route('/informe/<asignatura_id>/<tutoria_id>/', methods=['GET', 'POST'])
@app.route('/informe/<asignatura_id>/<tutoria_id>/<params>', methods=['GET', 'POST'])
def informe_html(asignatura_id, tutoria_id, params={}):
    try:
        tutoria_id = hashids_decode(tutoria_id)
        asignatura_id = hashids_decode(asignatura_id)
        tutoria_asignatura_check = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria_id, Association_Tutoria_Asignatura.asignatura_id == asignatura_id).first()
        if not tutoria_asignatura_check:
            return redirect(url_for('informe_no_disponible_html'))
    except:
        return redirect(url_for('informe_no_disponible_html'))
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['pregunta_sin_respuesta'] = params_old.get('pregunta_sin_respuesta', False)
    params['selector_guardar_cuestionario'] = params_old.get('selector_guardar_cuestionario', False)
    print('selector_guardar_cuestionario:', params['selector_guardar_cuestionario'])

    tutoria = tutoria_by_id(tutoria_id)
    asignatura = asignatura_by_id(asignatura_id)
    grupo = grupo_by_tutoria_id(tutoria_id)
    alumno = alumno_by_id(tutoria.alumno_id)
    settings = settings_by_tutoria_id(tutoria_id)
    informe_sql = invitado_informe(tutoria_id, asignatura_id)
    preguntas_orden_desc = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings.id).join(Categoria).order_by(desc(Categoria.orden), desc(Pregunta.orden)).all()
    for pregunta in preguntas_orden_desc:
        params['pregunta_' + str(pregunta.id)] = params_old.get('pregunta_' + str(pregunta.id), -2)
    params['comentario'] = params_old.get('comentario', '')

    params['cuestionario_tab'] = params_old.get('cuestionario_tab', True)
    params['notas_tab'] = params_old.get('notas_tab', False)
    params['observaciones_tab'] = params_old.get('observaciones_tab', False)

    params['current_prueba_evaluable_id'] = params_old.get('current_prueba_evaluable_id', 0)
    current_prueba_evaluable_id = params['current_prueba_evaluable_id']
    prueba_evaluable_dic = {}

    if request.method == 'POST':
        params['cuestionario_tab'] = False  # es mas comodo ponerlo aqui que estar repitiendolo
        # NOTE captura de datos antes de crear el informe
        # ****************************************************************
        for pregunta in preguntas_orden_desc:
            params['pregunta_' + str(pregunta.id)] = request.form.get('pregunta_' + str(hashids_encode(pregunta.id)))
            if params['pregunta_' + str(pregunta.id)]:
                if int(params['pregunta_' + str(pregunta.id)]) == -2:
                    params['anchor'] = 'anchor_pregunta_' + str(hashids_encode(pregunta.id))
                    params['pregunta_sin_respuesta'] = True
            else:
                params['pregunta_sin_respuesta'] = True

        params['comentario'] = request.form.get('comentario')
        # ------------------------------------------------------------
        # NOTE FIN captura de datos antes de crear el informe

        # NOTE captura de notas una vez creado el informe
        # ****************************************************************
        if informe_sql:
            for pregunta in preguntas_orden_desc:
                invitado_respuesta(informe_sql.id, pregunta.id).resultado = params['pregunta_' + str(pregunta.id)]

            informe_sql.comentario = params['comentario']

            for prueba_evaluable in invitado_pruebas_evaluables(informe_sql.id):
                prueba_evaluable.nombre = request.form.get('prueba_evaluable_nombre_' + str(hashids_encode(prueba_evaluable.id)))
                prueba_evaluable.nota = request.form.get('prueba_evaluable_nota_' + str(hashids_encode(prueba_evaluable.id)))
                prueba_evaluable_dic['selector_prueba_evaluable_delete_' + str(prueba_evaluable.id)] = int(prueba_evaluable.id)

        # ------------------------------------------------------------
        # NOTE FIN captura de notas una vez creado el informe

        if request.form['selector_button'] in prueba_evaluable_dic.keys():
            prueba_evaluable_delete_id = prueba_evaluable_dic[request.form['selector_button']]
            prueba_evaluable_delete_sql = session_sql.query(Prueba_Evaluable).filter(Prueba_Evaluable.id == prueba_evaluable_delete_id).first()
            session_sql.delete(prueba_evaluable_delete_sql)
            params['notas_tab'] = True
            return redirect(url_for('informe_html', tutoria_id=hashids_encode(tutoria_id), asignatura_id=hashids_encode(asignatura_id), params=dic_encode(params)))

        # NOTE primero hay que agregar el informe para poder continuar agregando elementos usando informe.id
        if request.form['selector_button'] == 'selector_guardar_cuestionario' or params['selector_guardar_cuestionario']:
            if params['pregunta_sin_respuesta']:
                flash_toast('Preguntas sin evaluar', 'warning')
                params['cuestionario_tab'] = True
                return redirect(url_for(
                    'informe_html',
                    asignatura_id=hashids_encode(asignatura_id), tutoria_id=hashids_encode(tutoria_id),
                    params=dic_encode(params)))
            else:
                informe_add = Informe(tutoria_id=tutoria_id, asignatura_id=asignatura_id, comentario=params['comentario'])
                session_sql.add(informe_add)
                session_sql.flush()  # NOTE necesario para obtener informe_add.id antes del commit
                for pregunta in preguntas_orden_desc:
                    respuesta = Respuesta(informe_id=informe_add.id, pregunta_id=pregunta.id, resultado=params['pregunta_' + str(pregunta.id)])
                    session_sql.add(respuesta)
                    # session_sql.flush()
                    params['notas_tab'] = True
            return redirect(url_for(
                'informe_html',
                asignatura_id=hashids_encode(asignatura_id), tutoria_id=hashids_encode(tutoria_id),
                params=dic_encode(params)))
        if request.form['selector_button'] == 'selector_prueba_evaluable_add':
            params['collapse_prueba_evaluable_add'] = True
            prueba_evaluable_nombre = ''
            prueba_evaluable_nota = 0
            prueba_evaluable_add = Prueba_Evaluable(informe_id=informe_sql.id, nombre=prueba_evaluable_nombre, nota=prueba_evaluable_nota)
            session_sql.add(prueba_evaluable_add)
            session_sql.flush()  # necesario para disponer luego de prueba_evaluable_add.id
            params['anchor'] = 'anchor_pru_eva_' + str(hashids_encode(prueba_evaluable_add.id))
            # flash_toast('Prueba evaluable agregada', 'success')
            params['notas_tab'] = True
            return redirect(url_for('informe_html', tutoria_id=hashids_encode(tutoria_id), asignatura_id=hashids_encode(asignatura_id), params=dic_encode(params)))

        if request.form['selector_button'] == 'selector_enviar_informe':
            session_sql.commit()
            flash_toast('Infome de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' enviado', 'success')
            return redirect(url_for(
                'informe_success_html',
                asignatura_id=hashids_encode(asignatura_id), tutoria_id=hashids_encode(tutoria_id),
                params=dic_encode(params)))

    return render_template(
        'informe.html', tutoria=tutoria, asignatura=asignatura,
        alumno=alumno, grupo=grupo, informe=informe_sql, params=params)


# XXX informe_success


@app.route('/informe_success/<asignatura_id>/<tutoria_id>/', methods=['GET', 'POST'])
@app.route('/informe_success/<asignatura_id>/<tutoria_id>/<params>', methods=['GET', 'POST'])
def informe_success_html(asignatura_id, tutoria_id, params={}):
    try:
        tutoria_id = hashids_decode(tutoria_id)
        asignatura_id = hashids_decode(asignatura_id)
        tutoria_asignatura_check = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria_id, Association_Tutoria_Asignatura.asignatura_id == asignatura_id).first()
        if not tutoria_asignatura_check:
            return redirect(url_for('informe_no_disponible_html'))
    except:
        return redirect(url_for('informe_no_disponible_html'))

    params = {}
    asignatura = asignatura_by_id(asignatura_id)
    tutoria = tutoria_by_id(tutoria_id)
    alumno = alumno_by_tutoria_id(tutoria_id)
    grupo = grupo_by_tutoria_id(tutoria_id)
    params['participacion_porcentaje_recent'] = cociente_porcentual(asignatura_informes_respondidos_recent_count(asignatura.id), asignatura_informes_solicitados_recent_count(asignatura.id))
    params['tutorias_sin_respuesta_by_asignatura_id'] = tutorias_sin_respuesta_by_asignatura_id(asignatura.id)
    params['settings_global_periodo_participacion_recent'] = g.settings_global.periodo_participacion_recent
    return render_template(
        'informe_success.html',
        asignatura=asignatura, tutoria=tutoria, alumno=alumno, grupo=grupo, params=params)


@app.route('/informes_pendientes/<asignatura_id>', methods=['GET', 'POST'])
def informes_pendientes_html(asignatura_id):
    try:
        asignatura_id = hashids_decode(asignatura_id)
    except:
        return redirect(url_for('informe_no_disponible_html'))

    params = {}
    asignatura = asignatura_by_id(asignatura_id)
    grupo = grupo_by_asignatura_id(asignatura_id)
    tutorias_id_lista = tutorias_sin_respuesta_by_asignatura_id(asignatura.id)['tutorias_id_lista']
    tutorias_pendites = []
    for tutoria_id in tutorias_id_lista:
        tutorias_pendites.append(tutoria_by_id(tutoria_id))
    params['tutorias_pendites'] = tutorias_pendites
    return render_template('informes_pendientes.html', asignatura=asignatura, grupo=grupo, params=params)


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
    params['asignatura_edit_link'] = params_old.get('asignatura_edit_link', False)

    params['asignatura_delete_confirmar'] = params_old.get('asignatura_delete_confirmar', False)
    params['current_asignatura_id'] = params_old.get('current_asignatura_id', 0)
    current_asignatura_id = params['current_asignatura_id']

    if params['asignatura_delete_confirmar']:
        params['asignatura_delete_confirmar'] = False
        asignatura_delete_sql = asignatura_by_id(current_asignatura_id)
        session_sql.delete(asignatura_delete_sql)
        session_sql.commit()
        flash_toast(Markup('<strong>') + asignatura_delete_sql.nombre + Markup('</strong>') + ' elminado', 'success')
        return redirect(url_for('asignaturas_html', params=dic_encode(params)))

    stats = {}
    stats['evolucion_tutorias_exito_grupo'] = evolucion_tutorias_exito_grupo(g.settings_current_user.grupo_activo_id)[0]
    stats['evolucion_tutorias_exito_grupo_media'] = evolucion_tutorias_exito_grupo(g.settings_current_user.grupo_activo_id)[1]

    if not g.settings_current_user.grupo_activo_id:
        params['collapse_grupo_add'] = True
        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

    if request.method == 'POST':
        # NOTE almacena current_asignatura_id para el resto de situacones
        current_asignatura_id = current_id_request('current_asignatura_id')
        params['current_asignatura_id'] = current_asignatura_id

        # XXX selector_asignaturas_orden_switch
        if request.form['selector_button'] == 'asignaturas_orden_switch':
            current_asignaturas_orden = request.form.get('asignaturas_orden')
            if current_asignaturas_orden == 'True':
                current_asignaturas_orden = False
            else:
                current_asignaturas_orden = True
            settings_edit = g.settings_current_user
            settings_edit.asignaturas_orden = current_asignaturas_orden
            session_sql.commit()
            flash_toast('Asignaturas ordenadas por ' + asignaturas_orden_switch(current_asignaturas_orden), 'success')
            return redirect(url_for('asignaturas_html'))

        # XXX selector_asignatura_add
        if request.form['selector_button'] == 'selector_asignatura_add':
            params['anchor'] = 'anchor_asi_add'
            params['collapse_asignatura_add'] = True
            asignatura_add_form = Asignatura_Add(request.form)
            if asignatura_add_form.validate():
                asignatura_asignatura = session_sql.query(Asignatura).filter(Asignatura.grupo_id == g.settings_current_user.grupo_activo_id, unaccent(func.lower(Asignatura.asignatura)) == unaccent(func.lower(asignatura_add_form.asignatura.data))).first()
                asignatura_email = session_sql.query(Asignatura).filter(Asignatura.grupo_id == g.settings_current_user.grupo_activo_id, func.lower(Asignatura.email) == func.lower(asignatura_add_form.email.data)).first()
                asignatura_add = Asignatura(grupo_id=g.settings_current_user.grupo_activo_id, nombre=asignatura_add_form.nombre.data.title(), apellidos=asignatura_add_form.apellidos.data.title(), asignatura=asignatura_add_form.asignatura.data.title(), email=asignatura_add_form.email.data.lower())
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
                asignatura_edit = Asignatura(grupo_id=g.settings_current_user.grupo_activo_id, nombre=asignatura_edit_form.nombre.data.title(), apellidos=asignatura_edit_form.apellidos.data.title(), asignatura=asignatura_edit_form.asignatura.data.title(), email=asignatura_edit_form.email.data)
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
        # if request.form['selector_button'] == 'selector_asignatura_edit_rollback':
        #     params['asignatura_edit_link'] = True
        #     params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))
        #     session_sql.rollback()
        #     return redirect(url_for('asignaturas_html', params=dic_encode(params)))

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
                settings_add.diferencial_default = g.settings_global.diferencial_default
                params['current_user_id'] = user_add.id

                if user_add.email == 'antonioelmatematico@gmail.com':
                    settings_add.role = 'admin'
                    settings_add.email_validated = True
                session_sql.commit()
                send_email_validate_asincrono(user_add)
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
        user = user_by_id(current_user_id)
        email_validated_intentos_add = settings_by_id(current_user_id).email_validated_intentos + 1
        settings_edit = settings_by_id(current_user_id)
        settings_edit.email_validated_intentos = email_validated_intentos_add
        session_sql.commit()
        params['email_validated_intentos'] = email_validated_intentos_add
        send_email_validate_asincrono(user)
        return redirect(url_for('login_validacion_email_html', params=dic_encode(params)))
    try:
        params['email_validated_intentos'] = settings_by_id(current_user_id).email_validated_intentos
    except:
        abort(404)

    return render_template('login_validacion_email.html', params=params)

# XXX wellcome


@app.route('/wellcome')
@login_required
def wellcome_html():
    params = {}
    params['anchor'] = 'anchor_top'
    return render_template('wellcome.html', params=params)


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
            return redirect(url_for('wellcome_html', params=dic_encode(params)))
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
                    flash_toast('Bienvenido ' + Markup('<strong>') + login_form.username.data + Markup('</strong>'), 'success')
                    if not settings.grupo_activo_id:
                        params['login'] = True  # NOTE Para activar como activo el primer grupo creado y redirect a alumnos (por facilidad para un nuevo usuario)
                        return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
                    return redirect(url_for('tutorias_html'))
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
