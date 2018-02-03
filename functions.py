from app import app
from config_parametros import *
import config_parametros
import logging
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


# NOTE
# [] Lista
# () Objeto
# {} Valor

# ***************************************************************
# Mantenimiento nocturno
# ***************************************************************

def mantenimiento_historial():
    # XXX mover tutorias al historial
    tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == False, Tutoria.activa == True, Tutoria.fecha < g.current_date)
    for tutoria in tutorias:
        tutoria.activa = False
    session_sql.commit()


def mantenimiento_papelera():
    # XXX purgar papelera tutorias
    tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == True, Tutoria.deleted_at < g.current_date - datetime.timedelta(days=g.settings_global.periodo_deleted_tutorias)).all()
    for tutoria in tutorias:
        session_sql.delete(tutoria)
    session_sql.commit()


def mantenimiento_re_send_email():
    # XXX re_send_email last 24h
    settings_global_sql = session_sql.query(Settings_Global).first()
    sender = settings_global_sql.gmail_sender
    current_date = datetime.date.today()

    # XXX crea el servicio gmail
    try:
        oauth2_credentials = settings_global_sql.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
    except:
        print('Error al generar servicio de Gmail')

    # XXX re-send email 24 antes de la tutoria.fecha
    tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == False, Tutoria.activa == True, Tutoria.fecha == current_date + datetime.timedelta(days=1), Tutoria.created_at != current_date).all()

    for tutoria in tutorias:
        settings_current_user_sql = session_sql.query(Settings).join(Grupo).join(Alumno).join(Tutoria).filter(Tutoria.id == tutoria.id).first()
        emails_enviados = settings_current_user_sql.emails_enviados
        asignaturas_id_lista = []
        asignaturas_de_la_tutoria = session_sql.query(Asignatura).join(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria.id).all()
        for asignatura in asignaturas_de_la_tutoria:
            informe = session_sql.query(Informe).filter_by(tutoria_id=tutoria.id, asignatura_id=asignatura.id).all()
            if not informe:
                asignaturas_id_lista.append(asignatura.id)
        if asignaturas_id_lista:
            alumno = session_sql.query(Alumno).join(Tutoria).filter(Tutoria.id == tutoria.id).first()
            try:
                for asignatura_id in asignaturas_id_lista:
                    asignatura = session_sql.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
                    association_tutoria_asignatura_sql = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria.id, Association_Tutoria_Asignatura.asignatura_id == asignatura_id).first()
                    if association_tutoria_asignatura_sql:
                        association_tutoria_asignatura_sql.created_at = datetime.datetime.today()
                        email_reenvio_number = association_tutoria_asignatura_sql.email_reenvio_number
                    else:
                        tutoria_asignatura_add = Association_Tutoria_Asignatura(tutoria_id=tutoria.id, asignatura_id=asignatura_id)
                        session_sql.add(tutoria_asignatura_add)
                        session_sql.flush()
                        association_tutoria_asignatura_sql = tutoria_asignatura_add
                        email_reenvio_number = association_tutoria_asignatura_sql.email_reenvio_number
                    # XXX envio de mail
                    # ****************************************
                    to = asignatura.email
                    tutoria_dia_semana = translate_fecha(tutoria.fecha.strftime('%A'))
                    tutoria_dia_mes = tutoria.fecha.strftime('%d')
                    emails_enviados = emails_enviados + 1
                    email_reenvio_number = email_reenvio_number + 1
                    association_tutoria_asignatura_sql.email_reenvio_number = email_reenvio_number
                    grupo_activo_sql = session_sql.query(Grupo).join('alumnos').filter(Alumno.id == alumno.id).first()
                    subject = 'Tutoría | %s | %s |  %s %s [24h-%s]' % (grupo_activo_sql.nombre, alumno.nombre, tutoria_dia_semana, tutoria_dia_mes, email_reenvio_number)
                    message_text = render_template('email_tutoria.html', grupo=grupo_activo_sql, tutoria=tutoria, alumno=alumno, asignatura=asignatura, tutoria_email_link=tutoria_email_link, index_link=index_link)
                    create_message_and_send(service, sender, to, subject, message_text)
                settings_current_user_sql.emails_enviados = emails_enviados
            except:
                print('Error al enviar emails')
    session_sql.commit()
    # print('Mantenimiento Re-Send satisfactorio.')  # NOTE en aws lambda no funciona el print en su lugar usar return


def mantenimiento_re_send_email_asincrono():
    @copy_current_request_context
    def mantenimiento_re_send_email_process():
        mantenimiento_re_send_email()
    mantenimiento_re_send_email_threading = threading.Thread(name='mantenimiento_re_send_email_thread', target=mantenimiento_re_send_email_process)
    mantenimiento_re_send_email_threading.start()
# ----------------------------------------------------------------
# Mantenimiento nocturno [FIN]
# ----------------------------------------------------------------


def abort_asincrono(error_number):
    if error_number == 500:
        flash_toast('Notficiando error', 'info')
        # XXX notificar error por email
        settings_global_sql = session_sql.query(Settings_Global).first()
        settings_current_user_sql = settings()
        oauth2_credentials = settings_global_sql.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        sender = settings_global_sql.gmail_sender
        to = settings_global_sql.gmail_sender
        params = {}
        usuario = user_by_id(settings_current_user_sql.id)
        params['fecha'] = datetime.date.today()
        params['hora'] = datetime.datetime.now().strftime('%H:%M')
        params['index_link'] = index_link
        subject = 'INTERNAL SERVER ERROR | %s [%sh]' % (params['fecha'], params['hora'])
        message_text = render_template('email_internal_server_error.html', usuario=usuario, params=params)
        create_message_and_send(service, sender, to, subject, message_text)
    pass


def email_reenvio_number(tutoria_id, asignatura_id):
    tutoria_asignatura = session_sql.query(Association_Tutoria_Asignatura).filter_by(tutoria_id=tutoria_id, asignatura_id=asignatura_id).first()
    if tutoria_asignatura:
        return tutoria_asignatura.email_reenvio_number
    else:
        return 0


def translate_fecha(fecha):
    dic = {'Jan': 'Ene', 'Jan': 'Feb', 'Mar': 'Mar', 'Apr': 'Abr', 'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago', 'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dic',
           'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'}
    for i, j in dic.items():
        fecha = fecha.replace(i, j)
    return fecha


def replace_string_by_dic(texto, dic):
    for i, j in dic.items():
        texto = texto.replace(i, j)
    return texto

# Calendar API
# *****************************************************************


def get_service_calendar():  # Ejemplo de codigo para crear el servicio calendar
    try:
        oauth2_credentials = g.settings_current_user.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
    except:
        return redirect(url_for('oauth2callback_calendar'))
    return service
# Fin Caldenar API
# *****************************************************************


# Gmail API
# *****************************************************************

def get_service_gmail():  # Ejemplo de codigo para crear el servicio gmail
    try:
        settings_global_sql = session_sql.query(Settings_Global).first()
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
    except:
        return redirect(url_for('oauth2callback_gmail'))
    return service


def create_message(sender, to, subject, message_text):
    # Create message container
    message = MIMEText(message_text, 'html')
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes())
    raw_message = raw_message.decode()
    body = {'raw': raw_message}
    return body


def send_message(service, user_id, body, message_text):
    try:
        message_sent = (service.users().messages().send(userId=user_id, body=body).execute())
    except:
        pass


def create_message_and_send(service, sender, to, subject, message_text):
    message = create_message(sender, to, subject, message_text)
    send_message(service, "me", message, message_text)

# XXX Gmail API [FIN]
# -----------------------------------------------------------------------------


def association_tutoria_asignatura_id(tutoria_id, asignatura_id):
    return session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.asignatura_id == asignatura_id, Association_Tutoria_Asignatura.tutoria_id == tutoria_id).first().id


def grupo_by_asignatura_id(asignatura_id):
    return session_sql.query(Grupo).join(Asignatura).filter(Asignatura.id == asignatura_id).first()


def tutoria_stats(tutoria_id):
    informes_recibidos_by_tutoria_id_count = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id).count()
    tutoria_asignaturas_count = session_sql.query(Association_Tutoria_Asignatura).filter_by(tutoria_id=tutoria_id).count()
    return informes_recibidos_by_tutoria_id_count, tutoria_asignaturas_count


