from app import app
from config_parametros import *
import config_parametros

# NOTE
# [] Lista
# () Objeto
# {} Valor
# *****************************************************************


def usuario_cuestionario(usuario_id):

    return session_sql.query(Pregunta).join(Settings).filter(Settings.id == usuario_id).all()


def dic_try_ORG(dic, string, value_default):  # NOTE util para variables que muchas veces usar el valor default como por ejemplo 'anchor'
    return dic.get(string, value_default)


def dic_try(dic, string, value_default):  # NOTE util para variables que muchas veces usar el valor default como por ejemplo 'anchor'
    try:
        return dic.get(string, value_default)  # NOTE con esta modificacion no tengo que declarar params={} y pasarlo en cada redner_template
    except:
        return value_default


def current_id_request(current_id_name):
    try:
        current_encoded = request.form.get(current_id_name)
        current_id = hashids_decode(str(current_encoded))
    except:
        current_id = 0
    return current_id


def f_decode(string_encoded):
    return f.decrypt(str.encode(string_encoded)).decode()


def f_encode(string):
    return f.encrypt(str.encode(str(string)))


def dic_decode(dic_encoded):
    if dic_encoded:
        return eval(f_decode(dic_encoded))
    else:
        return {}


def dic_encode_args(dic):
    return f_encode(str(dic)).decode()


def dic_encode(dic):
    return f_encode(str(dic))


def hashids_encode(numero):
    return hashids.encode(int(numero))


def hashids_decode(texto):
    return int(hashids.decode(texto)[0])


class unaccent(ReturnTypeFromArgs):  # NOTE es necesario para el check de nombres con acentos
    pass


def usuario_grupos(usuario_id):
    return session_sql.query(Grupo).filter(Grupo.settings_id == usuario_id).order_by(desc('created_at')).all()


def allowed_file(fichero_nombre):
    ALLOWED_EXTENSIONS = set(['csv'])
    return '.' in fichero_nombre and \
           fichero_nombre.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def asignatura_informes_count(asignatura_id):
    asignatura_informes_count = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.asignatura_id == asignatura_id).count()
    return asignatura_informes_count


def asignatura_informes_respondidos_count(asignatura_id):
    asignatura_informes_respondidos_count = session_sql.query(Informe).filter(Informe.asignatura_id == asignatura_id).count()
    return asignatura_informes_respondidos_count


def connenction_check():
    try:
        with mail.connect() as conn:
            for asignatura_id in asignaturas_id_lista:
                conn.send('prueba')
        print('OK')
    except:
        print('xxx ERROR xxx')


# XXX: envio de mails por threading
# *****************************************************************
def send_email_password_reset(current_user_id):
    msg = Message('Cambiar password', sender='mitutoria', recipients=[user_by_id(current_user_id).email])
    # mail texto plano
    msg.body = 'Cambiar password'
    # mail HTML
    msg.html = render_template('email_password_reset_request.html', current_user_id=current_user_id, password_reset_link=password_reset_link, index_link=index_link)
    mail.send(msg)


def send_email_password_reset_request_asincrono(current_user_id):
    @copy_current_request_context
    def send_email_password_reset_request_process(current_user_id):
        send_email_password_reset(current_user_id)
    send_email_password_reset_request_threading = threading.Thread(name='send_email_password_reset_request_thread', target=send_email_password_reset_request_process, args=(current_user_id,))
    send_email_password_reset_request_threading.start()


def send_email_validate(user_id):
    msg = Message('Verificar email', sender='mitutoria', recipients=[user_by_id(user_id).email])
    # mail texto plano
    msg.body = 'Verificación de email'
    # mail HTML
    msg.html = render_template('email_validate.html', user_id=user_id, email_validate_link=email_validate_link, index_link=index_link)
    mail.send(msg)


def send_email_validate_asincrono(user_id):
    @copy_current_request_context
    def send_email_validate_process(user_id):
        send_email_validate(user_id)
    send_email_validate_threading = threading.Thread(name='send_email_validate_thread', target=send_email_validate_process, args=(user_id,))
    send_email_validate_threading.start()


def send_email_tutoria(alumno, tutoria):
    with mail.connect() as conn:
        for asignatura in alumno_asignaturas(alumno.id):
            msg = Message('Tutoria | %s | %s' % (grupo_activo().nombre, alumno.nombre), sender='mitutoria | %s' % grupo_activo().tutor, recipients=[asignatura.email])
            # mail texto plano
            msg.body = 'Informe para la tutoria de ' + alumno.nombre + ' ' + alumno.apellidos
            tutoria_asignatura_add = Association_Tutoria_Asignatura(tutoria_id=tutoria.id, asignatura_id=asignatura.id)
            session_sql.add(tutoria_asignatura_add)
            session_sql.flush()
            # mail HTML
            msg.html = render_template('email_tutoria.html', tutoria=tutoria, alumno=alumno, asignatura=asignatura, tutoria_email_link=tutoria_email_link, tutoria_asignatura_id=tutoria_asignatura_add.id)
            time.sleep(email_time_sleep)
            conn.send(msg)
            session_sql.commit()


def send_email_tutoria_asincrono(alumno, tutoria):
    @copy_current_request_context
    def send_email_tutoria_process(alumno, tutoria):
        send_email_tutoria(alumno, tutoria)
    send_email_tutoria_threading = threading.Thread(name='send_email_tutoria_thread', target=send_email_tutoria_process, args=(alumno, tutoria))
    send_email_tutoria_threading.start()
    flash_toast('Tutoria generada para ' + Markup('<strong>') + alumno.nombre + Markup('</strong>'), 'success')


def re_send_email_tutoria(alumno, tutoria, asignaturas_id_lista):
    with mail.connect() as conn:
        for asignatura_id in asignaturas_id_lista:
            asignatura = asignatura_by_id(asignatura_id)  # FIXME creo que sera conveniente usar int(asignatura_id) [bastara hacer asignatura_id=int(asignatura_id)]
            tutoria_asignatura_add = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria.id, Association_Tutoria_Asignatura.asignatura_id == asignatura_id).first()
            if tutoria_asignatura_add:
                tutoria_asignatura_add.created_at = datetime.datetime.now()
            else:
                tutoria_asignatura_add = Association_Tutoria_Asignatura(tutoria_id=tutoria.id, asignatura_id=asignatura_id)
                session_sql.add(tutoria_asignatura_add)
            msg = Message('Tutoria | %s | %s' % (grupo_activo().nombre, alumno.nombre), sender='mitutoria | %s' % grupo_activo().tutor, recipients=[asignatura.email])
            # mail texto plano
            msg.body = 'Informe para la tutoria de ' + alumno.nombre + ' ' + alumno.apellidos
            # mail HTML
            msg.html = render_template('email_tutoria.html', tutoria=tutoria, alumno=alumno, asignatura=asignatura, tutoria_email_link=tutoria_email_link, tutoria_asignatura_id=tutoria_asignatura_add.id)
            time.sleep(email_time_sleep)
            conn.send(msg)
            session_sql.commit()


