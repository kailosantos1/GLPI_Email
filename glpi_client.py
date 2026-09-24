"""
Cliente GLPI + Formcreator com suporte a múltiplos formulários.

- manutencao (id=1): tipo_solicitacao, equipamento, local, filial, etc.
- flexsmart  (id=5): tipo_atendimento, qual_liberacao_sistema, etc.

Fase 1: depois de criar o FormAnswer, o client:
  1. Descobre o Ticket real (via Item_Ticket)
  2. Adiciona o solicitante como Requerente
  3. Remove o bot (GLPI_BOT_USER_ID) de TODOS os atores

O método criar_chamado() retorna o dict do FormAnswer COM uma chave
extra "ticket_id" contendo o ID do ticket real.
"""

import requests

from config import (
    GLPI_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN, GLPI_BOT_USER_ID,
    FORM_ID_MANUTENCAO, FORM_ID_FLEXSMART,
    CAMPO_MANUT_TIPO_SOLICITACAO, CAMPO_MANUT_DESCRICAO,
    CAMPO_MANUT_URGENCIA, CAMPO_MANUT_LOCAL_SOLICITACAO,
    CAMPO_MANUT_FILIAL, CAMPO_MANUT_EQUIPAMENTO,
    CAMPO_MANUT_CANAL_CONTATO, CAMPO_MANUT_EMAIL_TEAMS,
    CAMPO_MANUT_SISTEMA_PROBLEMA,
    CAMPO_FLEX_TIPO_ATENDIMENTO, CAMPO_FLEX_QUAL_LIBERACAO_SISTEMA,
    CAMPO_FLEX_DESCRICAO, CAMPO_FLEX_CANAL_CONTATO,
    CAMPO_FLEX_EMAIL_TEAMS, CAMPO_FLEX_URGENCIA,
    CANAL_CONTATO_PADRAO, URGENCIA_PADRAO,
)
from logger_setup import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------
# Mapeamentos
# ---------------------------------------------------------------------
_TIPO_PARA_SOLICITACAO = {
    "Impressora":   "Manutenção de Equipamentos",
    "Hardware":     "Manutenção de Equipamentos",
    "Rede":         "Manutenção de Sistemas",
    "Email":        "Manutenção de Sistemas",
    "Desempenho":   "Manutenção de Sistemas",
    "Acesso/Senha": "Acessos",
    "Outro":        "Manutenção de Equipamentos",
}

_TIPO_PARA_EQUIPAMENTO = {
    "Impressora":   "Periféricos (Webcam/Impressora)",
    "Hardware":     "Computador/Hardware",
    "Rede":         "Internet/Páginas da Web",
    "Email":        "Internet/Páginas da Web",
    "Desempenho":   "Sistemas/Softwares",
    "Acesso/Senha": "Sistemas/Softwares",
    "Outro":        "Computador/Hardware",
}

_UNIDADE_PARA_FILIAL = {
    "MARAVILHA":  "Maravilha",
    "LAGES":      "Lages",
    "VIDEIRA":    "Videira",
    "CONCORDIA":  "Concordia",
    "CATANDUVAS": "Catanduvas",
}

_URGENCIA_PARA_NUMERO = {
    "muito baixa": 1,
    "baixa":       2,
    "media":       3,
    "média":       3,
    "alta":        4,
    "muito alta":  5,
}


def _verificar_resposta(resp):
    if resp.status_code >= 400:
        log.error("GLPI %s %s -> %s | Corpo: %s",
                  resp.request.method, resp.url, resp.status_code, resp.text)
    resp.raise_for_status()


