import logging
from datetime import datetime
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from dotenv import load_dotenv

from app.config.config import Configurations
from app.database.db import DatabaseConnector
from app.models.call_notification import CallNotification
from app.models.send_mail import MailObject

load_dotenv()


class NotificationHandler:
    notification_db = DatabaseConnector("notifications")

    @classmethod
    def __send_email(cls, mail_obj: MailObject):
        message = MIMEText(mail_obj.body, "html")
        message["From"] = Configurations.mail_username
        message["To"] = ", ".join(mail_obj.to)
        message["Subject"] = mail_obj.subject
        try:
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
                    subject="SentiView - Keywords Detected In Calls",
                    body=message_body
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
    async def send_below_sentiment_notification(cls, lower_threshold: float, current_score: float, is_email=True,
                                                is_push=True, receivers: list[str] = []):
        if lower_threshold > current_score:
            try:
                message_body = (
                    f"Overall call analytics sentiment score has gone below the threshold: {lower_threshold}. "
                    f"It has been recorded as {current_score}. Note that the above sentiment score is "
                    f"based on the data with last month.")

                if is_email and len(receivers) > 0:
                    mail_obj = MailObject(
                        to=receivers,
                        subject="SentiView - Low Overall Sentiment Score Alert",
                        body=message_body
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
    async def send_above_sentiment_notification(cls, upper_threshold: float, current_score: float, is_email=True,
                                                is_push=True, receivers: list[str] = []):
        if upper_threshold < current_score:
            try:
                message_body = (
                    f"Overall call analytics sentiment score has gone above the threshold: {upper_threshold}. "
                    f"It has been recorded as {current_score}. Note that the above sentiment score is "
                    f"based on the data with last month.")

                if is_email and len(receivers) > 0:
                    mail_obj = MailObject(
                        to=receivers,
                        subject="SentiView - High Overall Sentiment Score Alert",
                        body=message_body
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
