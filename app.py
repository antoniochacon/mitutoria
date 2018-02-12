import os
from flask import Flask
from config import *


app = Flask(__name__)
app.config.from_object(Server_Config)
from models import *
from views import *


if __name__ == '__main__':
    with app.app_context():
        Base.metadata.create_all(engine)
    try:
        port = int(os.environ.get("PORT", 5000))
    except:
        port = 5000
    app.run(host='0.0.0.0', port=port)