def asignaturas_ordenadas(status):
    asignaturas_porcentaje_lista = []
    asignaturas_lista = asignaturas('asignatura', 'apellidos', 'nombre')
    if status != True:
        for asignatura in asignaturas_lista:
            profesor_porcentaje = cociente_porcentual(asignatura_informes_respondidos_count(asignatura.id), asignatura_informes_solicitados_count(asignatura.id))
            asignaturas_porcentaje_lista.append([profesor_porcentaje, asignatura])

        asignaturas_lista = sorted(asignaturas_porcentaje_lista, key=itemgetter(0), reverse=True)
        asignaturas_porcentaje_lista = []
        for asignatura_lista in asignaturas_lista:
            asignaturas_porcentaje_lista.append(asignatura_lista[1])
        asignaturas_lista = asignaturas_porcentaje_lista

    return asignaturas_lista


def asignaturas_orden_switch(status):
    if status == True:
        orden = 'asignaturas'
    else:
        orden = 'participacion'
    return orden


# ***********************************************************************
# XXX: tutoria stats (SIN PANDA)
# ***********************************************************************


def analisis_tutoria(tutoria_id):
    stats = {}
    alumno = alumno_by_tutoria_id(tutoria_id)
    grupo = grupo_by_tutoria_id(tutoria_id)

    asignaturas_alumno_lista = []
    for asignatura in alumno.asignaturas.order_by('asignatura', 'apellidos', 'nombre'):
        asignaturas_alumno_lista.append(asignatura)
    stats['asignaturas_alumno_lista'] = asignaturas_alumno_lista

    asignaturas_grupo_lista = []
    for asignatura in grupo.asignaturas.order_by('asignatura', 'apellidos', 'nombre'):
        asignaturas_grupo_lista.append(asignatura)
    stats['asignaturas_grupo_lista'] = asignaturas_grupo_lista

    asignaturas_solicitadas_horario_lista = []
    asignaturas_solicitas_horario_asignatura_lista = []
    stats['asignaturas_solicitadas'] = session_sql.query(Asignatura).join(Association_Tutoria_Asignatura).filter(Tutoria.id == tutoria_id).order_by('asignatura').all()
    for asignatura in alumno.asignaturas.order_by('asignatura'):
        if asignatura in stats['asignaturas_solicitadas']:
            asignaturas_solicitadas_horario_lista.append(asignatura)
            asignaturas_solicitas_horario_asignatura_lista.append(asignatura.asignatura)
    stats['asignaturas_solicitadas_horario_lista'] = asignaturas_solicitadas_horario_lista
    stats['asignaturas_solicitas_horario_asignatura_lista'] = asignaturas_solicitas_horario_asignatura_lista

    asignaturas_recibidas_lista = []
    asignaturas_recibidas_lista_asignatura = []
    for asignatura in stats['asignaturas_solicitadas_horario_lista']:
        informe = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id, Informe.asignatura_id == asignatura.id).first()
        if informe and asignatura not in asignaturas_recibidas_lista:
            asignaturas_recibidas_lista.append(asignatura)
            asignaturas_recibidas_lista_asignatura.append(asignatura.asignatura)
    stats['asignaturas_recibidas_lista'] = asignaturas_recibidas_lista
    stats['asignaturas_recibidas_lista_asignatura'] = asignaturas_recibidas_lista_asignatura

    preguntas_con_respuesta_lista = []
    preguntas_con_respuesta_lista_enunciado_ticker = []
    label_color_dic = {}
    column_color = []
    stats['categorias_pregunta'] = session_sql.query(Categoria).order_by('orden').all()
    stats['preguntas_settings'] = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == g.settings_current_user.id).order_by('orden').all()
    for categoria in stats['categorias_pregunta']:
        for pregunta in categoria.preguntas.order_by('orden'):
            if pregunta in stats['preguntas_settings']:
                informes = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id).all()
                for informe in informes:
                    respuesta = session_sql.query(Respuesta).filter(Respuesta.pregunta_id == pregunta.id, Respuesta.informe_id == informe.id).first()
                    if respuesta and pregunta not in preguntas_con_respuesta_lista:
                        preguntas_con_respuesta_lista.append(pregunta)
                        preguntas_con_respuesta_lista_enunciado_ticker.append(pregunta.enunciado_ticker)
                        column_color.append(categoria.color)
                        label_color_dic[pregunta.enunciado_ticker] = categoria.color

    stats['preguntas_con_respuesta_lista'] = preguntas_con_respuesta_lista
    stats['preguntas_con_respuesta_lista_enunciado_ticker'] = preguntas_con_respuesta_lista_enunciado_ticker
    stats['column_color'] = column_color
    stats['label_color_dic'] = json.dumps(json.dumps(label_color_dic))
    return stats


def tutoria_comentarios(tutoria_id, asignaturas_lista):
    stats = {}
    for asignatura in asignaturas_lista:
        informe = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id, Informe.asignatura_id == asignatura.id).first()
        if informe.comentario or informe.comentario_editado:
            stats[asignatura.asignatura] = {'docente': asignatura.nombre, 'comentario': informe.comentario, 'comentario_editado': informe.comentario_editado}
    return stats


def tutoria_incoming(tutoria_id):
    stats = {}
    alumno = alumno_by_tutoria_id(tutoria_id)
    asignaturas_horario = alumno.asignaturas.order_by('asignatura')
    asignaturas_solicitadas = session_sql.query(Asignatura).join(Association_Tutoria_Asignatura).filter(Tutoria.id == tutoria_id).order_by('asignatura').all()

    asignaturas_solicitadas_horario_lista = []
    asignaturas_solicitas_horario_asignatura_lista = []
    for asignatura in asignaturas_horario:
        if asignatura in asignaturas_solicitadas:
            asignaturas_solicitadas_horario_lista.append(asignatura)
    stats['asignaturas_solicitadas_horario_lista_count'] = len(asignaturas_solicitadas_horario_lista)

    asignaturas_recibidas_lista = []
    for asignatura in asignaturas_solicitadas_horario_lista:
        informe = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id, Informe.asignatura_id == asignatura.id).first()
        if informe and asignatura not in asignaturas_recibidas_lista:
            asignaturas_recibidas_lista.append(asignatura)
    stats['asignaturas_recibidas_lista_count'] = len(asignaturas_recibidas_lista)

    stats['porcentaje'] = cociente_porcentual(stats['asignaturas_recibidas_lista_count'], stats['asignaturas_solicitadas_horario_lista_count'])

    return stats


def respuestas_pregunta_alumno_lista(tutoria_id, asignatura_id, asignaturas_lista, preguntas_lista):
    respuestas_pregunta_spline = []
    respuestas_pregunta_stacked = []
    respuestas_pregunta_media = 'sin_notas'
    stats = {}

    for pregunta in preguntas_lista:
        respuestas = session_sql.query(Respuesta).join(Informe).join(Tutoria).filter(Respuesta.pregunta_id == pregunta.id, Informe.asignatura_id == asignatura_id, Informe.tutoria_id == tutoria_id, Tutoria.deleted == False).all()
        for respuesta in respuestas:
            if respuesta:
                resultado = respuesta.resultado
                if int(respuesta.resultado) == 0:
                    resultado = 1
                respuestas_pregunta_spline.append(int(resultado))
                respuestas_pregunta_stacked.append(int(resultado) / len(asignaturas_lista))

    if respuestas_pregunta_spline:
        respuestas_pregunta_media = round(mean(respuestas_pregunta_spline), 1)

    stats['respuestas_pregunta_lista'] = respuestas_pregunta_spline
    stats['respuestas_pregunta_stacked'] = respuestas_pregunta_stacked
    stats['respuestas_pregunta_media'] = respuestas_pregunta_media
    return stats


def respuestas_asignatura_alumno_lista(tutoria_id, pregunta_id, asignaturas_lista, preguntas_lista):
    respuestas_asignatura_spline = []
    respuestas_asignatura_stacked = []
    respuestas_asignatura_media = 'sin_notas'
    stats = {}

    for asignatura in asignaturas_lista:
        respuestas = session_sql.query(Respuesta).join(Informe).join(Tutoria).filter(Respuesta.pregunta_id == pregunta_id, Informe.asignatura_id == asignatura.id, Informe.tutoria_id == tutoria_id, Tutoria.deleted == False).all()
        for respuesta in respuestas:
            if respuesta:
                resultado = respuesta.resultado
                if int(respuesta.resultado) == 0:
                    resultado = 1
                respuestas_asignatura_spline.append(int(resultado))
                respuestas_asignatura_stacked.append(int(resultado) / len(preguntas_lista))
        if respuestas_asignatura_spline:
            respuestas_asignatura_media = round(mean(respuestas_asignatura_spline), 1)
    stats['respuestas_asignatura_lista'] = respuestas_asignatura_spline
    stats['respuestas_asignatura_stacked'] = respuestas_asignatura_stacked
    stats['respuestas_asignatura_media'] = respuestas_asignatura_media

    return stats


