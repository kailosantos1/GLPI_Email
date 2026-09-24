"""
Loop principal com:
  - Item 1: circuit breaker (para após N erros seguidos)
  - Item 2: salva e-mails com erro em disco pra análise manual
  - Item 3: logging em arquivo (bot.log)
  - Item 7: corpo truncado (já tratado no email_reader)
  - Abordagem D: Gemini decide se é chamado ou não antes de classificar

Fase 1: pós-processamento (requerente + limpeza de atores) no glpi_client.
Fase 2: auto-reply HTML de confirmação pro solicitante.
"""

import html
import json
import os
import re
import signal
import sys
import time

from config import POLL_INTERVAL_SECONDS
from email_reader import buscar_emails_novos
from email_sender import enviar_email
from glpi_client import GLPIClient
from ad_parser import extrair_info_dn
from triagem import classificar_email, classificar_problema, e_chamado
from logger_setup import configurar_logging, get_logger


# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
configurar_logging()
log = get_logger(__name__)

PASTA_ERROS = "emails_com_erro"
MAX_ERROS_CONSECUTIVOS = 5

COR_TEXTO_GLPI = "#85bd81"

NOMES_FORMS = {
    "manutencao": "Manutenção",
    "flexsmart":  "FlexSmart",
}

_erros_consecutivos = 0
_parar = False


def _handler_saida(sig, frame):
    global _parar
    log.info("Sinal %s recebido, encerrando...", sig)
    _parar = True


signal.signal(signal.SIGINT, _handler_saida)
signal.signal(signal.SIGTERM, _handler_saida)


# ---------------------------------------------------------------------
# Limpeza do corpo do e-mail
# ---------------------------------------------------------------------
def _limpar_corpo(corpo: str) -> str:
    if not corpo:
        return ""
    corpo = corpo.replace("\r\n", "\n").replace("\r", "\n")
    corpo = "\n".join(linha.rstrip() for linha in corpo.split("\n"))
    corpo = re.sub(r"\n{3,}", "\n\n", corpo)
    corpo = corpo.strip()
    corpo = html.escape(corpo)
    return corpo


def montar_descricao(email_msg: dict, info: dict) -> str:
    corpo_limpo = _limpar_corpo(email_msg["corpo"]) or "(corpo vazio)"
    corpo_html = corpo_limpo.replace("\n", "<br>")
    return (
        f'<div style="color: {COR_TEXTO_GLPI}; font-family: sans-serif; '
        'font-size: 14px; margin: 0; padding: 0;">'
        f'{corpo_html}'
        '</div>'
    )


# ---------------------------------------------------------------------
# Template HTML do auto-reply
# ---------------------------------------------------------------------
def montar_html_confirmacao(nome: str, ticket_id, tipo: str,
                            unidade: str, canal: str) -> str:
    nome = nome or "Colaborador(a)"
    unidade_fmt = unidade.capitalize() if unidade else "—"
    ticket_str = f"#{ticket_id}" if ticket_id else "—"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f4f6f8; padding: 30px 15px;">
    <tr>
      <td align="center">

        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width:600px; background-color:#ffffff; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow:hidden;">

          <tr>
            <td style="background-color:#ffffff; padding: 28px 30px; border-bottom: 3px solid #4caf50;">
              <h1 style="margin:0; font-size:20px; font-weight:600; color:#000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                ✅ Chamado aberto com sucesso
              </h1>
              <p style="margin:6px 0 0 0; font-size:14px; color:#000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                Sua solicitação foi registrada no sistema de TI
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding: 28px 30px; color:#000000; font-size:14px; line-height:1.6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">

              <p style="margin:0 0 18px 0; color:#000000;">Olá <strong>{nome}</strong>,</p>

              <p style="margin:0 0 18px 0; color:#000000;">
                Recebemos sua solicitação e ela já foi registrada no nosso sistema de atendimento.
                Em breve um técnico irá analisar e entrar em contato.
              </p>

              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f8fafb; border-left:4px solid #4caf50; border-radius:4px; margin: 20px 0;">
                <tr>
                  <td style="padding: 16px 20px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                      <tr>
                        <td style="padding: 4px 0; font-size:13px; color:#666666; width:120px;">Número</td>
                        <td style="padding: 4px 0; font-size:13px; color:#000000; font-weight:600;">{ticket_str}</td>
                      </tr>
                      <tr>
                        <td style="padding: 4px 0; font-size:13px; color:#666666;">Tipo</td>
                        <td style="padding: 4px 0; font-size:13px; color:#000000;">{tipo}</td>
                      </tr>
                      <tr>
                        <td style="padding: 4px 0; font-size:13px; color:#666666;">Unidade</td>
                        <td style="padding: 4px 0; font-size:13px; color:#000000;">{unidade_fmt}</td>
                      </tr>
                      <tr>
                        <td style="padding: 4px 0; font-size:13px; color:#666666;">Canal de contato</td>
                        <td style="padding: 4px 0; font-size:13px; color:#000000;">{canal}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <p style="margin: 20px 0 0 0; font-size:13px; color:#666666;">
                Se precisar adicionar mais informações, basta responder este e-mail
                ou entrar em contato pelo canal escolhido.
              </p>

            </td>
          </tr>

          <tr>
            <td style="background-color:#f8fafb; padding: 18px 30px; border-top:1px solid #e8ecef; text-align:center; font-size:12px; color:#999999; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
              <p style="margin:0;">Equipe de TI · COMPASI Implementos Rodoviários</p>
              <p style="margin:6px 0 0 0;">Este é um e-mail automático. Não responda diretamente.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ---------------------------------------------------------------------
