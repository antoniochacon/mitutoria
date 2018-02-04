
def mantenimiento_re_send_email():
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
                    current_grupo_activo = session_sql.query(Grupo).join('alumnos').filter(Alumno.id == alumno.id).first()
                    subject = 'Tutoria | %s | %s |  %s %s [r-%s]' % (current_grupo_activo.nombre, alumno.nombre, tutoria_dia_semana, tutoria_dia_mes, email_reenvio_number)
                    message_text = 'message_text'
                    create_message_and_send(service, sender, to, subject, message_text)
                settings_current_user_sql.emails_enviados = emails_enviados
            except:
                print('Error al enviar emails')
    print('Mantenimiento Re-Send satisfactorio.')  # NOTE en aws lambda no funciona el print en su lugar usar return


def mantenimiento_re_send_email_asincrono():  # NOTE funciona en modo local pero no como funcion lambda
    def mantenimiento_re_send_email_process():
        mantenimiento_re_send_email()
    mantenimiento_re_send_email_threading = threading.Thread(name='mantenimiento_re_send_email_thread', target=mantenimiento_re_send_email_process, args=())
    mantenimiento_re_send_email_threading.start()
