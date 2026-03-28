from asgiref.sync import async_to_sync
from celery import Celery

from app.core.config import settings
from app.email import create_message, mail, render_template


broker = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

c_app = Celery("tukole_backend")
c_app.conf.update(
	broker_url=broker,
	result_backend=broker,
	broker_connection_retry_on_startup=True,
)


@c_app.task(name="app.celery_task.send_email_task")
def send_email_task(recipients: list[str], subject: str, body: str) -> None:
	message = create_message(recipients=recipients, subject=subject, body=body)
	async_to_sync(mail.send_message)(message)


@c_app.task(name="app.celery_task.send_verification_email_task")
def send_verification_email_task(recipient: str, verification_link: str) -> None:
	body = render_template(
		template_name="email_verification.html",
		context={"verification_link": verification_link},
	)
	send_email_task([recipient], "Verify your email", body)