def respuestas_grupo_stats(tutoria_id, preguntas_lista, asignaturas_lista):
    respuestas_pregunta_grupo_spline = []
    respuestas_pregunta_grupo_spline_without_NaN = []
    respuestas_asignatura_grupo_spline = []
    respuestas_asignatura_grupo_spline_without_NaN = []
    pruebas_evaluables_lista = []
    respuestas_pregunta_grupo_media = 'sin_notas'
    respuestas_asignatura_grupo_media = 'sin_notas'
    alumno = alumno_by_tutoria_id(tutoria_id)
    grupo = grupo_by_tutoria_id(tutoria_id)
    preguntas = preguntas_lista
    asignaturas = asignaturas_lista
    pruebas_evaluables = session_sql.query(Prueba_Evaluable).join(Informe).join(Tutoria).filter(Tutoria.id == tutoria_id).all()
    stats = {}

    for pregunta in preguntas:
        respuestas_pregunta_lista = []
        for asignatura in asignaturas:
            respuestas = session_sql.query(Respuesta).join(Informe).join(Tutoria).join(Alumno).join(Grupo).filter(Respuesta.pregunta_id == pregunta.id, Informe.asignatura_id == asignatura.id, Alumno.id != alumno.id, Grupo.id == grupo.id, Tutoria.deleted == False).all()
            for respuesta in respuestas:
                if respuesta:
                    resultado = respuesta.resultado
                    if int(respuesta.resultado) == 0:
                        resultado = 1
                    respuestas_pregunta_lista.append(int(resultado))
        if respuestas_pregunta_lista:
            respuestas_pregunta_grupo_spline.append(round(mean(respuestas_pregunta_lista), 1))
            respuestas_pregunta_grupo_spline_without_NaN.append(round(mean(respuestas_pregunta_lista), 1))
        else:
            respuestas_pregunta_grupo_spline.append('NaN')

    if respuestas_pregunta_grupo_spline_without_NaN:
        respuestas_pregunta_grupo_media = round(mean(respuestas_pregunta_grupo_spline_without_NaN), 1)

    for asignatura in asignaturas:
        respuestas_asignatura_lista = []
        for pregunta in preguntas:
            respuestas = session_sql.query(Respuesta).join(Informe).join(Tutoria).join(Alumno).join(Grupo).filter(Respuesta.pregunta_id == pregunta.id, Informe.asignatura_id == asignatura.id, Alumno.id != alumno.id, Grupo.id == grupo.id, Tutoria.deleted == False).all()
            for respuesta in respuestas:
                if respuesta:
                    resultado = respuesta.resultado
                    if int(respuesta.resultado) == 0:
                        resultado = 1
                    respuestas_asignatura_lista.append(int(resultado))

        if respuestas_asignatura_lista:
            respuestas_asignatura_grupo_spline.append(round(mean(respuestas_asignatura_lista), 1))
            respuestas_asignatura_grupo_spline_without_NaN.append(round(mean(respuestas_asignatura_lista), 1))
        else:
            respuestas_asignatura_grupo_spline.append('NaN')

    if respuestas_asignatura_grupo_spline_without_NaN:
        respuestas_asignatura_grupo_media = round(mean(respuestas_asignatura_grupo_spline_without_NaN), 1)

    stats['respuestas_pregunta_grupo_lista'] = respuestas_pregunta_grupo_spline
    stats['respuestas_pregunta_grupo_media'] = respuestas_pregunta_grupo_media
    stats['respuestas_asignatura_grupo_lista'] = respuestas_asignatura_grupo_spline
    stats['respuestas_asignatura_grupo_media'] = respuestas_asignatura_grupo_media

    return stats


def respuestas_tutoria_media(tutoria_id):
    repuestas_tutoria_lista = []
    repuestas_tutoria_media = 'sin_notas'
    respuestas = session_sql.query(Respuesta).join(Informe).join(Tutoria).filter(Tutoria.id == tutoria_id).all()
    for respuesta in respuestas:
        if respuesta:
            resultado = respuesta.resultado
            if int(respuesta.resultado) == 0:
                resultado = 1
            repuestas_tutoria_lista.append(int(resultado))
    if repuestas_tutoria_lista:
        repuestas_tutoria_media = round(mean(repuestas_tutoria_lista), 1)

    return repuestas_tutoria_media


def notas_pruebas_evaluables_alumno(tutoria_id, asignatura_id):
    nota_pruebas_evaluables_asignatura_lista = []
    pruebas_evaluables_nombre_asignatura_lista = []
    nota_pruebas_evaluables_asignatura_media = 'sin_notas'
    stats = {}

    pruebas_evaluables = session_sql.query(Prueba_Evaluable).join(Informe).join(Tutoria).filter(Tutoria.id == tutoria_id, Informe.asignatura_id == asignatura_id).all()
    for prueba_evaluable in pruebas_evaluables:
        if prueba_evaluable:
            nota_pruebas_evaluables_asignatura_lista.append(float(prueba_evaluable.nota))
            pruebas_evaluables_nombre_asignatura_lista.append((prueba_evaluable.nombre, float(prueba_evaluable.nota)))
    if nota_pruebas_evaluables_asignatura_lista:
        nota_pruebas_evaluables_asignatura_media = round(mean(nota_pruebas_evaluables_asignatura_lista), 1)

    stats['notas_alumno_lista'] = nota_pruebas_evaluables_asignatura_lista
    stats['notas_alumno_media'] = nota_pruebas_evaluables_asignatura_media
    stats['notas_alumno_lista_asignatura'] = pruebas_evaluables_nombre_asignatura_lista
    return stats


def notas_pruebas_evaluables_grupo(tutoria_id, asignatura_id):
    notas_pruebas_evaluables_lista = []
    nota_pruebas_evaluables_media = 'sin_notas'
    grupo = grupo_by_tutoria_id(tutoria_id)
    alumno = alumno_by_tutoria_id(tutoria_id)
    pruebas_evaluables = session_sql.query(Prueba_Evaluable).join(Informe).join(Tutoria).filter(Informe.asignatura_id == asignatura_id, Tutoria.alumno_id != alumno.id, Tutoria.deleted == False).all()

    for prueba_evaluable in pruebas_evaluables:
        if prueba_evaluable:
            notas_pruebas_evaluables_lista.append(float(prueba_evaluable.nota))
    if notas_pruebas_evaluables_lista:
        nota_pruebas_evaluables_media = mean(notas_pruebas_evaluables_lista)

    return nota_pruebas_evaluables_media


def evolucion_tutorias(alumno_id):
    evolucion_grupo_lista = []
    evolucion_grupo_media_lista = []
    evolucion_alumno_lista = []
    evolucion_alumno_media_lista = []
    evolucion_notas_serie = []
    evolucion_notas = []
    alumno = alumno_by_id(alumno_id)
    tutorias_alumno = session_sql.query(Tutoria).filter(Tutoria.alumno_id == alumno_id, Tutoria.deleted == False).order_by(desc('fecha')).all()
    tutorias_grupo = session_sql.query(Tutoria).join(Alumno).join(Grupo).filter(Grupo.id == alumno.grupo_id, Tutoria.alumno_id != alumno_id, Tutoria.deleted == False).order_by(desc('fecha')).all()
    stats = {}

    # evolucion_grupo
    for tutoria in tutorias_grupo:
        for informe in tutoria.informes:
            for respuesta in informe.respuestas:
                if respuesta:
                    resultado = respuesta.resultado
                    if int(respuesta.resultado) == 0:
                        resultado = 1
                    evolucion_grupo_lista.append(int(resultado))
        if evolucion_grupo_lista:
            evolucion_grupo_media_lista.append([arrow.get(tutoria.fecha).timestamp * 1000, round(mean(evolucion_grupo_lista), 1)])
        evolucion_grupo_lista = []

    # evolucion_alumno
    for tutoria in tutorias_alumno:
        for informe in tutoria.informes:
            for respuesta in informe.respuestas:
                if respuesta:
                    resultado = respuesta.resultado
                    if int(respuesta.resultado) == 0:
                        resultado = 1
                    evolucion_alumno_lista.append(int(resultado))
            for prueba_evaluable in informe.pruebas_evaluables:
                evolucion_notas_serie.append(float(prueba_evaluable.nota))

        if evolucion_alumno_lista:
            evolucion_alumno_media_lista.append([arrow.get(tutoria.fecha).timestamp * 1000, round(mean(evolucion_alumno_lista), 1)])
        evolucion_alumno_lista = []
        if evolucion_notas_serie:
            evolucion_notas.append([arrow.get(tutoria.fecha).timestamp * 1000, round(mean(evolucion_notas_serie), 1)])
        evolucion_notas_serie = []

    stats['evolucion_grupo_media_lista'] = evolucion_grupo_media_lista
    stats['evolucion_alumno_media_lista'] = evolucion_alumno_media_lista
    stats['evolucion_notas'] = evolucion_notas

    return stats


