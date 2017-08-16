from app import app
from functions import *
import functions

# ****************************


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


@app.route('/getos')
def getos():
    return (os.name)


@app.errorhandler(404)
def page_not_found_html(warning):
    params = params_default
    fab = Fab(True, False, False, True, True, True, True)
    return render_template('page_not_found.html', fab=fab, params=params)

# NOTE calendar_token
# de momento he forzado False, mas adelante sera tomado de settings


@app.route('/')
def index_html():
    return redirect(url_for('alumnos_html'))


# XXX user_ficha_grupos
@app.route('/user_ficha_grupos', methods=['GET', 'POST'])
@app.route('/user_ficha_grupos/<params>', methods=['GET', 'POST'])
@login_required
def user_ficha_grupos_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    fab = Fab(True, False, False, True, True, True, True)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_user_id'] = params_old.get('current_user_id', hashids_encode(0))
    current_user_id = params['current_user_id']
    user = user_by_id(current_user_id)

    return render_template(
        'user_ficha_grupos.html', fab=fab, user=user, params=params)


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
    fab = Fab(True, False, False, True, True, True, True)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_user_id'] = params_old.get('current_user_id', hashids_encode(0))
    current_user_id = params['current_user_id']
    user = user_by_id(current_user_id)

    return render_template(
        'user_ficha_alumnos.html', fab=fab, user=user, params=params)


# XXX pruebas


@app.route('/pagina_1/', methods=['GET', 'POST'])
@app.route('/pagina_1/<params>', methods=['GET', 'POST'])
@login_required
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

    return render_template('pagina_1.html', par_1=par_1, par_2=par_2, params=params)


@app.route('/pagina_2', methods=['GET', 'POST'])
@login_required
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
    fab = Fab(True, False, False, False, True, True, True)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['collapse_alumno_add'] = params_old.get('collapse_alumno_add', False)
    params['alumno_importar_link'] = params_old.get('alumno_importar_link', False)
    params['collapse_alumno'] = params_old.get('collapse_alumno', False)
    params['alumno_edit_link'] = params_old.get('alumno_edit_link', False)
    params['collapse_alumno_edit'] = params_old.get('collapse_alumno_edit', False)
    params['collapse_alumno_edit_asignaturas'] = params_old.get('collapse_alumno_edit_asignaturas', False)
    params['current_alumno_id'] = params_old.get('current_alumno_id', hashids_encode(0))
    params['from_url'] = params_old.get('from_url', False)
    params['alumno_delete_link'] = params_old.get('alumno_delete_link', False)
    params['collapse_tutorias'] = params_old.get('collapse_tutorias', False)
    params['collapse_tutoria_no_activas'] = params_old.get('collapse_tutoria_no_activas', False)
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', hashids_encode(0))
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
                        'alumnos.html', fab=fab, alumno_add=alumno_add_form, alumno_edit=Alumno_Add(), tutoria_add=Tutoria_Add(),
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
                    'alumnos.html', fab=fab, alumno_add=alumno_add_form, alumno_edit=Alumno_Add(), tutoria_add=Tutoria_Add(),
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
                        alumno_apellidos = alumno['Alumno/a'].split(', ')[0]
                        alumno_nombre = alumno['Alumno/a'].split(', ')[1]
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
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))

            # ***************************************
            if alumno_edit_form.validate():
                alumno_edit = Alumno(grupo_id=settings().grupo_activo_id, nombre=alumno_edit_form.nombre.data.title(), apellidos=alumno_edit_form.apellidos.data.title())
                alumno_sql = session_sql.query(Alumno).filter_by(id=current_alumno_id).first()
                if alumno_sql.nombre.lower() != alumno_edit.nombre.lower() or alumno_sql.apellidos.lower() != alumno_edit.apellidos.lower():
                    session_sql.begin_nested()
                    if alumno_sql.nombre.lower() != alumno_edit.nombre.lower():
                        alumno_sql.nombre = alumno_edit.nombre.title()
                        flash_toast(Markup('<strong>') + alumno_edit.nombre + Markup('</strong>') + ' actualizado', 'success')
                    if alumno_sql.apellidos.lower() != alumno_edit.apellidos.lower():
                        alumno_sql.apellidos = alumno_edit.apellidos.title()
                        flash_toast(Markup('<strong>') + alumno_edit.apellidos + Markup('</strong>') + ' actualizado', 'success')
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))
                session_sql.begin_nested()
                session_sql.commit()
                # XXX redirect a tutoria_add
                if params['from_url'] == 'from_tutoria_add':
                    params['collapse_alumno'] = True
                    params['collapse_tutoria_add'] = True
                    params['anchor'] = 'anchor_tut_add_' + str(hashids_encode(current_alumno_id))
                    return redirect(url_for('alumnos_html', params=dic_encode(params)))
            else:
                flash_wtforms(alumno_edit_form, flash_toast, 'warning')
            return render_template('alumnos.html', fab=fab, alumno_add=Alumno_Add(), alumno_edit=alumno_edit_form,
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
                params['anchor'] = 'anchor_alu_asig_' + str(hashids_encode(current_alumno_id))
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
                            send_email_tutoria(alumno, tutoria_add)
                            flash_toast('Enviando emails al equipo educativo de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>'), 'secondary')
                            params['current_alumno_id'] = current_alumno_id
                            params['collapse_alumno'] = True
                            params['collapse_tutorias'] = True
                            params['anchor'] = 'anchor_top'
                            return redirect(url_for('alumnos_html', params=dic_encode(params)))
                else:
                    flash_wtforms(tutoria_add_form, flash_toast, 'warning')
            return render_template(
                'alumnos.html', fab=fab, alumno_add=Alumno_Add(), alumno_edit=Alumno_Add(),
                tutoria_add=tutoria_add_form, params=params)

        # XXX selector_tutoria_add_close
        if request.form['selector_button'] == 'selector_tutoria_add_close':
            return redirect(url_for('alumnos_html', params=dic_encode(params)))

    # XXX tutorias_timeout
    tutorias_timeout()
    return render_template(
        'alumnos.html', fab=fab, alumno_add=Alumno_Add(), alumno_edit=Alumno_Add(),
        tutoria_add=Tutoria_Add(), tutoria_edit=Tutoria_Add(), asignatura_add=Asignatura_Add(),
        params=params)