def re_send_email_tutoria_asincrono(alumno, tutoria, asignaturas_id_lista):
    @copy_current_request_context
    def re_send_email_tutoria_process(alumno, tutoria, asignaturas_id_lista):
        re_send_email_tutoria(alumno, tutoria, asignaturas_id_lista)
    re_send_email_tutoria_threading = threading.Thread(name='re_send_email_tutoria_thread', target=re_send_email_tutoria_process, args=(alumno, tutoria, asignaturas_id_lista))
    re_send_email_tutoria_threading.start()


# *****************************************************************


def tutoria_stats(tutoria_id):
    tutoria_informes_count = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id).count()
    tutoria_asignaturas_count = session_sql.query(Association_Tutoria_Asignatura).filter_by(tutoria_id=tutoria_id).count()
    return tutoria_informes_count, tutoria_asignaturas_count


def pregunta_delete(pregunta_delete_id):  # Delete pregunta
    pregunta_delete = session_sql.query(Pregunta).filter_by(id=pregunta_delete_id).first()
    session_sql.delete(pregunta_delete)
    session_sql.commit()


def alumno_delete(alumno_delete_id):  # Delete alumno
    alumno_delete = session_sql.query(Alumno).filter_by(id=alumno_delete_id).first()
    session_sql.delete(alumno_delete)
    session_sql.commit()


def asignatura_delete(asignatura_delete_id):  # Delete asignatura
    asignatura_sql = session_sql.query(Asignatura).filter_by(id=asignatura_delete_id).first()
    session_sql.delete(asignatura_sql)
    session_sql.commit()


def grupo_delete(grupo_delete_id):  # Delete grupo
    grupo_delete_sql = session_sql.query(Grupo).filter(Grupo.id == grupo_delete_id).first()
    if grupo_activo_check(grupo_delete_sql.id):
        settings_sql = session_sql.query(Settings).filter(Settings.id == settings().id).first()
        settings_sql.grupo_activo_id = None
    session_sql.delete(grupo_delete_sql)
    session_sql.commit()


def grupo_check():  # Comprueba si existe ya un grupo declarado como activo.
    if current_user:
        if settings().grupo_activo_id:
            return True
    return False


def grupo_activo():  # (Grupo) activo de usuario
    if settings():
        grupo_activo = session_sql.query(Grupo).filter(Grupo.id == settings().grupo_activo_id).first()
    return grupo_activo


def grupo_activo_check(grupo_id):  # Checkea si un grupo es el activo o no
    if grupo_id == settings().grupo_activo_id:
        return True
    else:
        return False


def pregunta_active_default_check(pregunta_id):
    active_default_check = False
    if pregunta_id:
        pregunta = session_sql.query(Pregunta).filter(Pregunta.id == pregunta_id).first()
        if pregunta.active_default:
            active_default_check = True
    return active_default_check


def pregunta_visible_check(pregunta_id):
    visible_check = False
    if pregunta_id:
        pregunta = session_sql.query(Pregunta).filter(Pregunta.id == pregunta_id).first()
        if pregunta.visible:
            visible_check = True
    return visible_check

# NOTE updating ................


def notas_asignatura_grupo_ORG(df_data, asignatura):
    notas_asignatura = []
    nota_media = []
    asignatura_sql = session_sql.query(Asignatura).join(Grupo).filter(Grupo.id == settings().grupo_activo_id).filter(Asignatura.asignatura == asignatura).first()
    informes = session_sql.query(Informe).filter(Informe.asignatura_id == asignatura_sql.id).all()
    for informe in informes:
        notas = session_sql.query(Prueba_Evaluable).filter(Prueba_Evaluable.informe_id == informe.id).all()
        if notas:
            for nota in notas:
                notas_asignatura.append(float(nota.nota))
    if notas_asignatura:
        nota_media = mean(notas_asignatura)
    else:
        nota_media = 'sin_notas'
    return nota_media


def notas_asignatura_grupo(df_data, asignatura, alumno_id):
    notas_asignatura = []
    nota_media = []
    notas = []
    asignatura_sql = session_sql.query(Asignatura).join(Grupo).filter(Grupo.id == settings().grupo_activo_id).filter(Asignatura.asignatura == asignatura).first()
    informes = session_sql.query(Informe).filter(Informe.asignatura_id == asignatura_sql.id).all()
    for informe in informes:
        alumno_informes = session_sql.query(Informe).join(Tutoria).join(Alumno).filter(Alumno.id == alumno_id)
        if informe not in alumno_informes:
            notas = session_sql.query(Prueba_Evaluable).filter(Prueba_Evaluable.informe_id == informe.id).all()
        if notas:
            for nota in notas:
                notas_asignatura.append(float(nota.nota))
    if notas_asignatura:
        nota_media = mean(notas_asignatura)
    else:
        nota_media = 'sin_notas'
    return nota_media


def notas_asignatura(df_data, tutoria_id, asignatura):  # NOTE aqui estaba el dichoso problema del NoneType al cargar analisis
    notas_asignatura = []
    nota_media = []
    # NOTE  hay que restringir al grupo activo para que indentifique correctamente la asignatura
    asignatura_sql = session_sql.query(Asignatura).join(Grupo).filter(Grupo.id == settings().grupo_activo_id).filter(Asignatura.asignatura == asignatura).first()
    informe = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id, Informe.asignatura_id == asignatura_sql.id).first()
    notas = session_sql.query(Prueba_Evaluable).filter(Prueba_Evaluable.informe_id == informe.id).all()
    if notas:
        for nota in notas:
            notas_asignatura.append(float(nota.nota))
        nota_media = mean(notas_asignatura)
    else:
        nota_media = 'sin_notas'
    return notas_asignatura, nota_media
    return notas_asignatura, nota_media


def settings():
    if current_user:
        settings = session_sql.query(Settings).filter(Settings.user_id == current_user.id).first()
    return settings


def settings_by_id(settings_id):
    settings_by_id = session_sql.query(Settings).filter(Settings.user_id == settings_id).first()
    return settings_by_id