def alumno_by_tutoria_id(tutoria_id):
    return session_sql.query(Alumno).join(Tutoria).filter(Tutoria.id == tutoria_id).first()


def grupo_by_tutoria_id(tutoria_id):
    return session_sql.query(Grupo).join(Alumno).filter(Alumno.id == alumno_by_tutoria_id(tutoria_id).id).first()


def informe_by_tutoria_id_by_asignatura_id(tutoria_id, asignatura_id):
    return session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id, Informe.asignatura_id == asignatura_id).first()


def informes_by_tutoria_id(tutoria_id):
    return session_sql.query(Informe).filter(Informe.tutoria_id == tutoria_id).all()


def informes_grupo_by_tutoria_id(tutoria_id):
    return session_sql.query(Informe).join(Tutoria).join(Alumno).join(Grupo).filter(Grupo.id == grupo_by_tutoria_id(tutoria_id, Tutoria.deleted == False).id).all()


# ***********************************************************************
# Funciones para usuario anonimos para rellenar el formulario.
# ***********************************************************************

def settings_by_tutoria_id(tutoria_id):  # (Settings) by tutoria_id
    settings_by_tutoria_id = session_sql.query(Settings).join(Grupo).join(Alumno).join(Tutoria).filter(Tutoria.id == tutoria_id).first()
    return settings_by_tutoria_id


def invitado_preguntas(settings_id):  # [Preguntas] by settings_id
    invitado_preguntas = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings_id).order_by('orden').all()
    return invitado_preguntas


def invitado_preguntas_by_categoria_id(settings_id, categoria_id):  # [Preguntas] by settings_id
    invitado_preguntas = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings_id).join(Categoria).filter(Categoria.id == categoria_id).order_by(Pregunta.orden).all()
    return invitado_preguntas


def settings_by_tutoria_id_by_id(settings_id):  # (Settings) by settings_id
    settings_by_tutoria_id_by_id = session_sql.query(Settings).filter(Settings.user_id == settings_id).first()
    return settings_by_tutoria_id_by_id


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


# *****************************************************************
# XXX admin stats (SIN PANDAS)
# *****************************************************************


def usuarios_all_count():
    return session_sql.query(User).count()


def usuarios_activos_count():
    return session_sql.query(Settings).filter(Settings.grupo_activo_id != None).count()


def tutorias_all_count():
    return session_sql.query(Tutoria).filter(Tutoria.deleted == False).count()


def profesores_all_cunt():
    return session_sql.query(Asignatura).count()


def informes_all_count():
    return session_sql.query(Informe).count()


def preguntas_all_count():
    return session_sql.query(Pregunta).count()


def respuesta_all_count():
    return session_sql.query(Respuesta).count()


def usuarios_mas_activos(numero):
    return session_sql.query(Settings).order_by(desc('visit_number'), 'visit_last').all()[0:numero]


def profesores_por_usuario():
    try:
        settings_profesores_count_lista = []
        settings_all = session_sql.query(Settings).filter(Settings.grupo_activo_id != None).count()
        for settings in settings_all:
            settings_profesores_count = g.settings_current_user.query(Asignatura).filter(Asignatura.grupo_id == settings.grupo_activo_id).count()
            settings_profesores_count_lista.append(settings_profesores_count)
        profesores_min = min(settings_profesores_count_lista)
        profesores_media = int(mean(settings_profesores_count_lista))
        profesores_max = max(settings_profesores_count_lista)
        return profesores_min, profesores_media, profesores_max
    except:
        return 1, 1, 1


def emails_validados_count():
    try:
        emails_validados_count = session_sql.query(Settings).filter(Settings.email_validated == True).count()
        emails_validados_percent = emails_validados_count / usuarios_all_count() * 100
        return emails_validados_count, emails_validados_percent
    except:
        return 1, 1


def emails_no_robinson_count():
    try:
        emails_no_robinson_count = session_sql.query(Settings).filter(Settings.email_robinson == False).count()
        emails_no_robinson_percent = emails_no_robinson_count / usuarios_all_count() * 100
        return emails_no_robinson_count, emails_no_robinson_percent
    except:
        return 1, 1


def emails_no_ban_count():
    try:
        emails_no_ban_count = session_sql.query(Settings).filter(Settings.ban == False).count()
        emails_no_ban_percent = emails_no_ban_count / usuarios_all_count() * 100
        return emails_no_ban_count, emails_no_ban_percent
    except:
        return 1, 1


def tutoria_timeout_count():
    try:
        tutoria_timeout_count = session_sql.query(Settings).filter(Settings.tutoria_timeout == True).count()
        tutoria_timeout_percent = tutoria_timeout_count / usuarios_all_count() * 100
        return tutoria_timeout_count, tutoria_timeout_percent
    except:
        return 1, 1


def informes_con_comentario_count():
    try:
        informes_con_comentario_count = session_sql.query(Informe).filter(Informe.comentario != '').count()
        informes_con_comentario_percent = int(informes_con_comentario_count / informes_all_count() * 100)
        return informes_con_comentario_count, informes_con_comentario_percent
    except:
        return 1, 1


def diferencial_media():
    try:
        diferencial_lista = []
        settings_all = session_sql.query(Settings).filter(Settings.grupo_activo_id != None).all()
        for settings in settings_all:
            diferencial_lista.append(settings.diferencial)
        diferencial_media = int(mean(diferencial_lista))
        return diferencial_media
    except:
        return 1


def informes_con_pruebas_evalubles_count():
    try:
        informes_con_pruebas_evalubles_evolucion = []
        informes_con_pruebas_evalubles_count = 0
        informes_count = 0
        informes = session_sql.query(Informe).order_by('created_at').all()
        for informe in informes:
            informe_prueba_evaluble_check = session_sql.query(Prueba_Evaluable).filter(Prueba_Evaluable.informe_id == informe.id).first()
            informes_count = informes_count + 1
            if informe_prueba_evaluble_check:
                informes_con_pruebas_evalubles_count = informes_con_pruebas_evalubles_count + 1
                informes_con_pruebas_evalubles_evolucion.append([arrow.get(informe.created_at).timestamp * 1000, int(informes_con_pruebas_evalubles_count / informes_count * 100)])
        informes_con_pruebas_evalubles_percent = int(informes_con_pruebas_evalubles_count / informes_all_count() * 100)
        return informes_con_pruebas_evalubles_count, informes_con_pruebas_evalubles_percent, informes_con_pruebas_evalubles_evolucion
    except:
        return 1, 1, 1


def evolucion_equipo_educativo_count():
    try:
        evolucion_equipo_educativo_count = session_sql.query(Settings).filter(Settings.show_asignaturas_analisis == True).count()
        evolucion_equipo_educativo_percent = evolucion_equipo_educativo_count / usuarios_all_count() * 100
        return evolucion_equipo_educativo_count, evolucion_equipo_educativo_percent
    except:
        return 1, 1


def tutorias_con_respuesta_count():
    try:
        # NOTE todos los informes tienen respuesta pues son generados al responder
        tutorias_sin_respuesta_count = 0
        tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == False).all()
        for tutoria in tutorias:
            tutoria_respuesta = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria.id).first()
            if not tutoria_respuesta:
                tutorias_sin_respuesta_count = tutorias_sin_respuesta_count + 1
        tutorias_con_respuesta_count = tutorias_all_count() - tutorias_sin_respuesta_count
        tutorias_con_respuesta_percent = tutorias_con_respuesta_count / tutorias_all_count() * 100
        return tutorias_con_respuesta_count, tutorias_con_respuesta_percent
    except:
        return 1, 1


