class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = '00bocata00'


class Server_Config(Config):
    # NOTE Local_Host
    # DEBUG = True
    # engine_url = 'postgresql://antonio:bocata@localhost/mitutoria'

    # NOTE Heroku_Host
    DEBUG = False
    engine_url = 'postgres://lgiizrlnnxrxma:d2ec0030ef9a5b8ba5fde3a4a43abd298772f82c201c7d0824bdd7b22ee43c18@ec2-54-247-92-185.eu-west-1.compute.amazonaws.com:5432/d4eji6rllseihn'
