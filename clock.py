from app import app
from functions import *
import functions

from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()


# ***************************************************************
# oauth2_credentials (necesario para gmail y calendar api)
# ***************************************************************
# import threading  # NOTE mail threading
# import httplib2
# import os
# import json
# import oauth2client
# from oauth2client import client, tools
# import base64
# from email import encoders
# from email.message import Message
# from email.mime.text import MIMEText
# from apiclient import discovery
# ----------------------------------------------------------------
# oauth2_credentials [FIN]
# ----------------------------------------------------------------
# import datetime
# import time


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    with app.app_context():
        mantenimiento_historial_clock()
        mantenimiento_papelera_clock()
        mantenimiento_re_send_email_clock()


@sched.scheduled_job('cron', day_of_week='mon-fri', hour=17)
def scheduled_job():
    print('This job is run every weekday at 5pm.')


sched.start()
