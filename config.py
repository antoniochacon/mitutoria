import io
import locale


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = '00bocata00'


class Server_Config(Config):
    DEBUG = True
    # NOTE Local_Host
    # engine_url = 'postgresql://antonio:bocata@localhost/mitutoria'
    # locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')

    # NOTE Heroku_Host
    engine_url = 'postgres://uensldeziqfoic:6ca0dd91ef4d1a8fac81c53e05c7937b90d96d49d75d97ef48688faac1f37d97@ec2-54-228-182-57.eu-west-1.compute.amazonaws.com:5432/dfblqp0gmhj387'
    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