def usuarios(order_by_1, order_by_2, order_by_3):

    # return session_sql.query(User).order_by(order_by_1, order_by_2, order_by_3).all()
    return session_sql.query(Settings).order_by(desc(order_by_1), order_by_2, order_by_3).all()


def user_by_id(user_id):
    user_by_id = session_sql.query(User).filter(User.id == user_id).first()
    return user_by_id


def preguntas_active_default(settings_id):  # Inserta las preguntas_active_default
    preguntas_id_lista = []
    preguntas_active_default = session_sql.query(Pregunta).filter(Pregunta.active_default == True).all()

    if preguntas_active_default:
        for pregunta in preguntas_active_default:
            preguntas_id_lista.append(pregunta.id)

    if preguntas_id_lista:
        for pregunta in preguntas('True'):
            if pregunta.id in preguntas_id_lista:
                if not association_settings_pregunta_check(settings_id, pregunta.id):
                    association_settings_pregunta_add = Association_Settings_Pregunta(settings_id=settings_id, pregunta_id=pregunta.id)
                    session_sql.add(association_settings_pregunta_add)
            else:
                if association_settings_pregunta_check(settings_id, pregunta.id):
                    association_settings_pregunta_delete = session_sql.query(Association_Settings_Pregunta).filter_by(settings_id=settings_id, pregunta_id=pregunta.id).first()
                    session_sql.delete(association_settings_pregunta_delete)


# NOTE: hay que usarlo para mantener el formato de texto asi como su posterior manipulacion
def asignatura_comentario(tutoria_id, asignatura_asignatura):
    asignatura_comentario = ''
    for informe in tutoria_informes(tutoria_id):
        asignatura = session_sql.query(Asignatura).filter(Asignatura.id == informe.asignatura_id).first()
        if asignatura.asignatura == asignatura_asignatura:
            asignatura_comentario = informe.comentario
    return asignatura_comentario


# XXX: pandas para admin
# -----------------------------------------------------------------------
def df_load_admin_usuarios():
    df_usuario = pd.read_sql_query(session_sql.query(User).statement, engine)
    df_usuario.drop(['id', 'password', 'email'], axis=1, inplace=True)
    df_data = df_usuario
    return df_data


def df_load_admin_settings():
    df_usuario = pd.read_sql_query(session_sql.query(User).statement, engine)
    df_usuario.drop(['password', 'email'], axis=1, inplace=True)
    df_usuario.rename(columns={'id': 'user_id'}, inplace=True)

    df_settings = pd.read_sql_query(session_sql.query(Settings).statement, engine)
    df_data = pd.merge(df_usuario, df_settings, how='inner', on=None, left_on='user_id', right_on='user_id', left_index=False, right_index=False, sort=False, suffixes=('_usuario', '_settings'), copy=False, indicator=False)
    df_data.drop(['user_id', 'calendar', 'grupo_activo_id', 'created_at', 'edited_at', 'show_tutorias',  'show_tutorias_collapse', 'role', 'email_validated_intentos', 'id'], axis=1, inplace=True)
    return df_data


def df_load_admin_tutorias():
    df_usuario = pd.read_sql_query(session_sql.query(User).statement, engine)
    df_data = df_usuario
    df_data.rename(columns={'id': 'user_id'}, inplace=True)
    df_data.drop(['password', 'email'], axis=1, inplace=True)
    # print(df_data)

    df_settings = pd.read_sql_query(session_sql.query(Settings).statement, engine)
    df_data = pd.merge(df_data, df_settings, how='inner', on=None, left_on='user_id', right_on='user_id', left_index=False, right_index=False, sort=False, suffixes=('_usuario', '_settings'), copy=False, indicator=False)
    df_data.drop(['id', 'username', 'calendar', 'grupo_activo_id', 'created_at', 'edited_at', 'visit_last', 'show_tutorias', 'email_validated', 'email_validated_intentos', 'email_robinson', 'role', 'ban', 'tutoria_timeout', 'show_tutorias_collapse', 'visit_number'], axis=1, inplace=True)
    # print(df_data)

    df_grupo = pd.read_sql_query(session_sql.query(Grupo).statement, engine)
    df_data = pd.merge(df_data, df_grupo, how='inner', on=None, left_on='user_id', right_on='settings_id', left_index=False, right_index=False, sort=False, suffixes=('_usuario', '_grupo'), copy=False, indicator=False)
    df_data.rename(columns={'id': 'grupo_id'}, inplace=True)
    df_data.drop(['settings_id', 'nombre', 'tutor', 'centro', 'created_at'], axis=1, inplace=True)
    # print(df_data)

    df_alumno = pd.read_sql_query(session_sql.query(Alumno).statement, engine)
    df_data = pd.merge(df_data, df_alumno, how='inner', on=None, left_on='grupo_id', right_on='grupo_id', left_index=False, right_index=False, sort=False, suffixes=('_grupo', '_alumno'), copy=False, indicator=False)
    df_data.rename(columns={'id': 'alumno_id'}, inplace=True)
    df_data.drop(['nombre', 'apellidos', 'created_at'], axis=1, inplace=True)
    # print(df_data)

    df_tutoria = pd.read_sql_query(session_sql.query(Tutoria).statement, engine)
    df_data = pd.merge(df_data, df_tutoria, how='inner', on=None, left_on='alumno_id', right_on='alumno_id', left_index=False, right_index=False, sort=False, suffixes=('_alumno', '_tutoria'), copy=False, indicator=False)
    df_data.rename(columns={'id': 'tutoria_id'}, inplace=True)
    df_data.drop(['fecha', 'hora', 'activa', 'deleted', 'created_at'], axis=1, inplace=True)
    # print(df_data)
    return df_data


def df_load_admin_informes():
    df_informe = pd.read_sql_query(session_sql.query(Informe).statement, engine)
    df_data = df_informe
    # print(df_data)
    return df_data


# ***********************************************************************


def data_count(df_data, columna):
    return df_data[columna].count()


def data_usuarios_count(df_data):
    return df_data.username.count()


def data_email_validated(df_data):
    usuarios_count = data_usuarios_count(df_load_admin_usuarios())
    columna_true_count = int(df_data[df_data.email_validated == True]['email_validated'].count())
    columna_true_percent = int((columna_true_count / usuarios_count * 100).round(decimals=0))
    columna_false_count = int(usuarios_count - columna_true_count)
    columna_false_percent = int(100 - columna_true_percent)
    return columna_true_count, columna_true_percent, columna_false_count, columna_false_percent