# XXX settings_admin_cuestionario


@app.route('/settings_admin_cuestionario', methods=['GET', 'POST'])
@app.route('/settings_admin_cuestionario/<params>', methods=['GET', 'POST'])
@login_required
def settings_admin_cuestionario_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    fab = Fab(True, False, False, True, True, True, False)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_pregunta_id'] = params_old.get('current_pregunta_id', hashids_encode(0))
    params['collapse_pregunta_edit'] = params_old.get('collapse_pregunta_edit', False)
    params['pregunta_delete_link'] = params_old.get('pregunta_delete_link', False)
    params['collapse_pregunta_add'] = params_old.get('collapse_pregunta_add', False)

    if request.method == 'POST':

        # XXX pregunta_add
        if request.form['selector_button'] == 'selector_pregunta_add':
            pregunta_add_form = Pregunta_Add(request.form)
            if pregunta_add_form.validate():
                pregunta_add_visible = request.form.get('pregunta_add_visible')
                pregunta_add_active_default = request.form.get('pregunta_add_active_default')
                pregunta_add = Pregunta(enunciado=pregunta_add_form.enunciado.data, enunciado_ticker=pregunta_add_form.enunciado_ticker.data,
                                        orden=pregunta_add_form.orden.data, visible=pregunta_add_visible, active_default=pregunta_add_active_default)
                # NOTE checking unicidad de enunciado, ticker y orden
                pregunta_enunciado_sql = session_sql.query(Pregunta).filter(Pregunta.enunciado == pregunta_add_form.enunciado.data).first()
                pregunta_enunciado_ticker_sql = session_sql.query(Pregunta).filter(Pregunta.enunciado_ticker == pregunta_add_form.enunciado_ticker.data).first()
                pregunta_orden_sql = session_sql.query(Pregunta).filter(Pregunta.orden == pregunta_add_form.orden.data).first()
                if pregunta_enunciado_sql or pregunta_enunciado_ticker_sql or pregunta_orden_sql:
                    params['collapse_pregunta_add'] = True
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
                        'settings_admin_cuestionario.html', fab=fab,  pregunta_add=pregunta_add_form, preguntas=preguntas(''),
                        pregunta_edit=Pregunta_Add(), params=params)
                else:
                    session_sql.add(pregunta_add)
                    session_sql.commit()
                    flash_toast('Pregunta agregada', 'success')
                    return redirect(url_for('settings_admin_cuestionario_html', params=dic_encode(params)))
            else:
                params['collapse_pregunta_add'] = True
                flash_wtforms(pregunta_add_form, flash_toast, 'warning')
            return render_template(
                'settings_admin_cuestionario.html', fab=fab, pregunta_add=pregunta_add_form, preguntas=preguntas(''),
                pregunta_edit=Pregunta_Add(), params=params)

        # XXX selector_pregunta_add_close
        if request.form['selector_button'] == 'selector_pregunta_add_close':
            return redirect(url_for('settings_admin_cuestionario_html'))

        # XXX pregunta_edit
        if request.form['selector_button'] in ['selector_pregunta_edit', 'selector_move_down', 'selector_move_up']:
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            move_up = False
            move_down = False
            pregunta_edit_form = Pregunta_Add(request.form)
            pregunta_edit_visible = request.form.get('pregunta_edit_visible')
            pregunta_edit_active_default = request.form.get('pregunta_edit_active_default')
            if not pregunta_edit_visible:
                pregunta_edit_visible = False
            if not pregunta_edit_active_default:
                pregunta_edit_active_default = False
            if pregunta_edit_form.validate():
                pregunta_edit = Pregunta(enunciado=pregunta_edit_form.enunciado.data, enunciado_ticker=pregunta_edit_form.enunciado_ticker.data,
                                         orden=pregunta_edit_form.orden.data, visible=pregunta_edit_visible, active_default=pregunta_edit_active_default)
                pregunta = session_sql.query(Pregunta).filter(Pregunta.id == current_pregunta_id).first()
                if pregunta.enunciado.lower() != pregunta_edit.enunciado.lower() or pregunta.enunciado_ticker.lower() != pregunta_edit.enunciado_ticker.lower() or pregunta.orden != pregunta_edit.orden or str(pregunta.visible) != str(pregunta_edit_visible) or str(pregunta.active_default) != str(pregunta_edit_active_default):
                    if pregunta.enunciado.lower() != pregunta_edit.enunciado.lower():
                        pregunta.enunciado = pregunta_edit.enunciado
                    if pregunta.enunciado_ticker.lower() != pregunta_edit.enunciado_ticker.lower():
                        pregunta.enunciado_ticker = pregunta_edit.enunciado_ticker
                    if pregunta.orden != pregunta_edit.orden:
                        pregunta.orden = pregunta_edit.orden
                    if pregunta.visible != pregunta_edit_visible:
                        pregunta.visible = pregunta_edit_visible
                    if pregunta.active_default != pregunta_edit_active_default:
                        pregunta.active_default = pregunta_edit_active_default
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

                session_sql.begin_nested()  # FIXME no encuetro el motivo por el cual hace un rollback de varias preguntas
                session_sql.commit()
                return redirect(url_for('settings_admin_cuestionario_html', params=dic_encode(params)))

            else:
                flash_wtforms(pregunta_edit_form, flash_toast, 'warning')
            return render_template(
                'settings_admin_cuestionario.html', fab=fab, pregunta_add=Pregunta_Add(), preguntas=preguntas(''),
                pregunta_edit=pregunta_edit_form, move_down=move_down, move_up=move_up, visible=pregunta_edit_visible,
                active_default=pregunta_edit_active_default, params=params)

        # XXX selector_pregunta_edit_close
        if request.form['selector_button'] == 'selector_pregunta_edit_close':
            return redirect(url_for('settings_admin_cuestionario_html'))

        # XXX selector_pregunta_edit_rollback
        if request.form['selector_button'] == 'selector_pregunta_edit_rollback':
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            session_sql.rollback()
            return redirect(url_for('settings_admin_cuestionario_html', params=dic_encode(params)))

        # XXX selector_pregunta_delete_link
        if request.form['selector_button'] == 'selector_pregunta_delete_link':
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            params['pregunta_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('settings_admin_cuestionario_html', params=dic_encode(params)))

        # XXX pregunta_delete
        if request.form['selector_button'] == 'selector_pregunta_delete':
            pregunta_delete_form = Pregunta_Add(request.form)
            current_pregunta_id = current_id_request('current_pregunta_id')
            pregunta_delete = pregunta_by_id(current_pregunta_id, '')
            session_sql.delete(pregunta_delete)
            session_sql.commit()
            flash_toast('Pregunta elminada', 'success')
            return redirect(url_for('settings_admin_cuestionario_html'))

        # XXX pregunta_delete_close
        if request.form['selector_button'] == 'selector_pregunta_delete_close':
            current_pregunta_id = current_id_request('current_pregunta_id')
            params['current_pregunta_id'] = current_pregunta_id
            params['collapse_pregunta_edit'] = True
            params['anchor'] = 'anchor_pre_' + str(hashids_encode(current_pregunta_id))
            return redirect(url_for('settings_admin_cuestionario_html', params=dic_encode(params)))

    return render_template(
        'settings_admin_cuestionario.html', fab=fab, pregunta_add=Pregunta_Add(), preguntas=preguntas(''),
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
    fab = Fab(True, False, False, True, True, False, True)
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
            session_sql.begin_nested()
            session_sql.commit()
            if not settings().preguntas:
                flash_toast('Cuestionario vacío', 'warning')
            else:
                if contador != 0:
                    flash_toast('Cuestionario  actualizado', 'success')
                    contador = 0
            return redirect(url_for('settings_cuestionario_html'))
    return render_template('settings_cuestionario.html', fab=fab, params=params)

# XXX user_grupos


@app.route('/user_grupos', methods=['GET', 'POST'])
@login_required
def user_grupos_html():

    current_user_id = request.args.get('i_7', False)
    user = user_by_id(current_user_id)
    grupos = user_grupos(current_user_id)
    return render_template('user_grupos.html', fab=Fab(True, False, False, True, True, True, True), user=user, grupos=grupos)

# XXX analisis


@app.route('/tutoria_no_disponible', methods=['GET', 'POST'])
@app.route('/tutoria_no_disponible/<params>', methods=['GET', 'POST'])
@login_required
def tutoria_no_disponible_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)

    params = {}
    fab = Fab(True, False, False, True, True, True, True)
    return render_template('tutoria_no_disponible.html', fab=fab, params=params)


@app.route('/analisis', methods=['GET', 'POST'])
@app.route('/analisis/<params>', methods=['GET', 'POST'])
@login_required
def analisis_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)
    params = {}
    fab = Fab(True, False, False, True, True, True, True)
    params['current_tutoria_id'] = params_old.get('current_tutoria_id', hashids_encode(0))
    current_tutoria_id = params['current_tutoria_id']
    params['tutoria_delete_link'] = params_old.get('tutoria_delete_link', False)
    params['tutoria_re_enviar_link'] = params_old.get('tutoria_re_enviar_link', False)
    params['tutoria_edit_link'] = params_old.get('tutoria_edit_link', False)

    if current_tutoria_id == hashids_encode(0):
        return redirect(url_for('tutoria_no_disponible_html', params=dic_encode(params)))

    grupo = grupo_activo()
    tutoria = tutoria_by_id(current_tutoria_id)
    alumno = invitado_alumno(current_tutoria_id)
    df_data = df_load()
    return render_template(
        'analisis.html', fab=fab, grupo=grupo, alumno=alumno, tutoria=tutoria, df_data=df_data,
        tutoria_edit=Tutoria_Add(), params=params)


