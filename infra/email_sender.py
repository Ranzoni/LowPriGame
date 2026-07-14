import logging
import os
import smtplib
import time

from email.message import EmailMessage
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def _load_email_config() -> dict[str, str | int]:
    """Carrega e valida as variáveis de ambiente necessárias para envio."""
    load_dotenv()

    config = {
        "host": os.getenv("EMAIL_HOST"),
        "user": os.getenv("EMAIL_USER"),
        "password": os.getenv("EMAIL_PASS"),
        "port": os.getenv("EMAIL_PORT"),
        "retries": os.getenv("EMAIL_MAX_NETWORK_RETRIES"),
        "to": os.getenv("EMAIL_DESTINATION"),
    }

    missing = [key for key, value in config.items() if not value]
    if missing:
        formatted = ", ".join(missing)
        raise ValueError(f"Variáveis de ambiente ausentes: {formatted}")

    try:
        retries = int(config["retries"])
    except ValueError as exc:
        raise ValueError("EMAIL_MAX_NETWORK_RETRIES deve ser um numero inteiro.") from exc

    if retries < 1:
        raise ValueError("EMAIL_MAX_NETWORK_RETRIES deve ser maior ou igual a 1.")

    config["retries"] = retries
    return config


def send_email(subject: str, content: str) -> bool:
    """Envia e-mail de texto simples e retorna status."""
    try:
        config = _load_email_config()

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = config["user"]
        msg["To"] = config["to"]
        msg.set_content(content)

        for attempt in range(1, config["retries"] + 1):
            try:
                with smtplib.SMTP_SSL(config["host"], config["port"], timeout=10) as smtp:
                    smtp.login(config["user"], config["password"])
                    smtp.send_message(msg)
                return True
            except (OSError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as exc:
                if attempt == config["retries"]:
                    logger.exception(
                        "Falha de rede ao enviar e-mail após %s tentativas.",
                        config["retries"],
                    )
                    return False

                logger.warning(
                    "Falha de rede na tentativa %s/%s: %s. Tentando novamente...",
                    attempt,
                    config["retries"],
                    exc,
                )
                time.sleep(attempt)
            except smtplib.SMTPException:
                logger.exception("Falha SMTP não relacionada à rede.")
                return False
    except ValueError as exc:
        logger.error("Configuração de e-mail inválida: %s", exc)
        return False