def data_email_robinson(df_data):
    usuarios_count = data_usuarios_count(df_load_admin_usuarios())
    columna_true_count = int(df_data[df_data.email_robinson == True]['email_robinson'].count())
    columna_true_percent = int((columna_true_count / usuarios_count * 100).round(decimals=0))
    columna_false_count = int(usuarios_count - columna_true_count)
    columna_false_percent = int(100 - columna_true_percent)
    return columna_true_count, columna_true_percent, columna_false_count, columna_false_percent


def data_tutoria_timeout(df_data):
    usuarios_count = data_usuarios_count(df_load_admin_usuarios())
    columna_true_count = int(df_data[df_data.tutoria_timeout == True]['tutoria_timeout'].count())
    columna_true_percent = int((columna_true_count / usuarios_count * 100).round(decimals=0))
    columna_false_count = int(usuarios_count - columna_true_count)
    columna_false_percent = int(100 - columna_true_percent)
    return columna_true_count, columna_true_percent, columna_false_count, columna_false_percent


def data_ban(df_data):
    usuarios_count = data_usuarios_count(df_load_admin_usuarios())
    columna_true_count = int(df_data[df_data.ban == True]['ban'].count())
    columna_true_percent = int((columna_true_count / usuarios_count * 100).round(decimals=0))
    columna_false_count = int(usuarios_count - columna_true_count)
    columna_false_percent = int(100 - columna_true_percent)
    return columna_true_count, columna_true_percent, columna_false_count, columna_false_percent


def data_usuarios_top_10(df_data):
    df_data = df_data.sort_values(['visit_number', 'visit_last', 'username'], ascending=False)[['username', 'visit_number', 'visit_last']]
    df_data = df_data.head(10)
    return df_data


def data_tutorias_media(df_data, columna):
    tutorias_media = 0
    tutorias_string = []
    grouped = df_data.groupby(columna, sort=True)
    for user, grupo in grouped:
        tutorias_string.append(grupo.tutoria_id.count())
        tutorias_number = map(int, tutorias_string)
    tutorias_media = round(mean(tutorias_number), 2)
    return tutorias_media


# ***********************************************************************
# XXX: pandas para usuarios
# -----------------------------------------------------------------------


def df_load():

    df_alumno = pd.read_sql_query(session_sql.query(Alumno).join(Grupo).filter(Grupo.id == settings().grupo_activo_id).statement, engine)
    df_alumno.drop(['grupo_id', 'created_at', 'nombre', 'apellidos'], axis=1, inplace=True)
    df_alumno.rename(columns={'id': 'alumno_id'}, inplace=True)
    # print(df_alumno)

    df_tutoria = pd.read_sql_query(session_sql.query(Tutoria).statement, engine)
    df_data = pd.merge(df_alumno, df_tutoria, how='inner', on=None, left_on='alumno_id', right_on='alumno_id', left_index=False, right_index=False, sort=False, suffixes=('_alumno', '_tutoria'), copy=False, indicator=False)
    df_data.drop(['hora', 'activa', 'created_at', 'deleted'], axis=1, inplace=True)
    df_data.rename(columns={'id': 'tutoria_id'}, inplace=True)
    # print(df_data)

    df_informe = pd.read_sql_query(session_sql.query(Informe).statement, engine)
    df_data = pd.merge(df_data, df_informe, how='inner', on=None, left_on='tutoria_id', right_on='tutoria_id', left_index=False, right_index=False, sort=False, suffixes=('_tutoria', '_informe'), copy=False, indicator=False)
    df_data.drop(['created_at', 'comentario'], axis=1, inplace=True)
    df_data.rename(columns={'id': 'informe_id'}, inplace=True)
    # print(df_data)

    df_asignatura = pd.read_sql_query(session_sql.query(Asignatura).join(Grupo).filter(Grupo.id == settings().grupo_activo_id).statement, engine)
    df_data = pd.merge(df_data, df_asignatura, how='inner', on=None, left_on='asignatura_id', right_on='id', left_index=False, right_index=False, sort=False, suffixes=('_informe', '_asignatura'), copy=False, indicator=False)
    df_data.drop(['id', 'email', 'created_at', 'nombre', 'apellidos'], axis=1, inplace=True)
    # df_data.rename(columns={'activa': 'tutoria_activa'}, inplace=True)
    # print(df_data)
    #
    df_respuesta = pd.read_sql_query(session_sql.query(Respuesta).statement, engine)
    df_data = pd.merge(df_data, df_respuesta, how='inner', on=None, left_on='informe_id', right_on='informe_id', left_index=False, right_index=False, sort=False, suffixes=('_informe', '_respuesta'), copy=False, indicator=False)
    df_data.drop(['id', 'created_at'], axis=1, inplace=True)
    df_data.rename(columns={'id': 'resultado_id', 'resultado': 'cuestionario_resultado'}, inplace=True)
    # print(df_data)
    #
    df_pregunta = pd.read_sql_query(session_sql.query(Pregunta).join(Association_Settings_Pregunta).join(Settings).filter(Settings.user_id == current_user.id).statement, engine)
    #
    df_data = pd.merge(df_data, df_pregunta, how='inner', on=None, left_on='pregunta_id', right_on='id', left_index=False, right_index=False, sort=False, suffixes=('_respuesta', '_pregunta'), copy=False, indicator=False)
    df_data.drop(['id', 'enunciado', 'created_at', 'visible', 'active_default'], axis=1, inplace=True)
    df_data.rename(columns={'enunciado_ticker': 'cuestionario_enunciado', 'orden': 'cuestionario_orden'}, inplace=True)
    # print(df_data)

    df_data = df_data
    df_data.cuestionario_resultado = df_data.cuestionario_resultado.astype(float)  # convierte a FLOAT los resultados que son INTEGER

    df_data.sort_values(by=['cuestionario_orden'], inplace=True)  # Para mantener el orden del cuestionario
    # print(df_data)
    return df_data
# ***********************************************************************


def arrow_fecha(texto):
    return arrow.get(texto, 'Spanish_Spain.1252')  # FIXME: supongo que habra que modificarlo para heroku


def df_evolucion_notas(alumno_id):
    tutorias_alumno = session_sql.query(Tutoria).filter(Tutoria.alumno_id == alumno_id).order_by(desc('fecha')).all()
    evolucion_notas_serie = []
    evolucion_notas = []
    for tutoria in tutorias_alumno:
        for informe in tutoria.informes:
            for prueba_evaluable in informe.pruebas_evaluables:
                evolucion_notas_serie.append(float(prueba_evaluable.nota))
        if evolucion_notas_serie:
            evolucion_notas.append([arrow.get(tutoria.fecha).timestamp * 1000, mean(evolucion_notas_serie)])
        evolucion_notas_serie = []
    return evolucion_notas