# XXX tutoria_edit
@app.route('/tutoria_edit', methods=['GET', 'POST'])
@login_required
def tutoria_edit_html():

    if request.method == 'POST':
        fab = Fab(True, False, False, True, True, True, True)
        params = {}
        current_tutoria_id = current_id_request('current_tutoria_id')
        params['current_tutoria_id'] = current_tutoria_id

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
                print('asignaturas_id_lista:', asignaturas_id_lista)
                print('current_tutoria_id:', current_alumno_id)
                re_send_email_tutoria(alumno, current_tutoria, asignaturas_id_lista)
                flash_toast('Reenviando emails al equipo educativo de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>'), 'secondary')
                params['tutoria_re_enviar_link'] = False
                return redirect(url_for('analisis_html', params=dic_encode(params)))
            else:
                params['tutoria_re_enviar_link'] = True
                # ***************************
                grupo = invitado_grupo(current_tutoria_id)
                tutoria = tutoria_by_id(current_tutoria_id)
                alumno = invitado_alumno(current_tutoria_id)
                df_data = df_load()
                # ***************************
                flash_toast('Emails no reenviados' + Markup('<br>') + 'Hay que asignar al menos una asignatura', 'warning')
                return render_template('analisis.html', fab=fab, grupo=grupo, alumno=alumno, tutoria=tutoria, df_data=df_data, params=params)
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
                flash_toast('No se puede activar una tutoria pasada' + Markup('<br>') + 'Debe cambiar fecha y activarla', 'warning')
            else:
                tutoria_to_move.activa = True
                session_sql.commit()
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

        # XXX tutoria_edit_close
        if request.form['selector_button'] == 'selector_tutoria_edit_close':
            return redirect(url_for('analisis_html', params=dic_encode(params)))

        # XXX tutoria_edit
        if request.form['selector_button'] == 'selector_tutoria_edit':
            params['tutoria_edit_link'] = True
            grupo = invitado_grupo(current_tutoria_id)
            tutoria = tutoria_by_id(current_tutoria_id)
            alumno = invitado_alumno(current_tutoria_id)
            df_data = df_load()
            tutoria_sql = session_sql.query(Tutoria).filter(Tutoria.id == current_tutoria_id).first()
            tutoria_edit_form = Tutoria_Add(current_tutoria_id=current_tutoria_id, fecha=request.form.get('fecha'), hora=request.form.get('hora'))
            if tutoria_edit_form.validate():
                tutoria_edit_form_fecha = datetime.datetime.strptime(tutoria_edit_form.fecha.data, '%A-%d-%B-%Y').strftime('%Y-%m-%d')
                if datetime.datetime.strptime(tutoria_edit_form_fecha, '%Y-%m-%d').date() < g.current_date:
                    tutoria_edit_form.fecha.errors = ['Fecha no actualizada.']
                    flash_wtforms(tutoria_edit_form, flash_toast, 'warning')
                    flash_toast('Debe indicar una fecha posterior', 'warning')
                    return render_template(
                        'analisis.html', fab=fab, grupo=grupo, alumno=alumno, tutoria=tutoria, df_data=df_data,
                        tutoria_edit=tutoria_edit_form, params=params)
                else:
                    tutoria_sql.fecha = tutoria_edit_form_fecha
                    tutoria_sql.hora = string_to_time(tutoria_edit_form.hora.data)
                    tutoria_sql.activa = True
                    session_sql.begin_nested()
                    session_sql.commit()
                    flash_toast('Tutoria actualizada', 'success')
                    params['tutoria_edit_link'] = False
                    return redirect(url_for('analisis_html', params=dic_encode(params)))
            else:
                flash_wtforms(tutoria_edit_form, flash_toast, 'warning')
                return render_template(
                    'analisis.html', fab=fab, grupo=grupo, alumno=alumno, tutoria=tutoria, df_data=df_data,
                    tutoria_edit=tutoria_edit_form, params=params)

        # XXX tutoria_edit_rollback
        if request.form['selector_button'] == 'selector_tutoria_edit_rollback':
            session_sql.rollback()
            return redirect(url_for('analisis_html', params=dic_encode(params)))
    else:
        abort(404)


