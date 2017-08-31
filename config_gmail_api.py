from app import app
from config_parametros import *
import config_parametros

import httplib2
import os
import oauth2client
from oauth2client import client, tools
from oauth2client.file import Storage
import base64
from email import encoders
from email.message import Message
from email.mime.text import MIMEText
# *************************************************
from apiclient import errors, discovery  # needed for gmail service
from apiclient.http import BatchHttpRequest

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'static/credentials/client_secret.json'
APPLICATION_NAME = 'mi tutoria'

# ****************************************


def create_message_and_send(service, sender, to, subject, message_text):
    message = create_message(sender, to, subject, message_text)
    send_message(service, "me", message, message_text)


def get_credentials():

    # NOTE [NO BORRAR] si no existe el archivo 'gmail_credentials.json' lo crea. Hay que hacerlo en modo local y luego subirlo al servidor (NO es capaz de hacerlo directamente en Heroku)
    # NOTE activarlo en caso de necesitar una nueva credential por haber modificado algo como por ejemplo el SCOPE
    # credential_path = 'static/credentials/gmail_credentials.json'
    # store = Storage(credential_path)
    # credentials = store.get()
    # if not credentials or credentials.invalid:
    #     flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    #     flow.user_agent = APPLICATION_NAME
    #     if flags:
    #         credentials = tools.run_flow(flow, store, flags)

    # NOTE suponiendo que tengo el archivo 'gmail_credentials.json' me limito a leerlo.
    store = Storage('static/credentials/gmail_credentials.json')
    credentials = store.get()
    return credentials


def create_message(sender, to, subject, message_text):
    # Create message container
    message = MIMEText(message_text, 'html')
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject

    # NOTE variable duplicada, no se si la reutiliza o que
    raw_message = base64.urlsafe_b64encode(message.as_bytes())
    raw_message = raw_message.decode()
    body = {'raw': raw_message}
    return body


def send_message(service, user_id, body, message_text):
    try:
        message_sent = (service.users().messages().send(userId=user_id, body=body).execute())
        # message_id = message_sent['id']
        # print('email enviado_id:', message_id)
    except errors.HttpError as error:
        print(f'An error occurred: {error}')
