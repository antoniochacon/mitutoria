from app import app
from functions import *
import functions

import urllib3
# import hjson
import logging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=15)
def heroku_dont_sleep():
    # XXX LOCAL_HOST:
    # url = 'http://localhost:5000/
    # XXX HEROKU:
    url = 'https://mitutoria.herokuapp.com/'
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    # print(hjson.dumpsJSON(response.data)) # NOTE si se usa hay que usar pip install hjson y activar el import
    # return hjson.dumpsJSON(response.data)


@sched.scheduled_job('interval', hours=1, minutes=30)
# @sched.scheduled_job('interval', minutes=1)
def matenimiento_minutes_90():
    with app.app_context():
        mantenimiento_calificaciones_nulas_clock()
        tutoria_calendar_sync_clock()


@sched.scheduled_job('cron', hour='1,3,5,7,9,11,13,15')
def matenimiento_nocturno():
    with app.app_context():
        settings_global = session_sql.query(Settings_Global).first()
        current_date = datetime.date.today()
        if settings_global.mantenimiento_nocturno_date != current_date:  # NOTE asegura que solo lo ejecuta una vez al dia
            mantenimiento_historial_clock()
            mantenimiento_papelera_clock()
            mantenimiento_re_send_email_clock()
            settings_global.mantenimiento_nocturno_date = current_date
            session_sql.commit()


sched.start()