# XXX settings_options
@app.route('/settings_options', methods=['GET', 'POST'])
@app.route('/settings_options/<params>', methods=['GET', 'POST'])
@login_required
def settings_options_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)

    params = {}
    fab = Fab(True, False, False, True, True, False, True)
    params['anchor'] = params_old.get('anchor', 'anchor_top')

    settings_user = settings()
    if request.method == 'POST':
        # XXX settings_edit
        if request.form['selector_button'] == 'selector_user_edit':
            settings_edit_tutoria_timeout = request.form.get('settings_edit_tutoria_timeout')
            settings_edit_show_tutorias_collapse = request.form.get('settings_edit_show_tutorias_collapse')
            settings_edit_calendar = request.form.get('settings_edit_calendar')
            if not settings_edit_tutoria_timeout:
                settings_edit_tutoria_timeout = False
            if not settings_edit_calendar:
                settings_edit_calendar = False
            if not settings_edit_show_tutorias_collapse:
                settings_edit_show_tutorias_collapse = False

            settings().tutoria_timeout = settings_edit_tutoria_timeout
            settings().show_tutorias_collapse = settings_edit_show_tutorias_collapse
            settings().calendar = settings_edit_calendar
            flash_toast('Configuracion actualizada', 'success')
            session_sql.begin_nested()
            session_sql.commit()
            return redirect(url_for('settings_options_html'))

    return render_template(
        'settings_options.html', fab=fab, settings_user=settings_user, params=params)


