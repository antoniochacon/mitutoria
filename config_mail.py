from app import app
from flask_mail import Mail, Message

mail = Mail()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mitutoria.email@gmail.com'
app.config['MAIL_PASSWORD'] = '##bocata##'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_SUPPRESS_SEND'] = False  # False para activar el envio de email.
