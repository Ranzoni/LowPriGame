import logging
import smtplib
import time

from email.message import EmailMessage

from infra.environment_variables import load_config


logger = logging.getLogger(__name__)

def send_email(subject: str, content: str) -> bool:
    """Envia e-mail de texto simples e retorna status."""
    try:
        config = load_config({
            "host": "EMAIL_HOST",
            "user": "EMAIL_USER",
            "password": "EMAIL_PASS",
            "port": "EMAIL_PORT",
            "retries": "EMAIL_MAX_NETWORK_RETRIES",
            "to": "EMAIL_DESTINATION",
        })

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = config["user"]
        msg["To"] = config["to"]
        msg.set_content(content)

        retries = int(config["retries"])

        for attempt in range(1, retries + 1):
            try:
                with smtplib.SMTP_SSL(config["host"], config["port"], timeout=10) as smtp:
                    smtp.login(config["user"], config["password"])
                    smtp.send_message(msg)
                return True
            except (OSError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as exc:
                if attempt == retries:
                    logger.exception(
                        "Falha de rede ao enviar e-mail após %s tentativas.",
                        retries,
                    )
                    return False

                logger.warning(
                    "Falha de rede na tentativa %s/%s: %s. Tentando novamente...",
                    attempt,
                    retries,
                    exc,
                )
                time.sleep(attempt)
            except smtplib.SMTPException:
                logger.exception("Falha SMTP não relacionada à rede.")
                return False
    except ValueError as exc:
        logger.error("Configuração de e-mail inválida: %s", exc)
        return False