# XXX settings_admin_users
@app.route('/settings_admin_users', methods=['GET', 'POST'])
@app.route('/settings_admin_users/<params>', methods=['GET', 'POST'])
@login_required
def settings_admin_users_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    fab = Fab(True, False, False, True, True, True, False)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['current_settings_id'] = params_old.get('current_settings_id', hashids_encode(0))
    params['collapse_user_edit'] = params_old.get('collapse_user_edit', False)
    params['user_delete_link'] = params_old.get('user_delete_link', False)

    settings_all = session_sql.query(Settings).order_by(desc('visit_last')).all()
    if request.method == 'POST':
        # XXX settings_edit
        if request.form['selector_button'] == 'selector_user_edit':
            settings_edit_form = Settings_Edit(request.form)
            current_settings_id = current_id_request('current_settings_id')
            params['current_settings_id'] = current_settings_id
            settings_edit_ban = request.form.get('settings_edit_ban')
            settings_edit_tutoria_timeout = request.form.get('settings_edit_tutoria_timeout')
            settings_edit_calendar = request.form.get('settings_edit_calendar')
            params['collapse_user_edit'] = True
            params['anchor'] = 'anchor_set_' + str(hashids_encode(current_settings_id))
            if not settings_edit_ban:
                settings_edit_ban = False
            if not settings_edit_tutoria_timeout:
                settings_edit_tutoria_timeout = False
            if not settings_edit_calendar:
                settings_edit_calendar = False

            if settings_edit_form.validate():
                settings_sql = session_sql.query(Settings).filter(Settings.id == current_settings_id).first()
                settings_sql.role = settings_edit_form.role.data
                settings_sql.ban = settings_edit_ban
                settings_sql.tutoria_timeout = settings_edit_tutoria_timeout
                settings_sql.calendar = settings_edit_calendar
                flash_toast(Markup('Usuario <strong>') + user_by_id(current_settings_id).username + Markup('</strong>') + ' actualizado', 'success')
                session_sql.begin_nested()
                session_sql.commit()
                return redirect(url_for('settings_admin_users_html', params=dic_encode(params)))

            else:
                flash_wtforms(settings_edit_form, flash_toast, 'warning')

            return render_template(
                'settings_admin_users.html', fab=fab, settings_all=settings_all, settings_edit=settings_edit_form,
                settings_edit_ban=settings_edit_ban, settings_edit_tutoria_timeout=settings_edit_tutoria_timeout,
                settings_edit_calendar=settings_edit_calendar, params=params)

        # XXX selector_user_edit_close
        if request.form['selector_button'] == 'selector_user_edit_close':
            return redirect(url_for('settings_admin_users_html'))

        # XXX user_edit_rollback
        if request.form['selector_button'] == 'selector_user_edit_rollback':
            current_settings_id = current_id_request('current_settings_id')
            params['current_settings_id'] = current_settings_id
            params['collapse_user_edit'] = True
            params['anchor'] = 'anchor_set_' + str(hashids_encode(current_settings_id))
            session_sql.rollback()
            return redirect(url_for('settings_admin_users_html', params=dic_encode(params)))

        # XXX user_delete_link
        if request.form['selector_button'] == 'selector_user_delete_link':
            current_settings_id = current_id_request('current_settings_id')
            params['current_settings_id'] = current_settings_id
            params['collapse_user_edit'] = True
            params['anchor'] = 'anchor_set_' + str(hashids_encode(current_settings_id))
            params['user_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('settings_admin_users_html', params=dic_encode(params)))

        # XXX user_delete
        if request.form['selector_button'] == 'selector_user_delete':
            if request.form['selector_button'] == 'selector_user_delete':
                current_settings_id = current_id_request('current_settings_id')
                user_sql = session_sql.query(User).filter(User.id == current_settings_id).first()
                session_sql.delete(user_sql)
                session_sql.commit()
                flash_toast(Markup('Usuario <strong>') + user_sql.username + Markup('</strong>') + ' elminado', 'success')
                return redirect(url_for('settings_admin_users_html'))

        # XXX user_delete_close
        if request.form['selector_button'] == 'selector_user_delete_close':
            current_settings_id = current_id_request('current_settings_id')
            params['current_settings_id'] = current_settings_id
            params['collapse_user_edit'] = True
            params['anchor'] = 'anchor_set_' + str(hashids_encode(current_settings_id))
            return redirect(url_for('settings_admin_users_html', params=dic_encode(params)))

    return render_template(
        'settings_admin_users.html', fab=fab, settings_all=settings_all, settings_edit=Settings_Edit(),
        params=params)


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
    fab = Fab(True, False, False, True, True, False, True)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['login'] = params_old.get('login', False)
    params['collapse_grupo_add'] = params_old.get('collapse_grupo_add', False)
    params['grupo_delete_link'] = params_old.get('grupo_delete_link', False)
    params['collapse_grupo_edit'] = params_old.get('collapse_grupo_edit', False)
    params['current_grupo_id'] = params_old.get('current_grupo_id', 0)

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
                        'settings_grupos.html', fab=fab, grupo_add=grupo_add_form, grupo_edit=Grupo_Add(), grupos=grupos(), params=params)
                else:
                    # NOTE set grupo_activo
                    session_sql.add(grupo_add)
                    session_sql.flush()
                    # session_sql.refresh(grupo_add)
                    if grupo_add_grupo_activo:
                        settings().grupo_activo_id = grupo_add.id
                        flash_toast(Markup('Grupo <strong>') + grupo_add_form.nombre.data + Markup('</strong>') + ' agregado' + Markup('<br>Ahora este es el nuevo actual grupo activo'), 'success')
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
            return render_template('settings_grupos.html',
                                   fab=fab, grupo_add=grupo_add_form, grupo_edit=Grupo_Add(), grupos=grupos(), params=params)

        # XXX selector_grupo_edit
        if request.form['selector_button'] == 'selector_grupo_edit':
            grupo_edit_form = Grupo_Add(request.form)
            params['collapse_grupo_edit'] = True
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
                    flash_toast(Markup('Grupo de <strong>') + grupo_edit.tutor + Markup('</strong>') + ' actualizado', 'success')
                    session_sql.begin_nested()
                    session_sql.commit()
                    return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
            else:
                flash_wtforms(grupo_edit_form, flash_toast, 'warning')
            return render_template(
                'settings_grupos.html', fab=fab, grupo_add=Grupo_Add(), grupos=grupos(), grupo_edit=grupo_edit_form, params=params)

        # XXX selector_grupo_edit_close
        if request.form['selector_button'] == 'selector_grupo_edit_close':
            return redirect(url_for('settings_grupos_html'))

        # XXX selector_grupo_edit_rollback
        if request.form['selector_button'] == 'selector_grupo_edit_rollback':
            params['collapse_grupo_edit'] = True
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            session_sql.rollback()
            return redirect(url_for('settings_grupos_html', params=dic_encode(params)))

        # XXX selector_grupo_delete_link
        if request.form['selector_button'] == 'selector_grupo_delete_link':
            params['collapse_grupo_edit'] = True
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
            params['anchor'] = 'anchor_gru_' + str(hashids_encode(current_grupo_id))
            return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
    return render_template(
        'settings_grupos.html', fab=fab, grupo_add=Grupo_Add(), grupo_edit=Grupo_Add(), grupos=grupos(), params=params)