# Salvar e-mail com erro
# ---------------------------------------------------------------------
def salvar_email_com_erro(email_msg: dict, motivo: str):
    os.makedirs(PASTA_ERROS, exist_ok=True)
    timestamp = int(time.time())
    nome = f"{timestamp}_{email_msg['remetente'].replace('@', '_at_')}.json"
    caminho = os.path.join(PASTA_ERROS, nome)

    dados = {
        "motivo": motivo,
        "timestamp": timestamp,
        "email": email_msg,
    }
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        log.info("E-mail com erro salvo em %s", caminho)
    except Exception as e:
        log.error("Falha ao salvar e-mail com erro: %s", e)


# ---------------------------------------------------------------------
# Processamento de 1 e-mail
# ---------------------------------------------------------------------
def processar_email(glpi: GLPIClient, email_msg: dict):
    remetente = email_msg["remetente"]
    corpo = email_msg["corpo"] or email_msg["assunto"]

    # ---- Abordagem D: isso é um chamado de verdade? ----
    if not e_chamado(corpo):
        log.info("IGNORADO: '%s' — não parece chamado de TI", remetente)
        return

    # ---- Trava 2: usuário precisa existir no GLPI ----
    usuario = glpi.buscar_usuario_por_email(remetente)
    if usuario is None:
        log.warning("BLOQUEADO: '%s' não existe no GLPI", remetente)
        return

    dn = glpi.extrair_dn(usuario)
    if not dn:
        log.warning("BLOQUEADO: '%s' sem DN sincronizado", remetente)
        return

    info = extrair_info_dn(dn)
    if not info["unidade"]:
        log.warning("BLOQUEADO: unidade de '%s' não identificada", remetente)
        return

    classificacao = classificar_email(corpo)
    form_chave = classificacao["formulario"]

    if not form_chave:
        log.info("IGNORADO: '%s' não classificável (%s)",
                 remetente, classificacao["detalhe"])
        return

    log.info("CLASSIFICADO: form=%s método=%s (%s)",
             form_chave, classificacao["metodo"], classificacao["detalhe"])

    tipo_problema = None
    if form_chave == "manutencao":
        tipo_problema = classificar_problema(corpo)

    descricao = montar_descricao(email_msg, info)

    # ---- Cria o chamado ----
    resultado = glpi.criar_chamado(
        form_chave=form_chave,
        descricao=descricao,
        unidade=info["unidade"],
        email_solicitante=remetente,
        tipo_problema=tipo_problema,
    )

    formanswer_id = resultado.get("id")
    ticket_id = resultado.get("ticket_id")

    log.info("CHAMADO CRIADO: %s | form=%s | unidade=%s | tipo=%s | "
             "formanswer=%s | ticket=%s",
             remetente, form_chave, info["unidade"], tipo_problema,
             formanswer_id, ticket_id)

    # ---- Envia auto-reply de confirmação ----
    try:
        id_para_email = ticket_id or formanswer_id

        nome = info.get("nome") or remetente.split("@")[0]
        nome_form = NOMES_FORMS.get(form_chave, form_chave)
        assunto = f"[GLPI #{id_para_email}] Chamado aberto com sucesso"

        html_corpo = montar_html_confirmacao(
            nome=nome,
            ticket_id=id_para_email,
            tipo=nome_form,
            unidade=info["unidade"],
            canal="Microsoft Teams",
        )
        enviado = enviar_email(remetente, assunto, html_corpo)
        if enviado:
            log.info("Auto-reply enviado pra %s", remetente)
        else:
            log.warning("Auto-reply NÃO enviado pra %s", remetente)
    except Exception as e:
        log.error("Erro ao enviar auto-reply: %s", e)


# ---------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------
def main():
    global _erros_consecutivos

    glpi = GLPIClient()
    glpi.iniciar_sessao()
    log.info("=== Bot iniciado. Polling a cada %ss ===", POLL_INTERVAL_SECONDS)

    try:
        while not _parar:
            try:
                emails = buscar_emails_novos()
                _erros_consecutivos = 0
            except Exception as e:
                _erros_consecutivos += 1
                log.error("Falha ao buscar e-mails (%s/%s): %s",
                          _erros_consecutivos, MAX_ERROS_CONSECUTIVOS, e)
                if _erros_consecutivos >= MAX_ERROS_CONSECUTIVOS:
                    log.critical("Muitos erros seguidos no IMAP. Encerrando.")
                    raise
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            for email_msg in emails:
                if _parar:
                    break
                try:
                    processar_email(glpi, email_msg)
                    _erros_consecutivos = 0
                except Exception as e:
                    log.error("Erro ao processar e-mail de %s: %s",
                              email_msg["remetente"], e, exc_info=True)
                    salvar_email_com_erro(email_msg, str(e))

            if not _parar:
                time.sleep(POLL_INTERVAL_SECONDS)

    finally:
        glpi.encerrar_sessao()
        log.info("=== Bot encerrado ===")


if __name__ == "__main__":
    main()