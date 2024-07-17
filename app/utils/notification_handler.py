import logging
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from smtplib import SMTP_SSL

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from app.config.config import Configurations
from app.database.database_connector import DatabaseConnector
from app.models.call_notification import CallNotification
from app.models.mail_object import MailObject

load_dotenv()


class NotificationHandler:
    notification_db = DatabaseConnector("notifications")
    action_link = Configurations.webapp_url + "/call/dashboard"

    @classmethod
    def __send_email(cls, mail_obj: MailObject):
        try:
            message = MIMEMultipart()
            message["From"] = formataddr(("SentiView", Configurations.mail_username))
            message["To"] = ", ".join(mail_obj.to)
            message["Subject"] = mail_obj.subject

            utils_dir = os.path.dirname(__file__)
            app_dir = os.path.dirname(utils_dir)
            template_dir = os.path.join(app_dir, 'templates')

            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(mail_obj.template)

            # Render the template with the provided context
            html_content = template.render(mail_obj.context)

            # Attach the HTML content
            message.attach(MIMEText(html_content, "html"))

            with SMTP_SSL(Configurations.mail_host, Configurations.mail_port) as server:
                server.login(Configurations.mail_username, Configurations.mail_password)
                logging.info("Sending the email.")
                server.send_message(message)
                server.quit()
                logging.info("Email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    @classmethod
    def send_keyword_notification(cls, keywords: list[str], is_email=True, is_push=True, receivers: list[str] = []):
        try:
            message_body = f"Below keywords are recently detected in call recordings. Keywords: {', '.join(keywords)}"

            if is_email and len(receivers) > 0:
                mail_obj = MailObject(
                    to=receivers,
                    subject="SentiView Call Analytics - Keywords Detected In Calls",
                    template_name="keyword_notification.html",
                    context={"keywords": ', '.join(keywords), "action_link": cls.action_link}
                )
                cls.__send_email(mail_obj)

            if is_push:
                notification = CallNotification(
                    title="Keywords Detected In Calls",
                    description=message_body,
                    isRead=False,
                    datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                cls.notification_db.add_entity(notification)

        except Exception as e:
            logging.error(f"Failed to send keyword notifications: {e}")

    @classmethod
    def send_analysis_success_notification(cls, count: int):
        notification = CallNotification(
            title="Call Analysis Successful",
            description=f"All {count} call recordings have been successfully analyzed and saved to the database.",
            isRead=False,
            datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        cls.notification_db.add_entity(notification)

    @classmethod
    def send_analysis_failed_notification(cls, count: int):
        notification = CallNotification(
            title="Call Analysis Failed",
            description=f"{count} call recordings are failed to analyze.",
            isRead=False,
            datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        cls.notification_db.add_entity(notification)

    @classmethod
    async def send_below_sentiment_notification(cls, lower_limit: float, current_score: float, is_email=True,
                                                is_push=True, receivers: list[str] = []):
        if lower_limit > current_score:
            try:
                message_body = (
                    f"Overall call analytics sentiment score has gone below the threshold: {lower_limit}. "
                    f"It has been recorded as {current_score}. Note that the above sentiment score is "
                    f"based on the data with last month.")

                if is_email and len(receivers) > 0:
                    mail_obj = MailObject(
                        to=receivers,
                        subject="SentiView Call Analytics - Low Overall Sentiment Score Alert",
                        template="low_score.html",
                        context={"low": lower_limit, "current": round(current_score, 2), "action_link": cls.action_link}
                    )
                    cls.__send_email(mail_obj)

                if is_push:
                    notification = CallNotification(
                        title="Low Overall Sentiment Score Detected",
                        description=message_body,
                        isRead=False,
                        datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    )
                    await cls.notification_db.add_entity_async(notification)
            except Exception as e:
                logging.error(f"Failed to send lower sentiment threshold notifications: {e}")

    @classmethod
    async def send_above_sentiment_notification(cls, upper_limit: float, current_score: float, is_email=True,
                                                is_push=True, receivers: list[str] = []):
        if upper_limit < current_score:
            try:
                message_body = (
                    f"Overall call analytics sentiment score has gone above the threshold: {upper_limit}. "
                    f"It has been recorded as {current_score}. Note that the above sentiment score is "
                    f"based on the data with last month.")

                if is_email and len(receivers) > 0:
                    mail_obj = MailObject(
                        to=receivers,
                        subject="SentiView Call Analytics - High Overall Sentiment Score Alert",
                        template="high_score.html",
                        context={"high": upper_limit, "current": round(current_score, 2),
                                 "action_link": cls.action_link}
                    )
                    cls.__send_email(mail_obj)

                if is_push:
                    notification = CallNotification(
                        title="High Overall Sentiment Score Detected",
                        description=message_body,
                        isRead=False,
                        datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    )
                    await cls.notification_db.add_entity_async(notification)
            except Exception as e:
                logging.error(f"Failed to send lower sentiment threshold notifications: {e}")
