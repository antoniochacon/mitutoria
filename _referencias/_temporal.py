def tutoria_calendar_sync_clock():
    settings_global = session_sql.query(Settings_Global).first()
    current_date = datetime.date.today()
    settings_current_users = session_sql.query(Settings).all()
    for settings_current_user in settings_current_users:
        if settings_current_user.calendar:
            try:
                credentials = oauth2client.client.Credentials.new_from_json(settings_current_user.oauth2_credentials)
                http = httplib2.Http()
                http = credentials.authorize(http)
                service = discovery.build('calendar', 'v3', http=http)
            except:
                pass  # He eliminado la peticion de permiso
            if settings_current_user.calendar_sincronizado:
                for tutoria in tutorias_by_grupo_id(settings_current_user.grupo_activo_id):
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
                            tutoria.deleted_at = current_date
                    except:  # NOTE Elimina tutoria si no esta en el calendario
                        tutoria.deleted = True
                        tutoria.deleted_at = current_date
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
                settings_current_user.calendar_sincronizado = True
    session_sql.commit()
