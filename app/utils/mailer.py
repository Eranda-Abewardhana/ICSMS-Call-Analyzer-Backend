from app.config.config import Configurations
from app.models.send_mail import MailObject
from ssl import create_default_context
from email.mime.text import MIMEText
from smtplib import SMTP


def send_mail(data: dict):
    msg = MailObject(**data)
    message = MIMEText(msg.body, "html")
    message["From"] = Configurations.mail_username
    message["To"] = ", ".join(msg.to)
    message["Subject"] = msg.subject

    ctx = create_default_context()

    try:
        with SMTP(Configurations.mail_host, Configurations.mail_port) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(Configurations.mail_username, Configurations.mail_password)
            server.send_message(message)
            server.quit()
        return True
    except Exception as e:
        print(e)
        return False
