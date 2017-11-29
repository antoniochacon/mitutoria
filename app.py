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

        if not settings_admin():
            settings_admin_add = Settings_Admin(diferencial=20, periodo_recent=30)
            session_sql.add(settings_admin_add)
            session_sql.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