# XXX settings_admin_citas
@app.route('/settings_admin_citas', methods=['GET', 'POST'])
@app.route('/settings_admin_citas/<params>', methods=['GET', 'POST'])
@login_required
def settings_admin_citas_html(params={}):
    try:
        params_old = dic_decode(params)  # NOTE matiene siempre una copia de entrada original por si se necesita mas adelante
    except:
        params_old = {}
        abort(404)

    params = {}
    fab = Fab(True, False, False, True, True, True, False)
    citas = session_sql.query(Cita).order_by(desc('created_at')).all()
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['collapse_cita_add'] = params_old.get('collapse_cita_add', False)
    params['current_cita_id'] = params_old.get('current_cita_id', hashids_encode(0))
    params['collapse_cita_edit'] = params_old.get('collapse_cita_edit', False)
    params['cita_delete_link'] = params_old.get('cita_delete_link', False)

    if request.method == 'POST':
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
                        'settings_admin_citas.html', fab=fab, cita_add=cita_add_form, cita_edit=Cita_Add(), citas=citas,
                        params=params)
                else:
                    session_sql.add(cita_add)
                    session_sql.commit()
                    flash_toast('Cita agregada', 'success')
                    return redirect(url_for('settings_admin_citas_html', params=dic_encode(params)))
            else:
                flash_wtforms(cita_add_form, flash_toast, 'warning')
            return render_template(
                'settings_admin_citas.html', fab=fab, cita_add=cita_add_form, cita_edit=Cita_Add(), citas=citas,
                params=params)

        if request.form['selector_button'] == 'selector_cita_add_close':
            return redirect(url_for('settings_admin_citas_html'))

        # XXX cita_edit
        if request.form['selector_button'] == 'selector_cita_edit':
            current_cita_id = current_id_request('current_cita_id')
            params['current_cita_id'] = current_cita_id
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
                    session_sql.begin_nested()
                    session_sql.commit()
                    return redirect(url_for('settings_admin_citas_html', params=dic_encode(params)))
            else:
                flash_wtforms(cita_edit_form, flash_toast, 'warning')
            return render_template(
                'settings_admin_citas.html', fab=fab, cita_add=Cita_Add(), citas=citas, cita_edit=cita_edit_form,
                cita_edit_visible=cita_edit_visible, params=params)
        # XXX selector_cita_edit_close
        if request.form['selector_button'] == 'selector_cita_edit_close':
            return redirect(url_for('settings_admin_citas_html'))

        # XXX cita_edit_rollback
        if request.form['selector_button'] == 'selector_cita_edit_rollback':
            current_cita_id = current_id_request('current_cita_id')
            params['current_cita_id'] = current_cita_id
            params['collapse_cita_edit'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            session_sql.rollback()
            return redirect(url_for('settings_admin_citas_html', params=dic_encode(params)))

        # XXX cita_delete_link
        if request.form['selector_button'] == 'selector_cita_delete_link':
            current_cita_id = current_id_request('current_cita_id')
            params['current_cita_id'] = current_cita_id
            params['collapse_cita_edit'] = True
            params['anchor'] = 'anchor_cit_' + str(hashids_encode(current_cita_id))
            params['cita_delete_link'] = True
            flash_toast('Debe confirmar la aliminacion', 'warning')
            return redirect(url_for('settings_admin_citas_html', params=dic_encode(params)))

        # XXX cita_delete
        if request.form['selector_button'] == 'selector_cita_delete':
            current_cita_id = current_id_request('current_cita_id')
            cita_delete_form = Cita_Add(request.form)
            cita_sql = session_sql.query(Cita).filter(Cita.id == current_cita_id).first()
            session_sql.delete(cita_sql)
            flash_toast('Cita elminada', 'success')
            session_sql.commit()
            return redirect(url_for('settings_admin_citas_html'))

        # XXX cita_delete_close
        if request.form['selector_button'] == 'selector_cita_delete_close':
            params['cita_delete_link'] = False
            return redirect(url_for('settings_admin_citas_html', params=dic_encode(params)))

    return render_template(
        'settings_admin_citas.html', fab=fab, cita_add=Cita_Add(), cita_edit=Cita_Add(), citas=citas,
        params=params)


# XXX informe_no_disponible
@app.route('/informe_no_disponible', methods=['GET', 'POST'])
def informe_no_disponible_html():

    return render_template('informe_no_disponible.html', params=params)


# XXX informe
@app.route('/informe/<token_hash>', methods=['GET', 'POST'])
def informe_html(token_hash):
    try:
        informe_check = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.token == token_hash).first()
    except:
        return redirect(url_for('informe_no_disponible_html'))
    params_anchor_off = True  # NOTE necesario para activar el anchor sin pasarlo por params
    if request.method == 'POST':
        token_hash = request.form.get('token_hash')
        tutoria_id = request.form.get('tutoria_id')
        asignatura_id = request.form.get('asignatura_id')
        tutoria = tutoria_by_id(tutoria_id)
        asignatura = asignatura_by_id(asignatura_id)
        grupo = invitado_grupo(tutoria_id)
        alumno = invitado_alumno(tutoria_id)
        settings = invitado_settings(tutoria_id)
        informe = invitado_informe(tutoria.id, asignatura.id)
        if not informe:
            informe_exist = 'False'
            informe = Informe(tutoria_id=tutoria.id, asignatura_id=asignatura.id, comentario=request.form.get('comentario'))
            session_sql.add(informe)
            for pregunta in invitado_preguntas(settings.id):
                respuesta = Respuesta(informe_id=informe.id, pregunta_id=pregunta.id, resultado=request.form.get('pregunta' + str(pregunta.id)))
                session_sql.add(respuesta)
        else:
            informe_exist = 'True'
            informe.comentario = comentario = request.form.get('comentario')

            for pregunta in invitado_preguntas(settings.id):
                respuesta = invitado_respuesta(informe.id, pregunta.id)
                if not respuesta:
                    respuesta_add = Respuesta(informe_id=informe.id, pregunta_id=pregunta.id, resultado=request.form.get('pregunta' + str(pregunta.id)))
                    session_sql.add(respuesta_add)
                else:
                    respuesta.resultado = request.form.get('pregunta' + str(pregunta.id))
            session_sql.commit()

        for prueba_evaluable in invitado_pruebas_evaluables(informe.id):
            prueba_evaluable.nota = request.form.get('prueba_evaluable_nota_' + str(prueba_evaluable.id))

        if request.form['selector_button'] == 'selector_prueba_evaluable_add':
            anchor = 'anchor_pru_eva'
            prueba_evaluable_nombre = request.form.get('prueba_evaluable_nombre')
            if not prueba_evaluable_nombre or prueba_evaluable_nombre == 'agregar prueba evaluable':
                prueba_evaluable = False
            prueba_evaluable_add = Prueba_Evaluable(informe_id=informe.id, nombre=prueba_evaluable_nombre, nota=0)
            session_sql.add(prueba_evaluable_add)
            return redirect(url_for('informe_html', token_hash=token_hash, anchor=anchor))

        if request.form['selector_button'] == 'selector_prueba_evaluable_delete':
            anchor = 'anchor_pru_eva'
            prueba_evaluable_delete = invitado_pruebas_evaluables(informe.id)[-1]
            print('nota:', prueba_evaluable_delete.nota)
            session_sql.delete(prueba_evaluable_delete)
            session_sql.commit()
            return redirect(url_for('informe_html', token_hash=token_hash, anchor=anchor))

        if request.form['selector_button'] == 'selector_informe_add':
            session_sql.begin_nested()  # NOTE no tengo claro si esto es util aqui
            session_sql.commit()
            flash_toast('Infome de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' enviado', 'success')
            params = {}
            params['token_hash'] = token_hash
            params['alumno'] = alumno.nombre + ' ' + alumno.apellidos
            params['grupo'] = grupo.nombre
            params['fecha'] = tutoria.fecha
            params['hora'] = tutoria.hora
            params['asignatura'] = asignatura.asignatura
            params['docente'] = asignatura.nombre + ' ' + asignatura.apellidos
            params['params_anchor_off'] = True
            params['invitado'] = True
            return redirect(url_for('informe_success_html', params=dic_encode(params)))

        return render_template(
            'informe.html', token_hash=token_hash, tutoria=tutoria, asignatura=asignatura,
            alumno=alumno, grupo=grupo, informe=informe)

    else:
        tutoria_id = int(informe_check.tutoria_id)
        asignatura_id = informe_check.asignatura_id
        tutoria = tutoria_by_id(tutoria_id)
        asignatura = asignatura_by_id(asignatura_id)
        alumno = alumno_by_id(tutoria.alumno_id)
        settings = invitado_settings(tutoria_id)
        grupo = alumno_grupo(alumno.id)
        informe = invitado_informe(tutoria_id, asignatura_id)
        anchor = request.args.get('anchor', 'anchor_top')

        return render_template(
            'informe.html', tutoria=tutoria, asignatura=asignatura,
            alumno=alumno, grupo=grupo, informe=informe, token_hash=token_hash,
            params_anchor_off=params_anchor_off, anchor=anchor)

# XXX informe_success


@app.route('/informe_success/<params>', methods=['GET', 'POST'])
def informe_success_html(params={}):
    try:
        params_old = dic_decode(params)
    except:
        params_old = {}
        abort(404)
    params = {}
    params_anchor_off = True  # NOTE necesario para activar el anchor sin pasarlo por params
    params['token_hash'] = params_old.get('token_hash', False)
    params['alumno'] = params_old.get('alumno', False)
    params['grupo'] = params_old.get('grupo', False)
    params['fecha'] = params_old.get('fecha', False)
    params['hora'] = params_old.get('hora', False)
    params['asignatura'] = params_old.get('asignatura', False)
    params['docente'] = params_old.get('docente', False)
    return render_template(
        'informe_success.html', params=params)


# XXX tutorial_email NOTE solo es para pruebas, esto no se usa en produccion


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

    fab = Fab(True, False, False, True, False, True, True)
    params['anchor'] = params_old.get('anchor', 'anchor_top')
    params['collapse_asignatura_add'] = params_old.get('collapse_asignatura_add', False)
    params['collapse_asignatura_edit'] = params_old.get('collapse_asignatura_edit', False)
    params['current_asignatura_id'] = params_old.get('current_asignatura_id', hashids_encode(0))
    params['asignatura_delete_link'] = params_old.get('asignatura_delete_link', False)
    params['asignatura_edit_link'] = params_old.get('asignatura_edit_link', False)

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
                if asignatura_asignatura:
                    flash_toast('Esta asignatura ya existe', 'warning')
                elif asignatura_email:
                    flash_toast('Este email ya esta asignado a otra asignatura', 'warning')
                else:
                    asignatura_add = Asignatura(grupo_id=settings().grupo_activo_id, nombre=asignatura_add_form.nombre.data.title(), apellidos=asignatura_add_form.apellidos.data.title(), asignatura=asignatura_add_form.asignatura.data.title(), email=asignatura_add_form.email.data.lower())
                    session_sql.add(asignatura_add)
                    session_sql.commit()
                    flash_toast('Asignatura agregada', 'success')
                    return redirect(url_for('asignaturas_html'))
            else:
                flash_wtforms(asignatura_add_form, flash_toast, 'warning')
            return render_template(
                'asignaturas.html', fab=fab, asignatura_add=asignatura_add_form, asignatura_edit=Asignatura_Add(),
                params=params)

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
            # ****************************************

            if asignatura_edit_form.validate():
                params['collapse_asignatura_edit'] = True
                params['anchor'] = 'anchor_asi_' + str(hashids_encode(current_asignatura_id))

                # # NOTE unicidad del nombre de asignatura
                asignatura_asignatura_unicidad = session_sql.query(Asignatura).filter(Asignatura.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Asignatura.asignatura)) == unaccent(func.lower(asignatura_edit_form.asignatura.data))).all()
                asignatura_asignatura_unicidad_lista = []
                for asignatura in asignatura_asignatura_unicidad:
                    if asignatura.id != current_asignatura_id:
                        asignatura_asignatura_unicidad_lista.append(asignatura.id)
                if len(asignatura_asignatura_unicidad_lista) != 0:
                    asignatura_edit_form.asignatura.errors = ['ya existe como asignatura.']
                    flash_toast(Markup('<strong>') + asignatura_edit_form.asignatura.data + Markup('</strong>') + ' ya existe como asignatura.', 'warning')

                # NOTE unicidad del email
                asignatura_email_unicidad = session_sql.query(Asignatura).filter(Asignatura.grupo_id == settings().grupo_activo_id, unaccent(func.lower(Asignatura.email)) == unaccent(func.lower(asignatura_edit_form.email.data))).all()
                if asignatura_email_unicidad:
                    asignatura_email_unicidad_lista = []
                    for asignatura in asignatura_email_unicidad:
                        if asignatura.id != current_asignatura_id:
                            asignatura_email_unicidad_lista.append(asignatura.id)
                    if len(asignatura_email_unicidad_lista) != 0:
                        asignatura_edit_form.email.errors = ['email asignado a otra asignatura.']
                        flash_toast('Este email ya esta asignado a otra asignatura.', 'warning')

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
                session_sql.begin_nested()
                session_sql.commit()
                return redirect(url_for('asignaturas_html', params=dic_encode(params)))
            else:
                flash_wtforms(asignatura_edit_form, flash_toast, 'warning')
            return render_template(
                'asignaturas.html', fab=fab, asignatura_add=Asignatura_Add(), asignatura_edit=asignatura_edit_form,
                params=params)

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
        'asignaturas.html', fab=fab, asignatura_add=Asignatura_Add(), asignatura_edit=Asignatura_Add(),
        asignaturas=asignaturas, params=params)