def tutorias_con_acuerdo_count():
    try:
        tutorias_con_respuesta_count = session_sql.query(Tutoria).filter(Tutoria.acuerdo != None, Tutoria.deleted == False).count()
        tutorias_con_respuesta_percent = tutorias_con_respuesta_count / tutorias_all_count() * 100
        return tutorias_con_respuesta_percent
    except:
        return 1


def preguntas_por_cuestionario():
    try:
        preguntas_por_cuestionario = []
        settings_all = session_sql.query(Settings).filter(Settings.grupo_activo_id != None).all()
        for settings in settings_all:
            preguntas_numero = session_sql.query(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings.id).count()
            preguntas_por_cuestionario.append(preguntas_numero)
        preguntas_por_cuestionario_min = min(preguntas_por_cuestionario)
        preguntas_por_cuestionario_media = int(mean(preguntas_por_cuestionario))
        preguntas_por_cuestionario_max = max(preguntas_por_cuestionario)
        preguntas_por_cuestionario_percent = preguntas_por_cuestionario_media / preguntas_all_count() * 100
        return preguntas_por_cuestionario_min, preguntas_por_cuestionario_media, preguntas_por_cuestionario_max, preguntas_por_cuestionario_percent
    except:
        return 1, 1, 1, 1


def tutorias_por_usuario_count():
    try:
        tutorias_por_usuario_list = []
        settings_all = session_sql.query(Settings).filter(Settings.grupo_activo_id != None).all()  # NOTE con esto aseguro que el usuario al menos ha creado un grupo_activo_id
        for settings in settings_all:
            tutorias_por_usuario = session_sql.query(Tutoria).join(Alumno).join(Grupo).filter(Grupo.id == settings.grupo_activo_id, Tutoria.deleted == False).count()
            tutorias_por_usuario_list.append(tutorias_por_usuario)
        tutorias_por_usuario_min = min(tutorias_por_usuario_list)
        tutorias_por_usuario_media = int(mean(tutorias_por_usuario_list))
        tutorias_por_usuario_max = max(tutorias_por_usuario_list)
        return tutorias_por_usuario_min, tutorias_por_usuario_media, tutorias_por_usuario_max,
    except:
        return 1, 1, 1


def cuestionario_actividad():
    try:
        preguntas_id_lista = []
        preguntas_frecuencias_lista = []
        settings_all = session_sql.query(Settings).filter(Settings.grupo_activo_id != None).all()  # NOTE con esto aseguro que el usuario al menos ha creado un grupo_activo_id
        for settings in settings_all:
            settings_cuestionario_id = session_sql.query(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == settings.id).all()
            for pregunta in settings_cuestionario_id:
                preguntas_id_lista.append(pregunta.pregunta_id)
        preguntas = session_sql.query(Pregunta).order_by('orden').all()
        for pregunta in preguntas:
            frecuencia = preguntas_id_lista.count(pregunta.id)
            preguntas_frecuencias_lista.append([pregunta.enunciado_ticker, frecuencia])
        return preguntas_frecuencias_lista
    except:
        return 1


def evolucion_tutorias_exito_grupo(current_grupo_id):
    try:
        informes_posibles_count = 0
        tutoria_profesores_responden_evolucion = []
        media_lista = []
        tutorias = session_sql.query(Tutoria).join(Alumno).join(Grupo).filter(Grupo.id == current_grupo_id, Tutoria.deleted == False).order_by('fecha').all()
        for tutoria in tutorias:
            asignaturas_tutoria_count = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria.id).count()
            informes_posibles_count = informes_posibles_count + asignaturas_tutoria_count
            profesores_respoden = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria.id).count()
            profesores_respoden_percent = int(profesores_respoden / asignaturas_tutoria_count * 100)
            tutoria_profesores_responden_evolucion.append([arrow.get(tutoria.fecha).timestamp * 1000, profesores_respoden_percent])
            media_lista.append(profesores_respoden_percent)
        tutoria_profesores_responden_evolucion_media = int(mean(media_lista))
        return tutoria_profesores_responden_evolucion, tutoria_profesores_responden_evolucion_media
    except:
        return 1, 1


def profesores_actividad_count():
    try:
        informes_posibles_count = 0
        profesores_activos_evolucion_frecuencia_add = 0
        profesores_activos_evolucion = []
        tutoria_profesores_responden_valor = []
        profesores_activos_evolucion_frecuencia = []
        profesores_activos_evolucion_frecuencia_absoluta = []
        media_lista = []
        tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == False).order_by('fecha').all()
        for tutoria in tutorias:
            tutoria_asignaturas_count = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria.id).count()
            informes_posibles_count = informes_posibles_count + tutoria_asignaturas_count
            profesores_respoden = session_sql.query(Informe).filter(Informe.tutoria_id == tutoria.id).count()
            profesores_respoden_percent = int(profesores_respoden / tutoria_asignaturas_count * 100)
            tutoria_profesores_responden_valor.append(int(profesores_respoden_percent / 10) * 10)  # NOTE para repondear a decenas
            profesores_activos_evolucion.append([arrow.get(tutoria.fecha).timestamp * 1000, profesores_respoden_percent])

            media_lista.append(profesores_respoden_percent)
        profesores_activos_evolucion_media = int(mean(media_lista))
        for percent in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            frecuencia = tutoria_profesores_responden_valor.count(percent) / tutorias_all_count() * 100
            profesores_activos_evolucion_frecuencia.append([percent, frecuencia])
            profesores_activos_evolucion_frecuencia_add = profesores_activos_evolucion_frecuencia_add + frecuencia
            profesores_activos_evolucion_frecuencia_absoluta.append([percent, profesores_activos_evolucion_frecuencia_add])
        profesores_activos_count = informes_all_count()
        profesores_activos_percent = informes_all_count() / informes_posibles_count * 100
        return profesores_activos_count, profesores_activos_percent, profesores_activos_evolucion, profesores_activos_evolucion_frecuencia, profesores_activos_evolucion_frecuencia_absoluta, profesores_activos_evolucion_media
    except:
        return 1, 1, 1, 1, 1, 1

# *****************************************************************
# XXX FIN admin stats


def tutoria_calendar_undelete(event_id):
    if g.settings_current_user.calendar:
        try:
            oauth2_credentials = g.settings_current_user.oauth2_credentials
            credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http)
        except:
            return redirect(url_for('oauth2callback_calendar'))
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            event['status'] = 'confirmed'
            updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        except:
            pass


def tutoria_calendar_delete(event_id):
    g.settings_current_user = g.settings_current_user
    if g.settings_current_user.calendar:
        try:
            oauth2_credentials = g.settings_current_user.oauth2_credentials
            credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http)
        except:
            return redirect(url_for('oauth2callback_calendar'))
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
        except:
            pass


