from app import app
from functions import *
import functions

from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()


# @sched.scheduled_job('interval', minutes=1)
# def timed_job():
#     with app.app_context():
#         mantenimiento_historial_clock()
#         mantenimiento_papelera_clock()
#         mantenimiento_re_send_email_clock()

@sched.scheduled_job('cron', hour=4, minute=5)
def matenimiento_nocturno():
    with app.app_context():
        mantenimiento_historial_clock()
        mantenimiento_papelera_clock()
        mantenimiento_re_send_email_clock()


@sched.scheduled_job('cron', day_of_week='mon-fri', hour=17)
def scheduled_job():
    print('This job is run every weekday at 5pm.')


sched.start()