def df_evolucion(df_data, alumno_id):
    evolucion_grupo = []
    evolucion_alumno = []
    df_data_grupo_sin_alumno = df_data[df_data.alumno_id != alumno_id]
    grouped_grupo = df_data_grupo_sin_alumno.groupby('fecha', sort=True)
    for k, grupo in grouped_grupo:
        evolucion_grupo.append([arrow.get(k).timestamp * 1000, grupo.cuestionario_resultado.mean().round(decimals=2)])

    df_data_alumno = df_data[df_data.alumno_id == alumno_id]
    grouped_alumno = df_data_alumno.groupby('fecha', sort=True)
    for k, grupo in grouped_alumno:
        evolucion_alumno.append([arrow.get(k).timestamp * 1000, grupo.cuestionario_resultado.mean().round(decimals=2)])

    return evolucion_grupo, evolucion_alumno

# FIXME problema de float al encontrarse con datos vacios


def df_analisis_asignatura(df_data, tutoria_id, asignatura, alumno_id):
    prueba_evaluable_media = ''
    cuestionario_media = ''
    cuestionario_tutoria_media = ''
    cuestionario_asignatura_media = ''
    cuestionario_asignatura_tutoria_media = ''
    pruebas_evaluables_media = ''
    pruebas_evaluables_asignatura_media = ''

    # medias del grupo
    df_data_sin_alumno = df_data[df_data.alumno_id != alumno_id]
    if not df_data_sin_alumno.cuestionario_resultado.empty:
        cuestionario_media = df_data_sin_alumno.cuestionario_resultado.mean().round(decimals=2)

    df_data_asignatura = df_data_sin_alumno[df_data.asignatura == asignatura]
    if not df_data_asignatura.cuestionario_resultado.empty:
        cuestionario_asignatura_media = df_data_asignatura.cuestionario_resultado.mean().round(decimals=2)

    # medias del alumno
    df_data_tutoria = df_data[df_data.tutoria_id == tutoria_id]
    cuestionario_tutoria_media = df_data_tutoria.cuestionario_resultado.mean().round(decimals=2)

    df_data_tutoria_asignatura = df_data[(df_data.tutoria_id == tutoria_id) & (df_data.asignatura == asignatura)]
    cuestionario_asignatura_tutoria_media = df_data_tutoria_asignatura.cuestionario_resultado.mean().round(decimals=2)
    return cuestionario_media, cuestionario_tutoria_media, cuestionario_asignatura_media, cuestionario_asignatura_tutoria_media


def df_asignaturas_lista(df_data, tutoria_id):
    asignaturas_lista = []
    df_data_tutoria = df_data[df_data.tutoria_id == tutoria_id][['asignatura']]
    grouped_tutoria = df_data_tutoria.groupby('asignatura', sort=False)
    for k, grupo in grouped_tutoria:
        asignaturas_lista.append(k)
    return asignaturas_lista

# NOTE updated [OK] pero de momento esta sin usar


def df_asignaturas_dic(df_data, tutoria_id):
    asignaturas_dic = {}
    df_data_tutoria = df_data[df_data.tutoria_id == tutoria_id][['asignatura_id', 'asignatura']]
    grouped_tutoria = df_data_tutoria.groupby('asignatura_id', sort=False)
    for k, grupo in grouped_tutoria:
        asignaturas_dic[k] = grupo.asignatura[0]
    return asignaturas_dic


def df_asignatura_stacked(df_data, tutoria_id, cuestion):
    asignatura_spline_serie = []
    asignatura_stacked_serie = []
    notas_spline = []
    df_data_asignatura = df_data.loc[lambda df: (df.tutoria_id == tutoria_id) & (df.cuestionario_enunciado == cuestion)][['asignatura', 'cuestionario_enunciado', 'cuestionario_resultado']]
    for k in df_data_asignatura['cuestionario_resultado']:
        asignatura_spline_serie.append(k)  # genera el spline

    for k in df_data_asignatura['cuestionario_resultado'] / len(df_cuestiones_lista(df_data, tutoria_id)):
        asignatura_stacked_serie.append(k)  # genera el porcentage del stacked
    return asignatura_stacked_serie, asignatura_spline_serie, notas_spline


def df_asignatura_stacked_ORG(df_data, tutoria_id, cuestion):
    asignatura_spline_serie = []
    asignatura_stacked_serie = []
    df_data_asignatura = df_data.loc[lambda df: (df.tutoria_id == tutoria_id) & (df.cuestionario_enunciado == cuestion)][['asignatura', 'cuestionario_enunciado', 'cuestionario_resultado']]
    for k in df_data_asignatura['cuestionario_resultado']:
        asignatura_spline_serie.append(k)  # genera el spline

    for k in df_data_asignatura['cuestionario_resultado'] / len(df_cuestiones_lista(df_data, tutoria_id)):
        asignatura_stacked_serie.append(k)  # genera el porcentage del stacked
    return asignatura_stacked_serie, asignatura_spline_serie

# NOTE updated [OK]


def df_asignatura_grupo_spline(df_data, tutoria_id, alumno_id):
    asignatura_grupo_spline = []
    df_data_sin_alumno = df_data[df_data.alumno_id != alumno_id]
    grouped = df_data_sin_alumno.groupby('asignatura', sort=False)
    for k, grupo in grouped:
        if k in df_asignaturas_lista(df_data, tutoria_id):  # Para asegurar poner solo las categorias (asignaturas) de cada tutoria
            asignatura_grupo_spline.append(grupo.cuestionario_resultado.mean().round(decimals=2))
    return asignatura_grupo_spline


def df_cuestiones_lista(df_data, tutoria_id):
    cuestiones_lista = []
    df_data_tutoria = df_data.loc[lambda df: df.tutoria_id == tutoria_id][['cuestionario_enunciado']]
    grouped_tutoria = df_data_tutoria.groupby('cuestionario_enunciado', sort=False)

    for k, grupo in grouped_tutoria:
        cuestiones_lista.append(k)
    return cuestiones_lista


def df_cuestion_stacked(df_data, tutoria_id, asignatura):
    cuestion_spline_serie = []
    cuestion_stacked_serie = []
    df_data_asignatura = df_data.loc[lambda df: (df.tutoria_id == tutoria_id) & (df.asignatura == asignatura)][['asignatura', 'cuestionario_enunciado', 'cuestionario_resultado']]
    for k in df_data_asignatura['cuestionario_resultado']:
        cuestion_spline_serie.append(k)  # genera el spline

    # asignatura = df_data_asignatura.iloc[0]['asignatura'] // ejemplo para localizar datos en dataframe
    for k in df_data_asignatura['cuestionario_resultado'] / len(df_asignaturas_lista(df_data, tutoria_id)):
        cuestion_stacked_serie.append(k)  # genera el porcentage del stacked
    return cuestion_stacked_serie, cuestion_spline_serie

