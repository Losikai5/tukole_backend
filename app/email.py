from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Template

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parent

mail_config = ConnectionConfig(
	MAIL_USERNAME=settings.MAIL_USERNAME,
	MAIL_PASSWORD=settings.MAIL_PASSWORD,
	MAIL_FROM=settings.MAIL_FROM,
	MAIL_PORT=settings.MAIL_PORT,
	MAIL_SERVER=settings.MAIL_SERVER,
	MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
	MAIL_STARTTLS=settings.MAIL_STARTTLS,
	MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
	USE_CREDENTIALS=settings.USE_CREDENTIALS,
	VALIDATE_CERTS=settings.VALIDATE_CERTS,
	TEMPLATE_FOLDER=Path(BASE_DIR, "templates"),
)

mail = FastMail(config=mail_config)


def create_message(recipients: list[str], subject: str, body: str) -> MessageSchema:
	return MessageSchema(
		recipients=recipients,
		subject=subject,
		body=body,
		subtype=MessageType.html,
	)


async def send_html_email(recipients: list[str], subject: str, body: str):
	message = create_message(recipients=recipients, subject=subject, body=body)
	await mail.send_message(message)


def render_template(template_name: str, context: dict) -> str:
	template_path = Path(BASE_DIR, "templates", template_name)
	template_content = template_path.read_text(encoding="utf-8")
	template = Template(template_content)
	return template.render(**context)


async def send_verification_email(recipient: str, verification_link: str):
	body = render_template(
		template_name="email_verification.html",
		context={"verification_link": verification_link},
	)
	await send_html_email(
		recipients=[recipient],
		subject="Verify your email",
		body=body,
	)
