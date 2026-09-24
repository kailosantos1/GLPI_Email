"""
Envia e-mails via SMTP do Microsoft 365 usando OAuth2 (XOAUTH2).

Reutiliza o mesmo access token do IMAP (do email_reader). O token
tem escopo de SMTP.SendAsApp porque a permissão foi adicionada no
Azure AD + concedida no Exchange (Add-RecipientPermission).
"""

import base64
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import IMAP_SERVER, REMETENTE_NOME, REMETENTE_EMAIL
from email_reader import obter_access_token
from logger_setup import get_logger

log = get_logger(__name__)

SMTP_HOST = IMAP_SERVER
SMTP_PORT = 587


def enviar_email(destinatario: str, assunto: str, corpo_html: str,
                 corpo_texto: str = None) -> bool:
    """
    Envia um e-mail HTML via SMTP OAuth2.

    - destinatario: e-mail do destinatário
    - assunto: string
    - corpo_html: corpo em HTML
    - corpo_texto: (opcional) fallback em texto puro (pra clientes
      que não renderizam HTML)

    Retorna True se enviou, False se falhou.
    """
    try:
        token = obter_access_token()
    except Exception as e:
        log.error("Falha ao obter token pro SMTP: %s", e)
        return False

    # Monta a mensagem MIME (multipart: texto + html)
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{REMETENTE_NOME} <{REMETENTE_EMAIL}>"
    msg["To"] = destinatario
    msg["Subject"] = assunto

    # Fallback em texto puro
    if not corpo_texto:
        # Remove tags HTML pra gerar versão texto
        corpo_texto = re.sub(r"<[^>]+>", "", corpo_html)
        corpo_texto = re.sub(r"\n{3,}", "\n\n", corpo_texto).strip()

    msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    # Auth XOAUTH2
    auth_string = f"user={REMETENTE_EMAIL}\x01auth=Bearer {token}\x01\x01"
    auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("ascii")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()

            code, resp = smtp.docmd("AUTH", "XOAUTH2 " + auth_b64)
            if code != 235:
                log.error("Falha na autenticação SMTP: %s %s", code, resp)
                return False

            smtp.sendmail(
                REMETENTE_EMAIL,
                [destinatario],
                msg.as_string().encode("utf-8"),
            )

        log.info("E-mail enviado pra %s | assunto='%s'",
                 destinatario, assunto)
        return True

    except Exception as e:
        log.error("Erro ao enviar e-mail pra %s: %s", destinatario, e)
        return False