# NOTE media del grupo en highcharts_cuestionario

# NOTE updated [OK]


def df_cuestion_grupo_spline(df_data, tutoria_id, alumno_id):
    alumno_id = session_sql.query(Alumno).join(Tutoria).filter(Tutoria.id == tutoria_id).first().id  # para que el grupo sea ajeno a este alumno en la media
    cuestion_grupo_spline = []
    df_data_sin_alumno = df_data[df_data.alumno_id != alumno_id]
    grouped = df_data_sin_alumno.groupby('cuestionario_enunciado', sort=False)
    for k, grupo in grouped:
        if k in df_cuestiones_lista(df_data, tutoria_id):  # Para asegurar poner solo las categorias (asignaturas) de cada tutoria
            cuestion_grupo_spline.append(grupo.cuestionario_resultado.mean().round(decimals=2))
    return cuestion_grupo_spline


def df_analisis_asignatura_stacked(df_data, tutoria_id, asignatura):
    serie_temporal = []

    cuestionario_serie = []
    cuestionario_sin_alcanzar = ''
    cuestionario_asignatura_serie = []
    cuestionario_asignatura_sin_alcanzar = ''
    cuestionario_serie_tutoria = []
    cuestionario_sin_alcanzar_tutoria = ''
    cuestionario_asignatura_serie_tutoria = []
    cuestionario_asignatura_sin_alcanzar_tutoria = ''

    # cuestionario_serie
    grouped_cuestionario = df_data.groupby('cuestionario_enunciado', sort=False)
    for k, grupo in grouped_cuestionario:
        cuestionario_serie.append([k, grupo.cuestionario_resultado.mean().round(decimals=2)])
        serie_temporal.append(10 - grupo.cuestionario_resultado.mean().round(decimals=2))
    cuestionario_sin_alcanzar = sum(serie_temporal)

    # cuestionario_serie_tutoria
    df_data_tutoria = df_data.loc[lambda df: df.tutoria_id == tutoria_id][['cuestionario_enunciado', 'cuestionario_resultado']]
    grouped_cuestionario = df_data_tutoria.groupby('cuestionario_enunciado', sort=False)
    serie_temporal = []
    for k, grupo in grouped_cuestionario:
        cuestionario_serie_tutoria.append([k, grupo.cuestionario_resultado.mean().round(decimals=2)])
        serie_temporal.append(10 - grupo.cuestionario_resultado.mean().round(decimals=2))
    cuestionario_sin_alcanzar_tutoria = sum(serie_temporal)

    # cuestionario_serie_asignatura
    df_data_asignatura = df_data.loc[lambda df: (df.asignatura == asignatura)][['cuestionario_enunciado', 'cuestionario_resultado']]
    grouped_cuestionario_asignatura = df_data_asignatura.groupby('cuestionario_enunciado', sort=False)
    serie_temporal = []
    for k, grupo in grouped_cuestionario_asignatura:
        cuestionario_asignatura_serie.append([k, grupo.cuestionario_resultado.mean().round(decimals=2)])
        serie_temporal.append(10 - grupo.cuestionario_resultado.mean().round(decimals=2))
    cuestionario_asignatura_sin_alcanzar = sum(serie_temporal)

    # cuestionario_serie_asignatura_tutoria
    df_data_asignatura_tutoria = df_data.loc[lambda df: (df.tutoria_id == tutoria_id) & (df.asignatura == asignatura)][['cuestionario_enunciado', 'cuestionario_resultado']]
    grouped_cuestionario_asignatura = df_data_asignatura_tutoria.groupby('cuestionario_enunciado', sort=False)
    serie_temporal = []
    for k, grupo in grouped_cuestionario_asignatura:
        cuestionario_asignatura_serie_tutoria.append([k, grupo.cuestionario_resultado.mean().round(decimals=2)])
        serie_temporal.append(10 - grupo.cuestionario_resultado.mean().round(decimals=2))
    cuestionario_asignatura_sin_alcanzar_tutoria = sum(serie_temporal)

    return cuestionario_serie, cuestionario_serie_tutoria, cuestionario_sin_alcanzar, cuestionario_sin_alcanzar_tutoria, cuestionario_asignatura_serie, cuestionario_asignatura_serie_tutoria, cuestionario_asignatura_sin_alcanzar, cuestionario_asignatura_sin_alcanzar_tutoria

    # *****************************************************************

# Funciones para usuario anonimos para rellenar el formulario.
# -------------------------------------------------------------------------------------------


def invitado_settings(tutoria_id):  # (Settings) by tutoria_id
    invitado_settings = session_sql.query(Settings).join(Grupo).join(Alumno).join(Tutoria).filter(Tutoria.id == tutoria_id).first()
    return invitado_settings


def invitado_grupo(tutoria_id):  # (Grupo) by tutoria_id
    invitado_grupo = session_sql.query(Grupo).join(Alumno).filter(Tutoria.id == tutoria_id).first()
    return invitado_grupo


def invitado_preguntas(settings_id):  # [Preguntas] by settings_id
    invitado_preguntas = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings_id).order_by('orden').all()
    return invitado_preguntas


def invitado_settings_by_id(settings_id):  # (Settings) by settings_id
    invitado_settings_by_id = session_sql.query(Settings).filter(Settings.user_id == settings_id).first()
    return invitado_settings_by_id


def invitado_alumno(tutoria_id):  # (Alumno) by tutoria_id
    invitado_alumno = session_sql.query(Alumno).join(Tutoria).filter(Tutoria.id == tutoria_id).first()
    return invitado_alumno


def invitado_informe(tutoria_id, asignatura_id):  # (informe) actual
    invitado_informe = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id, Informe.asignatura_id == asignatura_id).first()
    return invitado_informe


def invitado_respuesta(informe_id, pregunta_id):  # (Respuesta) by informe_id y pregunta_id
    invitado_respuesta = session_sql.query(Respuesta).filter(Respuesta.informe_id == informe_id, Respuesta.pregunta_id == pregunta_id).first()
    return invitado_respuesta


def invitado_pruebas_evaluables(informe_id):  # [pruebas_evaluables] by informe_id
    invitado_pruebas_evaluables = session_sql.query(Prueba_Evaluable).filter(Prueba_Evaluable.informe_id == informe_id).order_by('id').all()
    return invitado_pruebas_evaluables


