from fastapi import APIRouter, BackgroundTasks

from app.utils.mailer import send_mail
from app.models.action_result import ActionResult
from app.models.send_mail import mail_body

email_router = APIRouter()


@email_router.post("/send-reset-mail", response_model=ActionResult)
async def send_reset_mail(mails: mail_body, task:BackgroundTasks):
    data = mails.dict()
    task.add_task(send_mail, data)
    return True
