from app import app
from functions import *
import functions

from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def matenimiento_hour_1():
    with app.app_context():
        tutoria_calendar_sync_clock()


@sched.scheduled_job('cron', hour=1)
def matenimiento_nocturno():
    with app.app_context():
        mantenimiento_historial_clock()
        mantenimiento_papelera_clock()
        mantenimiento_re_send_email_clock()


sched.start()