class GLPIClient:
    def __init__(self):
        self.session_token = None

    # ------------------------------------------------------------------
    # Sessão
    # ------------------------------------------------------------------
    def iniciar_sessao(self):
        resp = requests.post(
            f"{GLPI_URL}/initSession",
            headers={
                "Content-Type": "application/json",
                "App-Token": GLPI_APP_TOKEN,
                "Authorization": f"user_token {GLPI_USER_TOKEN}",
            },
            timeout=15,
        )
        _verificar_resposta(resp)
        self.session_token = resp.json()["session_token"]
        log.info("Sessão GLPI iniciada")

    def encerrar_sessao(self):
        if not self.session_token:
            return
        try:
            requests.get(f"{GLPI_URL}/killSession", headers=self._headers(), timeout=15)
            log.info("Sessão GLPI encerrada")
        except Exception as e:
            log.warning("Falha ao encerrar sessão GLPI: %s", e)
        self.session_token = None

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "App-Token": GLPI_APP_TOKEN,
            "Session-Token": self.session_token,
        }

    # ------------------------------------------------------------------
    # Busca de usuário por e-mail
    # ------------------------------------------------------------------
    def buscar_usuario_por_email(self, email: str):
        """
        Busca o usuário no GLPI pelo e-mail cadastrado.
        searchtype='contains' porque 'equals' é bugado no GLPI.
        """
        resp = requests.get(
            f"{GLPI_URL}/search/User",
            headers=self._headers(),
            params={
                "criteria[0][field]": 5,
                "criteria[0][searchtype]": "contains",
                "criteria[0][value]": email,
                "forcedisplay[0]": 2,
                "forcedisplay[1]": 1,
                "range": "0-1",
            },
            timeout=15,
        )
        _verificar_resposta(resp)
        data = resp.json()

        log.info("Busca por '%s' retornou %s resultado(s)",
                 email, data.get("count", 0))

        if not data.get("data"):
            return None

        linha = data["data"][0]
        usuario_id = linha.get("2")
        if not usuario_id:
            log.warning("Coluna 2 (ID) vazia: %s", linha)
            return None

        return self.buscar_usuario_por_id(usuario_id)

    def buscar_usuario_por_id(self, usuario_id) -> dict:
        resp = requests.get(
            f"{GLPI_URL}/User/{usuario_id}",
            headers=self._headers(),
            timeout=15,
        )
        _verificar_resposta(resp)
        return resp.json()

    @staticmethod
    def extrair_dn(usuario: dict):
        for chave in ("user_dn", "9", "ldap_dn", "dn"):
            if usuario.get(chave):
                return usuario[chave]
        return None

    # ------------------------------------------------------------------
    # Helpers do Formcreator
    # ------------------------------------------------------------------
    def _get_form_questions(self, form_id: int) -> list:
        questions = []
        try:
            resp = requests.get(
                f"{GLPI_URL}/PluginFormcreatorForm/{form_id}/PluginFormcreatorSection",
                headers=self._headers(),
                params={"range": "0-100"},
                timeout=10,
            )
            if resp.status_code != 200:
                return questions

            sections = resp.json()
            if not isinstance(sections, list):
                sections = [sections]

            for sec in sections:
                sec_id = sec.get("id")
                if not sec_id:
                    continue
                resp_q = requests.get(
                    f"{GLPI_URL}/PluginFormcreatorSection/{sec_id}/PluginFormcreatorQuestion",
                    headers=self._headers(),
                    params={"range": "0-100"},
                    timeout=10,
                )
                if resp_q.status_code == 200:
                    q_data = resp_q.json()
                    if not isinstance(q_data, list):
                        q_data = [q_data]
                    questions.extend(q_data)
        except Exception as e:
            log.error("Erro ao consultar perguntas do form %s: %s", form_id, e)
        return questions

    @staticmethod
    def _format_urgency(val):
        if val is None or val == "":
            return val
        val_str = str(val).strip()
        if val_str.isdigit():
            return val_str
        numero = _URGENCIA_PARA_NUMERO.get(val_str.lower())
        if numero is None:
            log.warning("Urgência desconhecida: '%s'", val)
            return val
        return str(numero)

    # ------------------------------------------------------------------
    # Dispatcher público
    # ------------------------------------------------------------------
    def criar_chamado(self, form_chave: str, descricao: str,
                      unidade: str, email_solicitante: str,
                      tipo_problema: str = None) -> dict:
        """
        Cria o FormAnswer e faz o pós-processamento.
        O dict de retorno tem:
          - "id": ID do FormAnswer
          - "ticket_id": ID do Ticket real (adicionado por nós)
        """
        # 1. Cria o FormAnswer
        if form_chave == "manutencao":
            resposta = self._criar_chamado_manutencao(
                descricao, unidade, email_solicitante, tipo_problema
            )
        elif form_chave == "flexsmart":
            resposta = self._criar_chamado_flexsmart(
                descricao, unidade, email_solicitante
            )
        else:
            raise ValueError(f"Form '{form_chave}' não suportado pelo bot")

        # 2. Descobre o ID do FormAnswer
        formanswer_id = None
        if isinstance(resposta, dict):
            formanswer_id = resposta.get("id")

        if not formanswer_id:
            log.warning("Sem ID do FormAnswer — pós-processamento pulado")
            if isinstance(resposta, dict):
                resposta["ticket_id"] = None
            return resposta

        # 3. Descobre o ID do Ticket real
        ticket_id = self._get_real_ticket_id(int(formanswer_id))
        resposta["ticket_id"] = ticket_id  # <-- ADICIONA A CHAVE

        if not ticket_id:
            log.warning("Sem ID do Ticket — pós-processamento pulado")
            return resposta

        # 4. Adiciona o solicitante como requerente
        user = self.buscar_usuario_por_email(email_solicitante)
        if user and user.get("id"):
            self._add_requester(ticket_id, int(user["id"]))
        else:
            log.warning("Usuário %s não achado pra adicionar como requerente",
                        email_solicitante)

        # 5. Remove o bot dos atores
        self._remove_bot_actors(ticket_id, GLPI_BOT_USER_ID)

        return resposta

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------
    def _criar_chamado_manutencao(self, descricao, unidade, email,
                                  tipo_problema=None):
        if tipo_problema is None:
            from triagem import classificar_problema
            tipo_problema = classificar_problema(descricao)

        tipo_solicitacao = _TIPO_PARA_SOLICITACAO.get(
            tipo_problema, "Manutenção de Equipamentos"
        )
        equipamento = _TIPO_PARA_EQUIPAMENTO.get(
            tipo_problema, "Computador/Hardware"
        )

        unidade_up = (unidade or "").upper()
        if unidade_up in ("MATRIZ", "_SUPORTE"):
            local = "Matriz"
            filial = None
        elif unidade_up in _UNIDADE_PARA_FILIAL:
            local = "Filial"
            filial = _UNIDADE_PARA_FILIAL[unidade_up]
        else:
            local = "Matriz"
            filial = None

        valores = {
            str(CAMPO_MANUT_TIPO_SOLICITACAO):  tipo_solicitacao,
            str(CAMPO_MANUT_EQUIPAMENTO):       equipamento,
            str(CAMPO_MANUT_DESCRICAO):         descricao,
            str(CAMPO_MANUT_LOCAL_SOLICITACAO): local,
            str(CAMPO_MANUT_CANAL_CONTATO):     CANAL_CONTATO_PADRAO,
            str(CAMPO_MANUT_EMAIL_TEAMS):       email,
            str(CAMPO_MANUT_URGENCIA):          URGENCIA_PADRAO,
        }
        if filial:
            valores[str(CAMPO_MANUT_FILIAL)] = filial
        if tipo_solicitacao == "Manutenção de Sistemas":
            valores[str(CAMPO_MANUT_SISTEMA_PROBLEMA)] = "Outros Sistemas"

        return self._enviar_form(FORM_ID_MANUTENCAO, valores)

    def _criar_chamado_flexsmart(self, descricao, unidade, email):
        valores = {
            str(CAMPO_FLEX_TIPO_ATENDIMENTO):       "Outro",
            str(CAMPO_FLEX_QUAL_LIBERACAO_SISTEMA): descricao,
            str(CAMPO_FLEX_DESCRICAO):              descricao,
            str(CAMPO_FLEX_CANAL_CONTATO):          CANAL_CONTATO_PADRAO,
            str(CAMPO_FLEX_EMAIL_TEAMS):            email,
            str(CAMPO_FLEX_URGENCIA):               URGENCIA_PADRAO,
        }
        return self._enviar_form(FORM_ID_FLEXSMART, valores)

    # ------------------------------------------------------------------
    # Helper comum
    # ------------------------------------------------------------------
    def _enviar_form(self, form_id: int, valores: dict) -> dict:
        perguntas = self._get_form_questions(form_id)
        fieldtype_por_id = {
            str(q.get("id")): q.get("fieldtype", "") for q in perguntas
        }

        for q in perguntas:
            q_id = str(q.get("id"))
            q_type = q.get("fieldtype", "")
            if q_type in ("text", "email", "textarea") and q_id not in valores:
                valores[q_id] = ""

        fields_payload = {}
        for q_id, val in valores.items():
            if fieldtype_por_id.get(q_id) == "urgency":
                val = self._format_urgency(val)
            fields_payload[f"formcreator_field_{q_id}"] = val

        payload = {
            "input": {
                "plugin_formcreator_forms_id": int(form_id),
                **fields_payload,
            }
        }

        log.info("Enviando FormAnswer form=%s", form_id)
        log.debug("Payload: %s", payload)

        resp = requests.post(
            f"{GLPI_URL}/PluginFormcreatorFormanswer",
            headers=self._headers(),
            json=payload,
            timeout=20,
        )
        _verificar_resposta(resp)
        return resp.json()

    # ==================================================================
    # Fase 1: pós-processamento
    # ==================================================================
    def _get_real_ticket_id(self, formanswer_id: int):
        """
        Descobre o ID do Ticket real que o Formcreator criou a partir
        do FormAnswer. Usa o endpoint Item_Ticket.
        """
        try:
            resp = requests.get(
                f"{GLPI_URL}/PluginFormcreatorFormAnswer/{formanswer_id}/Item_Ticket",
                headers=self._headers(),
                timeout=10,
            )
            if resp.status_code in (200, 206):
                items = resp.json()
                if isinstance(items, list) and items:
                    tid = items[0].get("tickets_id")
                    if tid:
                        log.info("Ticket real do FormAnswer %s: %s",
                                 formanswer_id, tid)
                        return tid
                elif isinstance(items, dict):
                    tid = items.get("tickets_id")
                    if tid:
                        log.info("Ticket real do FormAnswer %s: %s",
                                 formanswer_id, tid)
                        return tid
            log.warning("Ticket real não encontrado pro FormAnswer %s",
                        formanswer_id)
            return None
        except Exception as e:
            log.error("Erro ao buscar ticket real: %s", e)
            return None

    def _add_requester(self, ticket_id: int, user_id: int) -> bool:
        """Adiciona um usuário como REQUERENTE (type=1) no ticket."""
        try:
            payload = {
                "input": {
                    "tickets_id": int(ticket_id),
                    "users_id": int(user_id),
                    "type": 1,
                }
            }
            resp = requests.post(
                f"{GLPI_URL}/Ticket/{ticket_id}/Ticket_User",
                headers=self._headers(),
                json=payload,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                log.info("Requerente %s adicionado ao ticket %s",
                         user_id, ticket_id)
                return True
            log.warning("Falha ao adicionar requerente %s: %s - %s",
                        user_id, resp.status_code, resp.text)
            return False
        except Exception as e:
            log.error("Erro ao adicionar requerente: %s", e)
            return False

    def _remove_bot_actors(self, ticket_id: int, bot_user_id: int) -> int:
        """
        Remove o bot (por ID) de TODOS os papéis no ticket.
        Não toca em outros atores (TI, FlexSmart).

        Retorna quantos atores foram removidos.
        """
        removidos = 0
        try:
            resp = requests.get(
                f"{GLPI_URL}/Ticket/{ticket_id}/Ticket_User",
                headers=self._headers(),
                timeout=10,
            )
            if resp.status_code not in (200, 206):
                log.warning("Falha ao listar atores do ticket %s: %s",
                            ticket_id, resp.status_code)
                return 0

            atores = resp.json()
            if not isinstance(atores, list):
                return 0

            for ator in atores:
                if not isinstance(ator, dict):
                    continue
                if ator.get("users_id") != bot_user_id:
                    continue

                actor_id = ator.get("id")
                if not actor_id:
                    continue

                del_resp = requests.delete(
                    f"{GLPI_URL}/Ticket/{ticket_id}/Ticket_User/{actor_id}",
                    headers=self._headers(),
                    timeout=10,
                )
                if del_resp.status_code in (200, 201):
                    log.info("Bot (ator %s) removido do ticket %s",
                             actor_id, ticket_id)
                    removidos += 1
                else:
                    log.warning("Falha ao remover ator %s: %s - %s",
                                actor_id, del_resp.status_code, del_resp.text)

            log.info("Total de atores do bot removidos do ticket %s: %s",
                     ticket_id, removidos)
            return removidos
        except Exception as e:
            log.error("Erro ao remover bot dos atores: %s", e)
            return 0