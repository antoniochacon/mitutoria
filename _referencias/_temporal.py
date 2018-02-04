def tutoria_calendar_sync_clock():
    tutorias = session_sql.query(Tutoria).all()
    for tutoria in tutorias:
        settings_current_user = settings_by_tutoria_id(tutoria.id)
        if settings_current_user.calendar:
            try:
                credentials = oauth2client.client.Credentials.new_from_json(settings_current_user.oauth2_credentials)
                http = httplib2.Http()
                http = credentials.authorize(http)
                service = discovery.build('calendar', 'v3', http=http)
            except:
                print('Error al crear credentials')
            if settings_current_user.calendar_sincronizado:
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
                            if tutoria.fecha < current_date:
                                if tutoria.activa:
                                    tutoria.activa = False  # NOTE auto-archiva la tutoria

                            if current_date <= arrow.get(event['start']['dateTime']).date():
                                if not tutoria.activa:
                                    tutoria.activa = True  # NOTE auto-activa la tutoria

                    else:  # Elimina tutoria si ha sido eliminado desde la agenda
                        tutoria.deleted = True
                        tutoria.deleted_at = current_time
                except:  # NOTE Elimina tutoria si no esta en el calendario
                    tutoria.deleted = True
                    tutoria.deleted_at = current_time

            # NOTE Purga eventos de las tutorias eliminadas por el cleanpup
            if settings_current_user.cleanup_tutorias_status:
                settings_current_user.cleanup_tutorias_status = False
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
            for tutoria in tutorias_by_grupo_id(settings_current_user.grupo_activo_id, deleted=False):
                alumno_nombre = alumno_by_tutoria_id(tutoria.id).nombre
                calendar_datetime_utc_start_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute).replace(tzinfo='Europe/Madrid'))
                calendar_datetime_utc_end_arrow = str(arrow.get(tutoria.fecha).shift(hours=tutoria.hora.hour, minutes=tutoria.hora.minute + settings_current_user.tutoria_duracion).replace(tzinfo='Europe/Madrid'))
                tutoria_calendar_add(service, tutoria, calendar_datetime_utc_start_arrow, calendar_datetime_utc_end_arrow, alumno_nombre)
            flash_toast('Sincronizacion inical de Google Calendar', 'success')
            settings_current_user.calendar_sincronizado = True
        session_sql.commit()


def mantenimiento_historial_clock():
    # XXX mover tutorias al historial
    # current_date = datetime.date.today()
    tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == False, Tutoria.activa == True, Tutoria.fecha < current_date)
    for tutoria in tutorias:
        tutoria.activa = False
    session_sql.commit()


def mantenimiento_papelera_clock():
    # XXX purgar papelera tutorias
    # current_date = datetime.date.today()
    # settings_global = session_sql.query(Settings_Global).first()
    tutorias = session_sql.query(Tutoria).filter(Tutoria.deleted == True, Tutoria.deleted_at < current_date - datetime.timedelta(days=settings_global.periodo_deleted_tutorias)).all()
    for tutoria in tutorias:
        session_sql.delete(tutoria)
    session_sql.commit()


def mantenimiento_re_send_email_clock():
    # XXX re_send_email last 24h
    # settings_global = session_sql.query(Settings_Global).first()
    # current_date = datetime.date.today()
    sender = settings_global.gmail_sender

    # XXX crea el servicio gmail
    try:
        oauth2_credentials = settings_global.oauth2_credentials
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