@app.route('/user_add', methods=['GET', 'POST'])
def user_add_html():
    fab = Fab(True, False, True, False, False, False, False)
    user_add_form = User_Add(request.form)
    if request.method == 'POST':
        if user_add_form.validate():
            user_username = session_sql.query(User).filter(func.lower(User.username) == func.lower(user_add_form.username.data)).first()
            user_email = session_sql.query(User).filter(func.lower(User.email) == func.lower(user_add_form.email.data)).first()
            if user_username:
                flash_toast(Markup('<strong>') + user_add_form.username.data + Markup('</strong>') + ' ,ya esta registrado', 'warning')
            elif user_email:
                flash_toast(Markup('<strong>') + user_add_form.email.data + Markup('</strong>') + ' ,ya esta registrado', 'warning')
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
                if user_add.email == 'antonioelmatematico@gmail.com':
                    settings_add.role = 'admin'
                session_sql.commit()
                flash_toast('Enhorabuena ' + user_add_form.username.data + ', cuenta creada.', 'success')
                return redirect(url_for('alumnos_html'))
        else:
            flash_wtforms(user_add_form, flash_toast, 'warning')
        return render_template('user_add.html', fab=fab, user_add=user_add_form)
    return render_template('user_add.html', fab=fab, user_add=User_Add())