def tutoria_calendar_add(service, tutoria_add, calendar_datetime_utc_start_arrow, calendar_datetime_utc_end_arrow, alumno_nombre):

    event = {
        'summary': 'Tutoria de ' + alumno_nombre,
        'location': grupo_activo().centro,
        'description': 'Evento creado por https://mitutoria.herokuapp.com/',
        'colorId': '3',
        'start': {
            'dateTime': calendar_datetime_utc_start_arrow,
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': calendar_datetime_utc_end_arrow,
            'timeZone': 'Europe/Madrid',
        }
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    session_sql.flush()
    session_sql.refresh(tutoria_add)
    tutoria_add_id = tutoria_add.id
    tutoria_sql = tutoria_by_id(tutoria_add_id)
    tutoria_sql.calendar_event_id = event['id']
    if session_sql.is_modified(tutoria_sql):
        session_sql.commit()


def cleanpup_tutorias(periodo_cleanup_tutorias):
    tutorias_deleted_count = 0
    tutorias_clenaup = session_sql.query(Tutoria).filter(Tutoria.fecha < g.current_date - datetime.timedelta(days=30 * periodo_cleanup_tutorias)).all()
    for tutoria in tutorias_clenaup:
        tutorias_deleted_count = tutorias_deleted_count + 1
        session_sql.delete(tutoria)
    if tutorias_deleted_count != 0:
        settings_all = session_sql.query(Settings).all()
        for settings in settings_all:
            if not settings.cleanup_tutorias_status:
                settings.cleanup_tutorias_status = True
        session_sql.commit()
    flash_toast('CleanUp [' + str(tutorias_deleted_count) + ' tutorias]', 'success')
    return tutorias_deleted_count


def tutoria_calendar_sync():
    g.settings_current_user = g.settings_current_user
    if g.settings_current_user:
        if g.settings_current_user.calendar:
            try:
                credentials = oauth2client.client.Credentials.new_from_json(g.settings_current_user.oauth2_credentials)
                http = httplib2.Http()
                http = credentials.authorize(http)
                service = discovery.build('calendar', 'v3', http=http)
            except:
                return redirect(url_for('oauth2callback_calendar'))
            if g.settings_current_user.calendar_sincronizado:
                for tutoria in tutorias_by_grupo_id(g.settings_current_user.grupo_activo_id):
                    try:
                        event = service.events().get(calendarId='primary', eventId=tutoria.calendar_event_id).execute()
                        calendar_datetime_utc_start_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute).replace(tzinfo='Europe/Madrid'))
                        if tutoria.deleted:
                            service.events().delete(calendarId='primary', eventId=event['id']).execute()
                        # NOTE checkea cambios a sincronizar
                        if event['status'] == 'confirmed':  # NOTE Sincroniza fechas de eventos del calendario
                            if event['start']['dateTime'] != calendar_datetime_utc_start_arrow:
                                tutoria.fecha = arrow.get(event['start']['dateTime']).date()
                                tutoria.hora = arrow.get(event['start']['dateTime']).time()
                                alumno = alumno_by_tutoria_id(tutoria.id)
                                if tutoria.fecha < g.current_date:
                                    if tutoria.activa:
                                        tutoria.activa = False
                                        # flash_toast('Tutoria de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' auto-archivada', 'info')
                                        flash_toast('Google-Calendar sincronizando tutorías', 'info')

                                if g.current_date <= arrow.get(event['start']['dateTime']).date():
                                    if not tutoria.activa:
                                        tutoria.activa = True
                                        # flash_toast('Tutoria de ' + Markup('<strong>') + alumno.nombre + Markup('</strong>') + ' auto-activada', 'info')
                                        flash_toast('Google-Calendar sincronizando tutorías', 'info')

                        else:  # Elimina tutoria si ha sido eliminado desde la agenda
                            tutoria.deleted = True
                            tutoria.deleted_at = g.current_time
                    except:  # NOTE Elimina tutoria si no esta en el calendario
                        tutoria.deleted = True
                        tutoria.deleted_at = g.current_time

                # NOTE Purga eventos de las tutorias eliminadas por el cleanpup
                if g.settings_current_user.cleanup_tutorias_status:
                    g.settings_current_user.cleanup_tutorias_status = False
                    page_token = None
                    while True:
                        events = service.events().list(calendarId='primary', pageToken=page_token, q='Evento creado por https://mitutoria.herokuapp.com/').execute()
                        for event in events['items']:
                            if not tutoria_by_calendar_event_id(event['id']):
                                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                        page_token = events.get('nextPageToken')
                        if not page_token:
                            break
            else:
                # NOTE Purga eventos que contienen 'Evento creado por https://mitutoria.herokuapp.com/'
                page_token = None
                while True:
                    events = service.events().list(calendarId='primary', pageToken=page_token, q='Evento creado por https://mitutoria.herokuapp.com/').execute()
                    for event in events['items']:
                        service.events().delete(calendarId='primary', eventId=event['id']).execute()
                    page_token = events.get('nextPageToken')
                    if not page_token:
                        break
                # NOTE Agrega todas las tutorias al calendario una vez purgado
                for tutoria in tutorias_by_grupo_id(g.settings_current_user.grupo_activo_id, deleted=False):
                    alumno_nombre = alumno_by_tutoria_id(tutoria.id).nombre
                    calendar_datetime_utc_start_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute).replace(tzinfo='Europe/Madrid'))
                    calendar_datetime_utc_end_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute + g.settings_current_user.tutoria_duracion).replace(tzinfo='Europe/Madrid'))
                    tutoria_calendar_add(service, tutoria, calendar_datetime_utc_start_arrow, calendar_datetime_utc_end_arrow, alumno_nombre)
                flash_toast('Sincronizacion inical de Google Calendar', 'success')
                g.settings_current_user.calendar_sincronizado = True
            session_sql.commit()


def diferencial_check(percent, resultado_1, resultado_2):
    if resultado_1 == 'sin_notas' or resultado_2 == 'sin_notas' or not resultado_1 or not resultado_2:
        return False
    else:
        if (float(resultado_1) - float(resultado_2)) > resultado_1 * percent / 100:
            return True
    return False


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


def asignatura_informes_solicitados_count(asignatura_id):
    return session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.asignatura_id == asignatura_id).count()


def asignatura_informes_respondidos_count(asignatura_id):
    return session_sql.query(Informe).filter(Informe.asignatura_id == asignatura_id).count()


def asignatura_informes_solicitados_recent_count(asignatura_id):
    return session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.asignatura_id == asignatura_id, Association_Tutoria_Asignatura.created_at > g.current_date - datetime.timedelta(days=g.settings_global.periodo_participacion_recent)).count()


def asignatura_informes_respondidos_recent_count(asignatura_id):
    return session_sql.query(Informe).filter(Informe.asignatura_id == asignatura_id, Informe.created_at > g.current_date - datetime.timedelta(days=g.settings_global.periodo_participacion_recent)).count()


def tutorias_sin_respuesta_by_asignatura_id(asignatura_id):
    dic = {}
    tutorias_id_lista = []

    # tutorias_count
    tutorias_activas_pendintes_count = session_sql.query(Tutoria).filter(Tutoria.activa == True, Tutoria.deleted == False).join(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.asignatura_id == asignatura_id).count()
    tutorias_activas_respondidas_count = session_sql.query(Tutoria).filter(Tutoria.activa == True, Tutoria.deleted == False).join(Informe).filter(Informe.asignatura_id == asignatura_id).count()
    tutorias_sin_respuesta_count = tutorias_activas_pendintes_count - tutorias_activas_respondidas_count
    dic['tutorias_sin_respuesta_count'] = tutorias_sin_respuesta_count

    # tutorias (se podra usar para agregar la opcion de volver a recibir por email las tutorias no contestadas)
    if tutorias_sin_respuesta_count != 0:
        tutorias_activas_pendintes = session_sql.query(Tutoria).filter(Tutoria.activa == True, Tutoria.deleted == False).join(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.asignatura_id == asignatura_id).all()
        tutorias_activas_respondidas = session_sql.query(Tutoria).filter(Tutoria.activa == True, Tutoria.deleted == False).join(Informe).filter(Informe.asignatura_id == asignatura_id).all()
        for tutoria in tutorias_activas_pendintes:
            if tutoria not in tutorias_activas_respondidas:
                tutorias_id_lista.append(tutoria.id)
    dic['tutorias_id_lista'] = tutorias_id_lista
    return dic


def connenction_check():
    try:
        with mail.connect() as conn:
            for asignatura_id in asignaturas_id_lista:
                conn.send('prueba')
        print('OK')
    except:
        print('xxx ERROR xxx')


# *****************************************************************
# XXX: envio de mails por threading (gmail API)
# *****************************************************************


def send_email_tutoria(alumno, tutoria):
    try:
        settings_global_sql = session_sql.query(Settings_Global).first()
        settings_current_user_sql = settings()
        oauth2_credentials = settings_global_sql.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
    except:
        return redirect(url_for('oauth2callback_gmail'))
    sender = settings_global_sql.gmail_sender
    emails_enviados = settings_current_user_sql.emails_enviados

    for asignatura in asignaturas_alumno_by_alumno_id(alumno.id):
        tutoria_asignatura_add = Association_Tutoria_Asignatura(tutoria_id=tutoria.id, asignatura_id=asignatura.id)
        session_sql.add(tutoria_asignatura_add)
        # XXX envio de mail
        # ****************************************
        to = asignatura.email
        tutoria_dia_semana = translate_fecha(tutoria.fecha.strftime('%A'))
        tutoria_dia_mes = tutoria.fecha.strftime('%d')
        emails_enviados += 1
        grupo_activo_sql = grupo_activo()
        subject = 'Tutoria | %s | %s | %s %s [e-%s]' % (grupo_activo_sql.nombre, alumno.nombre, tutoria_dia_semana, tutoria_dia_mes, emails_enviados)
        message_text = render_template('email_tutoria.html', grupo=grupo_activo_sql, tutoria=tutoria, alumno=alumno, asignatura=asignatura, tutoria_email_link=tutoria_email_link, index_link=index_link)
        create_message_and_send(service, sender, to, subject, message_text)
        time.sleep(email_time_sleep)
    settings_current_user_sql.emails_enviados = emails_enviados
    session_sql.commit()