# ********************************************************************************************


def informe_by_id(informe_id):
    informe_by_id = session_sql.query(Informe).filter(Informe.id == informe_id).first()
    return informe_by_id


def respuesta_by_id(respuesta_id):
    respuesta_by_id = session_sql.query(Respuesta).filter(Respuesta.id == respuesta_id).first()
    return respuesta_by_id


def tutoria_asignaturas_count(tutoria_id):  # {total de asignaturas de una tutoria}
    tutoria_asignaturas_count = 0
    if tutoria_id:
        tutoria_asignaturas_count = session_sql.query(Association_Tutoria_Asignatura).filter_by(tutoria_id=tutoria_id).count()
    return tutoria_asignaturas_count


def tutoria_asignaturas(tutoria_id, order_by_1):  # [Asignaturas] de una tutoria
    tutoria_asignaturas = None
    if tutoria_id:
        if order_by_1:
            tutoria_asignaturas = session_sql.query(Asignatura).join(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria_id).order_by(order_by_1).all()
        else:
            tutoria_asignaturas = session_sql.query(Asignatura).join(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria_id).all()
    return tutoria_asignaturas


def cociente_porcentual(a, b):
    if b != 0:
        cociente_porcentual = int((a / b) * 100)
    else:
        cociente_porcentual = 0
    return cociente_porcentual


def tutoria_informes(tutoria_id):  # [informes] de una tutoria
    tutoria_informes = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id).all()
    return tutoria_informes


def preguntas(visible):  # [Preguntas] disponibles para un cuestionario.
    if visible:
        preguntas = session_sql.query(Pregunta).filter(Pregunta.visible == visible).order_by('orden').all()
    else:
        preguntas = session_sql.query(Pregunta).order_by('orden').all()
    return preguntas


def pregunta_by_id(pregunta_id, visible):
    if visible:
        pregunta_by_id = session_sql.query(Pregunta).filter(Pregunta.id == pregunta_id, Pregunta.visible == visible).first()
    else:
        pregunta_by_id = session_sql.query(Pregunta).filter(Pregunta.id == pregunta_id).first()
    return pregunta_by_id


def informe_preguntas():
    informe_preguntas = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings().id).all()
    return informe_preguntas


def grupo_informes(grupo_id):
    grupo_informes = session_sql.query(Informe).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings().id).all()


def grupos():
    grupos = session_sql.query(Grupo).filter(Grupo.settings_id == settings().id).order_by(desc('curso_academico'), 'nombre').all()
    return grupos


def curso():
    if 8 <= datetime.date.today().month <= 12:
        curso = datetime.date.today().year
    else:
        curso = datetime.date.today().year - 1
    curso = int(curso)
    return curso


def alumno_grupo(alumno_id):  # (Grupo) de un alumno
    alumno_grupo = None
    if alumno_id:
        alumno_grupo = session_sql.query(Grupo).join('alumnos').filter(Alumno.id == alumno_id).first()
    return alumno_grupo


def string_to_date(texto):
    if texto:  # {Fecha} Convierte string a fecha para ser usado dentro de un formulario
        date_obj = datetime.datetime.strptime(texto, '%Y-%m-%d')
    else:
        date_obj = datetime.date.today()
    return date_obj


def string_to_time(texto):
    if texto:  # {Fecha} Convierte string a fecha para ser usado dentro de un formulario
        date_obj = datetime.datetime.strptime(texto, '%H:%M')
    else:
        date_obj = datetime.date.today()
    return date_obj


def tutoria_by_id(tutoria_id):
    if tutoria_id != None:
        tutoria_by_id = session_sql.query(Tutoria).filter(Tutoria.id == tutoria_id).first()
    else:
        tutoria_by_id = None
    return tutoria_by_id


def alumno_by_id(alumno_id):
    if alumno_id != None:
        alumno_by_id = session_sql.query(Alumno).filter(Alumno.id == alumno_id).first()
    else:
        alumno_by_id = None
    return alumno_by_id


def asignatura_by_id(asignatura_id):
    if asignatura_id != None:
        asignatura_by_id = session_sql.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    else:
        asignatura_by_id = None
    return asignatura_by_id


def association_tutoria_asignatura_check(tutoria_id, asignatura_id):  # {Boolean} comprueba si una tutoria y asignatura estan vinculados
    check = session_sql.query(Association_Tutoria_Asignatura).filter_by(tutoria_id=tutoria_id, asignatura_id=asignatura_id).first()
    if check:
        return True
    else:
        return False


def flash_toast(message, type):
    flash(Markup('<script>toastr["') + type + Markup('"]("') + message + Markup('");</script>'), type)


def flash_wtforms(form, flash_type, category_filter):
    for field, errors in form.errors.items():
        for error in errors:
            flash_type(error, category_filter)


def truncate_custom(string, length):
    return string[:length].format(string, length)


def equal_str(a, b):
    if a != None and b != None:
        if str(a) == str(b):
            return True
    return False