# XXX login


@app.route('/login', methods=['GET', 'POST'])
def login_html():
    params = {}
    fab = Fab(True, True, False, False, False, False, False)
    session.clear()
    login_fail = False
    login_form = User_Login(request.form)
    ban = request.args.get('ban', False)
    if request.method == 'POST' and login_form.validate():
        user_sql = session_sql.query(User).filter_by(username=login_form.username.data).first()

        if ban:
            return render_template('login.html', fab=fab, user_login=login_form, login_fail=login_fail, params=params, ban=ban)
        if user_sql:
            if check_password_hash(user_sql.password, login_form.password.data):
                login_user(user_sql, remember=login_form.remember.data)
                settings = session_sql.query(Settings).filter(Settings.user_id == user_sql.id).first()
                settings.visit_last = datetime.datetime.now()
                settings.visit_number = settings.visit_number + 1
                if settings.ban:
                    ban = True
                    login_fail = True
                    flash_toast('Usuario ' + Markup('<strong>') + login_form.username.data + Markup('</strong> se encuentra temporalmente baneado<br>Por favor pongase en contacto con nosotros'), 'warning')
                    return redirect(url_for('login_html', ban=True))
                session_sql.commit()
                flash_toast('Bienvenido ' + Markup('<strong>') + login_form.username.data + Markup('</strong>'), 'success')
                if not settings.grupo_activo_id:
                    params['login'] = True  # NOTE Para activar como activo el primer grupo creado y redirect a alumnos (por facilidad para un nuevo usuario)
                    return redirect(url_for('settings_grupos_html', params=dic_encode(params)))
                return redirect(url_for('alumnos_html'))
            if user_sql.username == login_form.username:
                flash_toast('Contraseña incorrecta', 'warning')
            else:
                flash_toast('Usuario no registrado', 'warning')
        flash_toast(Markup('<strong>') + login_form.username.data + Markup('</strong>') + ' no existe como usuario' + Markup('<br>Debería crear una nueva cuenta.'), 'warning')
        login_fail = True
    return render_template('login.html', fab=fab, user_login=login_form, login_fail=login_fail, params=params, ban=ban)


@app.route('/logout')
def logout_html():
    params = {}
    fab = Fab(True, False, True, False, False, False, False)
    logout_user()
    flash_toast('Session cerrada', 'success')
    return render_template('logout.html', fab=fab, params=params)