def send_email_tutoria_asincrono(alumno, tutoria):
    @copy_current_request_context
    def send_email_tutoria_process(alumno, tutoria):
        send_email_tutoria(alumno, tutoria)
    send_email_tutoria_threading = threading.Thread(name='send_email_tutoria_thread', target=send_email_tutoria_process, args=(alumno, tutoria))
    send_email_tutoria_threading.start()


def send_email_validate(user):
    try:
        settings_global_sql = session_sql.query(Settings_Global).first()
        settings_current_user_sql = settings_by_id(user.id)
        oauth2_credentials = settings_global_sql.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
    except:
        return redirect(url_for('oauth2callback_gmail'))

    # XXX envio de mail
    # ****************************************
    try:
        sender = settings_global_sql.gmail_sender
        to = user.email
        email_validated_intentos = settings_current_user_sql.email_validated_intentos
        subject = 'Verificación de email [e-%s]' % (email_validated_intentos)
        message_text = render_template('email_validate.html', user=user, email_validate_link=email_validate_link, index_link=index_link)
        create_message_and_send(service, sender, to, subject, message_text)
    except:
        abort_asincrono(500)


def send_email_validate_asincrono(user):
    @copy_current_request_context
    def send_email_validate_process(user):
        send_email_validate(user)
    send_email_validate_threading = threading.Thread(name='send_email_validate_thread', target=send_email_validate_process, args=(user,))
    send_email_validate_threading.start()


def re_send_email_tutoria(alumno, tutoria, asignaturas_id_lista):
    try:
        settings_global_sql = session_sql.query(Settings_Global).first()
        settings_current_user_sql = settings()
        oauth2_credentials = settings_global_sql.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
    except:
        return redirect(url_for('oauth2callback_gmail'))
    sender = settings_global_sql.gmail_sender
    emails_enviados = settings_current_user_sql.emails_enviados

    try:
        for asignatura_id in asignaturas_id_lista:
            asignatura = asignatura_by_id(asignatura_id)
            association_tutoria_asignatura_sql = session_sql.query(Association_Tutoria_Asignatura).filter(Association_Tutoria_Asignatura.tutoria_id == tutoria.id, Association_Tutoria_Asignatura.asignatura_id == asignatura_id).first()
            if association_tutoria_asignatura_sql:
                association_tutoria_asignatura_sql.created_at = datetime.datetime.today()
                email_reenvio_number = association_tutoria_asignatura_sql.email_reenvio_number
            else:
                tutoria_asignatura_add = Association_Tutoria_Asignatura(tutoria_id=tutoria.id, asignatura_id=asignatura_id)
                session_sql.add(tutoria_asignatura_add)
                session_sql.flush()
                association_tutoria_asignatura_sql = tutoria_asignatura_add
                email_reenvio_number = association_tutoria_asignatura_sql.email_reenvio_number

            # XXX envio de mail
            # ****************************************
            to = asignatura.email
            tutoria_dia_semana = translate_fecha(tutoria.fecha.strftime('%A'))
            tutoria_dia_mes = tutoria.fecha.strftime('%d')
            emails_enviados = emails_enviados + 1
            email_reenvio_number = email_reenvio_number + 1
            association_tutoria_asignatura_sql.email_reenvio_number = email_reenvio_number
            grupo_activo_sql = grupo_activo()
            subject = 'Tutoria | %s | %s |  %s %s [r-%s]' % (grupo_activo_sql.nombre, alumno.nombre, tutoria_dia_semana, tutoria_dia_mes, email_reenvio_number)
            message_text = render_template('email_tutoria.html', grupo=grupo_activo_sql, tutoria=tutoria, alumno=alumno, asignatura=asignatura, tutoria_email_link=tutoria_email_link, index_link=index_link)
            create_message_and_send(service, sender, to, subject, message_text)
            time.sleep(email_time_sleep)
        settings_current_user_sql.emails_enviados = emails_enviados
        session_sql.commit()
        flash_toast('Reenviando emails a las asignaturas elegidas', 'info')
    except:
        abort_asincrono(500)


def re_send_email_tutoria_asincrono(alumno, tutoria, asignaturas_id_lista):
    @copy_current_request_context
    def re_send_email_tutoria_process(alumno, tutoria, asignaturas_id_lista):
        re_send_email_tutoria(alumno, tutoria, asignaturas_id_lista)
    re_send_email_tutoria_threading = threading.Thread(name='re_send_email_tutoria_thread', target=re_send_email_tutoria_process, args=(alumno, tutoria, asignaturas_id_lista))
    re_send_email_tutoria_threading.start()


def send_email_password_reset(current_user_id):
    try:
        settings_global_sql = session_sql.query(Settings_Global).first()
        settings_current_user_sql = settings()
        oauth2_credentials = settings_global_sql.oauth2_credentials
        credentials = oauth2client.client.Credentials.new_from_json(oauth2_credentials)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
    except:
        return redirect(url_for('oauth2callback_gmail'))
    # XXX envio de mail
    # ****************************************
    try:
        sender = settings_global_sql.gmail_sender
        to = user_by_id(current_user_id).email
        subject = 'Cambiar password'
        params = {}
        params['current_user_id'] = current_user_id
        params['password_reset_link'] = password_reset_link
        params['email_validate_link'] = email_validate_link
        params['index_link'] = index_link
        message_text = render_template('email_password_reset_request.html', params=params)
        create_message_and_send(service, sender, to, subject, message_text)
    except:
        abort_asincrono(500)


def send_email_password_reset_request_asincrono(current_user_id):
    @copy_current_request_context
    def send_email_password_reset_request_process(current_user_id):
        send_email_password_reset(current_user_id)
    send_email_password_reset_request_threading = threading.Thread(name='send_email_password_reset_request_thread', target=send_email_password_reset_request_process, args=(current_user_id,))
    send_email_password_reset_request_threading.start()
# *****************************************************************


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


def grupo_delete(grupo_delete_id):  # NOTE No es un simple delete, ademas hace algunas otras tareas
    grupo_delete_sql = session_sql.query(Grupo).filter(Grupo.id == grupo_delete_id).first()
    if grupo_activo_check(grupo_delete_sql.id):
        g.settings_current_user = session_sql.query(Settings).filter(Settings.id == g.settings_current_user.id).first()
        g.settings_current_user.grupo_activo_id = None
    session_sql.delete(grupo_delete_sql)
    session_sql.commit()


def grupo_activo():  # (Grupo) activo de usuario
    try:
        return session_sql.query(Grupo).filter(Grupo.id == settings().grupo_activo_id).first()
    except:
        pass


def settings():
    try:
        return session_sql.query(Settings).filter_by(id=current_user.id).first()
    except:
        pass


def grupo_activo_check(grupo_id):  # Checkea si un grupo es el activo o no
    if grupo_id == g.settings_current_user.grupo_activo_id:
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


def settings_by_id(settings_id):
    settings_by_id = session_sql.query(Settings).filter(Settings.user_id == settings_id).first()
    return settings_by_id


def usuarios(order_by_1, order_by_2, order_by_3):
    return session_sql.query(Settings).order_by(desc(order_by_1), order_by_2, order_by_3).all()


def user_by_id(user_id):
    user_by_id = session_sql.query(User).filter(User.id == user_id).first()
    return user_by_id


def categoria_by_id(categoria_id):
    return session_sql.query(Categoria).filter(Categoria.id == categoria_id).first()


def categorias(**kwargs):
    return session_sql.query(Categoria).filter_by(**kwargs).order_by('orden').all()