def tutorias_timeout():  # Update de TRUE a FALSE la columna activa de una tutoria pasadas 48 horas
    if settings().tutoria_timeout:
        alumnos = session_sql.query(Alumno).filter(Alumno.grupo_id == settings().grupo_activo_id).all()
        for alumno in alumnos:
            for tutoria in alumno_tutorias(alumno.id, True):
                if tutoria.fecha < g.current_date - datetime.timedelta(hours=6):
                    tutoria.activa = False
                    session_sql.commit()
                    flash_toast('Tutoria de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' para el dia ' + Markup('<strong>') + str(tutoria.fecha) + Markup('</strong>') + ' auto-archivada', 'warning')


def grupo_tutorias(grupo_id, activa):
    if str(activa) == '':
        grupo_tutorias = session_sql.query(Tutoria).join(Alumno).join(Grupo).filter(Grupo.id == grupo_id).order_by('fecha').all()
    else:
        grupo_tutorias = session_sql.query(Tutoria).join(Alumno).join(Grupo).filter(Grupo.id == grupo_id).filter(Tutoria.activa == activa).order_by('fecha').all()
    return grupo_tutorias


def alumno_asignaturas_id(alumno_id):  # (asignaturas_id) de un alumno
    alumno_asignaturas_id = session_sql.query(Association_Alumno_Asignatura).filter_by(alumno_id=alumno_id).all()
    return alumno_asignaturas_id


def alumno_asignaturas(alumno_id):  # (asignaturas) de un alumno
    alumno_asignaturas = session_sql.query(Asignatura).join(Association_Alumno_Asignatura).filter(Association_Alumno_Asignatura.alumno_id == alumno_id).all()
    return alumno_asignaturas


def grupo_alumnos_count(grupo_id):  # {alumnos_count} de un grupo
    return session_sql.query(Alumno).join(Grupo).filter(Grupo.id == grupo_id).count()


def asignaturas(order_by_1, order_by_2, order_by_3):  # [asignaturas] sorted de un grupo
    asignaturas = session_sql.query(Asignatura).filter_by(grupo_id=settings().grupo_activo_id).order_by(order_by_1, order_by_2, order_by_3).all()
    return asignaturas


def asignaturas_not_sorted():  # [asignaturas] not sorted  de un grupo
    asignaturas_not_sorted = session_sql.query(Asignatura).filter_by(grupo_id=settings().grupo_activo_id).order_by('id').all()
    return asignaturas_not_sorted


def alumnos_not_sorted():  # [alumnos] NO ordeandos de un grupo
    alumnos_not_sorted = session_sql.query(Alumno).filter_by(grupo_id=settings().grupo_activo_id).order_by('id').all()
    return alumnos_not_sorted


def alumnos(order_by_1, order_by_2):  # [alumnos] ordeandos de un grupo_activo
    alumnos = session_sql.query(Alumno).filter(Alumno.grupo_id == settings().grupo_activo_id).order_by(str(order_by_1), str(order_by_2)).all()
    return alumnos


def association_alumno_asignatura_check(alumno_id, asignatura_id):  # {Boolean} comprueba si alumno y asignatura estan vinculados
    check = session_sql.query(Association_Alumno_Asignatura).filter_by(alumno_id=alumno_id, asignatura_id=asignatura_id).first()
    if check:
        return True
    else:
        return False


def association_settings_pregunta_check(settings_id, pregunta_id):  # {Boolean} comprueba si alumno y asignatura estan vinculados
    check = session_sql.query(Association_Settings_Pregunta).filter_by(settings_id=settings_id, pregunta_id=pregunta_id).first()
    if check:
        return True
    else:
        return False


def asignatura_alumnos(asignatura_id):  # [Alumnos] de un asignatura ordenado por 'apellidos' y 'nombre' (usando join)
    asignatura_alumnos = session_sql.query(Alumno).join((Asignatura, Alumno.asignaturas)).filter(Asignatura.id == asignatura_id).order_by('apellidos', 'nombre').all()
    return asignatura_alumnos


def alumno_tutorias(alumno_id, activa):  # [Tutorias] de un alumno.
    alumno_tutorias = None
    if alumno_id:
        if str(activa):
            tutorias_de_alumno = session_sql.query(Tutoria).filter_by(alumno_id=alumno_id, activa=activa).order_by(desc('fecha')).all()
        else:
            tutorias_de_alumno = session_sql.query(Tutoria).filter_by(alumno_id=alumno_id).order_by(desc('fecha')).all()
    return tutorias_de_alumno


def singular_plural(singular, plural, lista):  # {texto} singular o plural usando una lista o entero
    if singular != None and plural != None:
        texto = plural
        if lista != None:
            if type(lista) is int:
                longitud = lista
            else:
                longitud = len(lista)
            if longitud == 1:
                texto = singular
    else:
        texto = 'singular o plural vacio'
    return texto


def cita_random():
    cita_random = session_sql.query(Cita).order_by(func.random()).first()
    return cita_random


app.jinja_env.globals.update(settings=settings, cita_random=cita_random,  singular_plural=singular_plural, grupo_activo=grupo_activo, curso=curso, alumnos_not_sorted=alumnos_not_sorted, alumnos=alumnos, alumno_tutorias=alumno_tutorias, equal_str=equal_str, alumno_asignaturas_id=alumno_asignaturas_id, asignaturas=asignaturas, asignatura_alumnos=asignatura_alumnos, association_alumno_asignatura_check=association_alumno_asignatura_check,
                             tutoria_asignaturas_count=tutoria_asignaturas_count, string_to_date=string_to_date, association_settings_pregunta_check=association_settings_pregunta_check, preguntas=preguntas, informe_preguntas=informe_preguntas, invitado_settings=invitado_settings, invitado_preguntas=invitado_preguntas, invitado_settings_by_id=invitado_settings_by_id, invitado_respuesta=invitado_respuesta, invitado_pruebas_evaluables=invitado_pruebas_evaluables, invitado_informe=invitado_informe, tutoria_informes=tutoria_informes, cociente_porcentual=cociente_porcentual, tutoria_asignaturas=tutoria_asignaturas, df_analisis_asignatura_stacked=df_analisis_asignatura_stacked, df_cuestion_stacked=df_cuestion_stacked, df_asignaturas_lista=df_asignaturas_lista, df_cuestiones_lista=df_cuestiones_lista, df_cuestion_grupo_spline=df_cuestion_grupo_spline, df_asignatura_stacked=df_asignatura_stacked, df_asignatura_grupo_spline=df_asignatura_grupo_spline, df_analisis_asignatura=df_analisis_asignatura, asignatura_comentario=asignatura_comentario, pregunta_active_default_check=pregunta_active_default_check, notas_asignatura=notas_asignatura, notas_asignatura_grupo=notas_asignatura_grupo, pregunta_visible_check=pregunta_visible_check, grupo_activo_check=grupo_activo_check, user_by_id=user_by_id, df_evolucion=df_evolucion, df_evolucion_notas=df_evolucion_notas, tutoria_stats=tutoria_stats, arrow_fecha=arrow_fecha, asignatura_informes_count=asignatura_informes_count, asignatura_informes_respondidos_count=asignatura_informes_respondidos_count, alumno_asignaturas=alumno_asignaturas, asignaturas_not_sorted=asignaturas_not_sorted, grupo_tutorias=grupo_tutorias, alumno_by_id=alumno_by_id, hashids_encode=hashids_encode, hashids_decode=hashids_decode, f_encode=f_encode, f_decode=f_decode, dic_encode_args=dic_encode_args, dic_try=dic_try, settings_by_id=settings_by_id, usuario_grupos=usuario_grupos, grupo_alumnos_count=grupo_alumnos_count, usuarios=usuarios, usuario_cuestionario=usuario_cuestionario, data_count=data_count, df_asignaturas_dic=df_asignaturas_dic, data_usuarios_count=data_usuarios_count, data_email_validated=data_email_validated, data_email_robinson=data_email_robinson, data_tutoria_timeout=data_tutoria_timeout, data_ban=data_ban, data_usuarios_top_10=data_usuarios_top_10, data_tutorias_media=data_tutorias_media)
