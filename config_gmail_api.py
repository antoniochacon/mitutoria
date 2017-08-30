from app import app
from config_parametros import *
import config_parametros

import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
# ********************
from oauth2client.client import flow_from_clientsecrets

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'static/credentials/client_secret.json'
APPLICATION_NAME = 'mi tutoria'


def get_credentials():

    # NOTE si no existe el archivo 'gmail_credentials.json' lo crea. Hay que hacerlo en modo local y luego subirlo al servidor (NO es capaz de hacerlo directamente en Heroku)
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


def main_test():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])