def preguntas_active_default(settings_id):  # Inserta las preguntas_active_default
    preguntas_id_lista = []
    preguntas_active_default = session_sql.query(Pregunta).filter(Pregunta.active_default == True).all()

    if preguntas_active_default:
        for pregunta in preguntas_active_default:
            preguntas_id_lista.append(pregunta.id)

    if preguntas_id_lista:
        for pregunta in preguntas(visible=True):
            if pregunta.id in preguntas_id_lista:
                if not association_settings_pregunta_check(settings_id, pregunta.id):
                    association_settings_pregunta_add = Association_Settings_Pregunta(settings_id=settings_id, pregunta_id=pregunta.id)
                    session_sql.add(association_settings_pregunta_add)
            else:
                if association_settings_pregunta_check(settings_id, pregunta.id):
                    association_settings_pregunta_delete = session_sql.query(Association_Settings_Pregunta).filter_by(settings_id=settings_id, pregunta_id=pregunta.id).first()
                    session_sql.delete(association_settings_pregunta_delete)


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
        if b < a:
            cociente_porcentual = 100
        else:
            cociente_porcentual = int((a / b) * 100)
    else:
        cociente_porcentual = 0
    return cociente_porcentual


def preguntas_by_categoria_id(categoria_id, **kwargs):
    return session_sql.query(Pregunta).filter_by(categoria_id=categoria_id, **kwargs).order_by('orden').all()


def preguntas(**kwargs):  # [Preguntas] disponibles para un cuestionario.
    return session_sql.query(Pregunta).filter_by(**kwargs).order_by('orden').all()


def pregunta_by_id(pregunta_id, **kwargs):
    return session_sql.query(Pregunta).filter_by(id=pregunta_id, **kwargs).first()


def informe_preguntas():
    informe_preguntas = session_sql.query(Pregunta).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == g.settings_current_user.id).all()
    return informe_preguntas


def grupo_informes(grupo_id):
    grupo_informes = session_sql.query(Informe).join(Association_Settings_Pregunta).filter(Association_Settings_Pregunta.settings_id == g.settings_current_user.id).all()


def grupos():
    grupos = session_sql.query(Grupo).filter(Grupo.settings_id == g.settings_current_user.id).order_by(desc('curso_academico'), 'nombre').all()
    return grupos


def curso():
    if 8 <= datetime.date.today().month <= 12:
        curso = datetime.date.today().year
    else:
        curso = datetime.date.today().year - 1
    curso = int(curso)
    return curso


def grupo_by_alumno_id(alumno_id):  # (Grupo) de un alumno
    grupo_by_alumno_id = None
    if alumno_id:
        grupo_by_alumno_id = session_sql.query(Grupo).join('alumnos').filter(Alumno.id == alumno_id).first()
    return grupo_by_alumno_id


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


def tutoria_by_calendar_event_id(calendar_event_id):
    if calendar_event_id:
        return session_sql.query(Tutoria).filter(Tutoria.calendar_event_id == calendar_event_id).first()
    return None


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


def tutorias_by_grupo_id(grupo_id, **kwargs):
    return session_sql.query(Tutoria).filter_by(**kwargs).join(Alumno).join(Grupo).filter(Grupo.id == grupo_id).order_by('fecha').all()

def tutorias_by_grupo_id_descent(grupo_id, **kwargs):
    return session_sql.query(Tutoria).filter_by(**kwargs).join(Alumno).join(Grupo).filter(Grupo.id == grupo_id).order_by(desc('fecha')).all()



def asignaturas_alumno_by_alumno_id(alumno_id):  # (asignaturas) de un alumno
    return session_sql.query(Asignatura).join(Association_Alumno_Asignatura).filter(Association_Alumno_Asignatura.alumno_id == alumno_id).all()


def grupo_alumnos_count(grupo_id):  # {alumnos_count} de un grupo
    return session_sql.query(Alumno).join(Grupo).filter(Grupo.id == grupo_id).count()


def asignaturas(order_by_1, order_by_2, order_by_3):  # [asignaturas] sorted de un grupo
    asignaturas = session_sql.query(Asignatura).filter_by(grupo_id=g.settings_current_user.grupo_activo_id).order_by(order_by_1, order_by_2, order_by_3).all()
    return asignaturas


def asignaturas_not_sorted():  # [asignaturas] not sorted  de un grupo
    asignaturas_not_sorted = session_sql.query(Asignatura).filter_by(grupo_id=g.settings_current_user.grupo_activo_id).order_by('id').all()
    return asignaturas_not_sorted


def alumnos_not_sorted():  # [alumnos] NO ordeandos de un grupo
    alumnos_not_sorted = session_sql.query(Alumno).filter_by(grupo_id=g.settings_current_user.grupo_activo_id).order_by('id').all()
    return alumnos_not_sorted


def alumnos(order_by_1, order_by_2):  # [alumnos] ordeandos de un grupo_activo
    alumnos = session_sql.query(Alumno).filter(Alumno.grupo_id == g.settings_current_user.grupo_activo_id).order_by(str(order_by_1), str(order_by_2)).all()
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


def tutorias_by_alumno_id(alumno_id, **kwargs):  # [Tutorias] de un alumno.
    return session_sql.query(Tutoria).filter_by(alumno_id=alumno_id, **kwargs).order_by(desc('fecha')).all()


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


app.jinja_env.globals.update(cita_random=cita_random,  singular_plural=singular_plural, grupo_activo=grupo_activo, curso=curso, alumnos_not_sorted=alumnos_not_sorted, alumnos=alumnos, tutorias_by_alumno_id=tutorias_by_alumno_id, equal_str=equal_str, asignaturas=asignaturas, asignatura_alumnos=asignatura_alumnos, association_alumno_asignatura_check=association_alumno_asignatura_check,
                             tutoria_asignaturas_count=tutoria_asignaturas_count, string_to_date=string_to_date, association_settings_pregunta_check=association_settings_pregunta_check, preguntas=preguntas, informe_preguntas=informe_preguntas, settings_by_tutoria_id=settings_by_tutoria_id, invitado_preguntas=invitado_preguntas, settings_by_tutoria_id_by_id=settings_by_tutoria_id_by_id, invitado_respuesta=invitado_respuesta, invitado_pruebas_evaluables=invitado_pruebas_evaluables, invitado_informe=invitado_informe, cociente_porcentual=cociente_porcentual, tutoria_asignaturas=tutoria_asignaturas, pregunta_active_default_check=pregunta_active_default_check, pregunta_visible_check=pregunta_visible_check, grupo_activo_check=grupo_activo_check, user_by_id=user_by_id, asignatura_informes_solicitados_count=asignatura_informes_solicitados_count, asignatura_informes_respondidos_count=asignatura_informes_respondidos_count, asignaturas_not_sorted=asignaturas_not_sorted, tutorias_by_grupo_id=tutorias_by_grupo_id, alumno_by_id=alumno_by_id, hashids_encode=hashids_encode, hashids_decode=hashids_decode, f_encode=f_encode, f_decode=f_decode, dic_encode_args=dic_encode_args, dic_try=dic_try, settings_by_id=settings_by_id, usuario_grupos=usuario_grupos, usuarios=usuarios, usuarios_mas_activos=usuarios_mas_activos, grupo_alumnos_count=grupo_alumnos_count, diferencial_check=diferencial_check, categoria_by_id=categoria_by_id, categorias=categorias, preguntas_by_categoria_id=preguntas_by_categoria_id, asignatura_by_id=asignatura_by_id, informe_by_tutoria_id_by_asignatura_id=informe_by_tutoria_id_by_asignatura_id, asignaturas_alumno_by_alumno_id=asignaturas_alumno_by_alumno_id, respuestas_pregunta_alumno_lista=respuestas_pregunta_alumno_lista, respuestas_asignatura_alumno_lista=respuestas_asignatura_alumno_lista, notas_pruebas_evaluables_grupo=notas_pruebas_evaluables_grupo, notas_pruebas_evaluables_alumno=notas_pruebas_evaluables_alumno, analisis_tutoria=analisis_tutoria, tutoria_incoming=tutoria_incoming, asignaturas_orden_switch=asignaturas_orden_switch, asignaturas_ordenadas=asignaturas_ordenadas, invitado_preguntas_by_categoria_id=invitado_preguntas_by_categoria_id, tutoria_stats=tutoria_stats, association_tutoria_asignatura_id=association_tutoria_asignatura_id, translate_fecha=translate_fecha, email_reenvio_number=email_reenvio_number, tutoria_by_id=tutoria_by_id, alumno_by_tutoria_id=alumno_by_tutoria_id, tutorias_by_grupo_id_descent=tutorias_by_grupo_id_descent)
