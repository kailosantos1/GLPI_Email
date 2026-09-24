"""
Lê e-mails não lidos da caixa de suporte via IMAP (Microsoft 365)
usando autenticação OAuth2 (XOAUTH2) com msal.

Trava 1: só processa e-mails cujo remetente termina com um dos
domínios da lista ALLOWED_DOMAINS (@compasi.com.br ou
@compasiimple.onmicrosoft.com).

Item 7: trunca o corpo em MAX_CORPO_CHARS pra não estourar memória.

Corpo: prioriza text/plain. Se só tiver text/html (comum em e-mails
do Outlook), converte pra texto limpo com BeautifulSoup, removendo
tags <style>, <script> e <head>.
"""

import email
import imaplib
import time
from email.header import decode_header

import msal
from bs4 import BeautifulSoup

from config import (
    IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_FOLDER, ALLOWED_DOMAINS,
    AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET,
)
from logger_setup import get_logger

log = get_logger(__name__)

SCOPES = ["https://outlook.office365.com/.default"]

MAX_CORPO_CHARS = 50_000

_token_cache = {
    "access_token": None,
    "expires_at": 0,
}


# ---------------------------------------------------------------------
# OAuth2 / IMAP
# ---------------------------------------------------------------------
def obter_access_token() -> str:
    """Obtém access_token via client credentials flow usando msal."""
    agora = time.time()
    if _token_cache["access_token"] and agora < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    authority = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    app = msal.ConfidentialClientApplication(
        client_id=AZURE_CLIENT_ID,
        client_credential=AZURE_CLIENT_SECRET,
        authority=authority,
    )

    resultado = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" not in resultado:
        raise RuntimeError(
            f"Falha ao obter token do Azure AD: "
            f"{resultado.get('error')} - {resultado.get('error_description')}"
        )

    _token_cache["access_token"] = resultado["access_token"]
    _token_cache["expires_at"] = agora + resultado.get("expires_in", 3600)

    log.info("Token OAuth2 renovado (expira em %ss)",
             resultado.get("expires_in", 3600))
    return resultado["access_token"]


def _autenticar_xoauth2(conexao: imaplib.IMAP4_SSL, usuario: str, access_token: str):
    auth_string = f"user={usuario}\x01auth=Bearer {access_token}\x01\x01"

    def _callback(challenge):
        return auth_string.encode("utf-8")

    conexao.authenticate("XOAUTH2", _callback)


# ---------------------------------------------------------------------
# Extração de corpo
# ---------------------------------------------------------------------
def _decodificar(valor: str) -> str:
    if not valor:
        return ""
    partes = decode_header(valor)
    texto = ""
    for parte, codificacao in partes:
        if isinstance(parte, bytes):
            texto += parte.decode(codificacao or "utf-8", errors="ignore")
        else:
            texto += parte
    return texto


def _limpar_html(texto_html: str) -> str:
    """
    Remove tags HTML e retorna só o texto limpo.
    - Remove <style>, <script>, <head> (senão viram texto).
    - Usa \n como separador entre blocos.
    - Colapsa linhas vazias.
    """
    soup = BeautifulSoup(texto_html, "html.parser")

    # Remove elementos que não são conteúdo
    for tag in soup(["style", "script", "head", "meta", "title"]):
        tag.decompose()

    # Pega só o texto, com \n entre blocos
    texto = soup.get_text(separator="\n")

    # Normaliza: remove linhas vazias e trailing spaces
    linhas = [ln.strip() for ln in texto.split("\n")]
    linhas = [ln for ln in linhas if ln]

    return "\n".join(linhas)


def _extrair_corpo(msg) -> str:
    """
    Extrai o corpo em texto puro.

    Estratégia:
      1. Se for multipart, busca text/plain E text/html.
      2. Prioriza text/plain se tiver conteúdo real.
      3. Se só tiver HTML, converte com BeautifulSoup.
      4. Trunca em MAX_CORPO_CHARS.
    """
    corpo_plain = ""
    corpo_html = ""

    if msg.is_multipart():
        for parte in msg.walk():
            ctype = parte.get_content_type()
            if ctype == "text/plain" and not corpo_plain:
                payload = parte.get_payload(decode=True)
                if payload:
                    corpo_plain = payload.decode(errors="ignore")
            elif ctype == "text/html" and not corpo_html:
                payload = parte.get_payload(decode=True)
                if payload:
                    corpo_html = payload.decode(errors="ignore")
    else:
        # Não é multipart: só tem um corpo
        ctype = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            texto = payload.decode(errors="ignore")
            if ctype == "text/html":
                corpo_html = texto
            else:
                corpo_plain = texto

    # Prioriza text/plain se tiver conteúdo real
    if corpo_plain.strip():
        corpo = corpo_plain
    elif corpo_html:
        corpo = _limpar_html(corpo_html)
    else:
        corpo = ""

    # Trunca
    if len(corpo) > MAX_CORPO_CHARS:
        log.warning("Corpo do e-mail truncado de %s para %s chars",
                    len(corpo), MAX_CORPO_CHARS)
        corpo = corpo[:MAX_CORPO_CHARS] + "\n\n[...truncado...]"

    return corpo


# ---------------------------------------------------------------------
# Validação de remetente (Trava 1)
# ---------------------------------------------------------------------
def _remetente_valido(endereco: str) -> bool:
    """
    Trava 1: só aceita e-mails de um dos domínios permitidos.
    A lista está em ALLOWED_DOMAINS (config.py).
    """
    if not ALLOWED_DOMAINS:
        return True  # sem trava (não recomendado)
    if not endereco:
        return False

    endereco_lower = endereco.lower().strip()
    return any(
        endereco_lower.endswith(dominio.lower())
        for dominio in ALLOWED_DOMAINS
    )


# ---------------------------------------------------------------------
# Busca de e-mails
# ---------------------------------------------------------------------
def buscar_emails_novos() -> list:
    """
    Conecta via IMAP no M365 com OAuth2 e pega os e-mails não lidos.
    Só devolve e-mails cujo remetente é de um dos domínios internos.
    """
    resultado = []

    access_token = obter_access_token()

    conexao = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    try:
        _autenticar_xoauth2(conexao, IMAP_USER, access_token)
        conexao.select(IMAP_FOLDER)

        status, mensagens = conexao.search(None, "UNSEEN")
        if status != "OK":
            log.warning("IMAP search retornou %s", status)
            return resultado

        for num in mensagens[0].split():
            status, dados = conexao.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(dados[0][1])
            remetente = email.utils.parseaddr(msg.get("From"))[1]

            if not _remetente_valido(remetente):
                log.warning("BLOQUEADO: e-mail de '%s' fora dos domínios %s",
                            remetente, ALLOWED_DOMAINS)
                continue

            assunto = _decodificar(msg.get("Subject", ""))
            corpo = _extrair_corpo(msg)

            resultado.append({
                "remetente": remetente,
                "assunto": assunto,
                "corpo": corpo.strip(),
            })

        if resultado:
            log.info("%s e-mail(s) novo(s) encontrado(s)", len(resultado))
    finally:
        try:
            conexao.close()
        except Exception:
            pass
        conexao.logout()

    return resultado