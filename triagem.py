"""
Classificação do e-mail:
  1) Verifica se o texto é um chamado de TI de verdade (Abordagem D)
     - Se keyword FORTE de TI bateu → é chamado
     - Senão → pergunta ao Gemini "é chamado?"
  2) Escolhe QUAL formulário (manutencao vs flexsmart) por keyword
  3) Classifica o TIPO do problema (Impressora, Rede, ...) por keyword
  4) Só cai no Gemini se NENHUMA keyword bateu

TEM RATE LIMIT: a cota gratuita do Gemini é baixa (~15 req/min).
Pra não estourar, usamos throttle de 5s entre chamadas e cache de 24h.
"""

import hashlib
import time
import requests

from config import GEMINI_API_KEY, GEMINI_MODEL
from forms_loader import carregar_formularios


# ---------------------------------------------------------------------
# Cache de respostas do Gemini (24h)
# ---------------------------------------------------------------------
_gemini_cache = {}
_GEMINI_CACHE_TTL = 24 * 60 * 60

_ultima_chamada_gemini = 0
_GEMINI_INTERVALO_MIN = 5.0  # segundos


# ---------------------------------------------------------------------
# Keywords: tipo do problema (usado no form de manutenção)
# ---------------------------------------------------------------------
KEYWORDS_TIPO = {
    # ---- Impressora ----
    "impressora":   "Impressora",
    "impressao":    "Impressora",
    "imprimir":     "Impressora",
    "toner":        "Impressora",
    "tinta":        "Impressora",
    "papel":        "Impressora",
    "atolando":     "Impressora",
    "atolou":       "Impressora",
    "atolado":      "Impressora",
    "multifuncional": "Impressora",
    "xerox":        "Impressora",
    "scanner":      "Impressora",
    "digitalizar":  "Impressora",

    # ---- Acesso / Senha ----
    "senha":        "Acesso/Senha",
    "login":        "Acesso/Senha",
    "acesso":       "Acesso/Senha",
    "bloqueado":    "Acesso/Senha",
    "bloqueada":    "Acesso/Senha",
    "bloqueio":     "Acesso/Senha",
    "desbloquear":  "Acesso/Senha",
    "esqueci":      "Acesso/Senha",
    "perdi":        "Acesso/Senha",

    # ---- Rede ----
    "internet":     "Rede",
    "wifi":         "Rede",
    "wi-fi":        "Rede",
    "rede":         "Rede",
    "vpn":          "Rede",
    "cabo":         "Rede",
    "sem conexão":  "Rede",
    "sem conexao":  "Rede",
    "caiu":         "Rede",
    "caindo":       "Rede",
    "lentidão de rede": "Rede",
    "cabeamento":   "Rede",

    # ---- Email ----
    "email":        "Email",
    "e-mail":       "Email",
    "outlook":      "Email",
    "correio":      "Email",
    "caixa postal": "Email",
    "spam":         "Email",
    "anexo":        "Email",

    # ---- Desempenho ----
    "lento":        "Desempenho",
    "lenta":        "Desempenho",
    "lentidão":     "Desempenho",
    "lentidao":     "Desempenho",
    "travando":     "Desempenho",
    "travou":       "Desempenho",
    "travado":      "Desempenho",
    "tela azul":    "Desempenho",
    "congelou":     "Desempenho",
    "reiniciando":  "Desempenho",
    "reinicia":     "Desempenho",

    # ---- Hardware ----
    "computador":   "Hardware",
    "monitor":      "Hardware",
    "teclado":      "Hardware",
    "mouse":        "Hardware",
    "notebook":     "Hardware",
    "desktop":      "Hardware",
    "cpu":          "Hardware",
    "gabinete":     "Hardware",
    "memória":      "Hardware",
    "memoria":      "Hardware",
    "hd":           "Hardware",
    "ssd":          "Hardware",
    "bateria":      "Hardware",
    "carregador":   "Hardware",
    "fonte":        "Hardware",
    "quebrou":      "Hardware",
    "quebrado":     "Hardware",
    "não liga":     "Hardware",
    "nao liga":     "Hardware",
    "não funciona": "Hardware",
    "nao funciona": "Hardware",
    "webcam":       "Hardware",
    "câmera":       "Hardware",
    "camera":       "Hardware",
    "headset":      "Hardware",
    "fone":         "Hardware",
    "microfone":    "Hardware",
}

CATEGORIAS_GEMINI = sorted(set(KEYWORDS_TIPO.values()))


# ---------------------------------------------------------------------
# Keywords consideradas "fortes o suficiente" pra decidir sozinhas que
# o texto é um chamado de TI. As outras keywords (email, acesso, senha,
# sistema, etc.) só ajudam a CLASSIFICAR o tipo, mas não bastam como
# prova de que é chamado (senão "olhe o email tal" viraria chamado).
# ---------------------------------------------------------------------
KEYWORDS_FORTES = {
    # Impressora
    "impressora", "impressao", "imprimir", "toner", "atolando", "atolou",
    "multifuncional", "xerox", "scanner",

    # Rede
    "wifi", "wi-fi", "vpn", "internet", "caiu", "caindo",
    "sem conexão", "sem conexao", "cabeamento",

    # Desempenho
    "lento", "lenta", "lentidão", "lentidao", "travando", "travou",
    "travado", "tela azul", "congelou",

    # Hardware
    "computador", "monitor", "teclado", "mouse", "notebook", "gabinete",
    "memória", "memoria", "hd", "ssd", "bateria", "carregador",
    "quebrou", "quebrado", "não liga", "nao liga", "não funciona",
    "nao funciona", "webcam", "câmera", "camera", "headset", "fone",
    "microfone",

    # Email (específicas — "email" e "e-mail" sozinhos NÃO contam)
    "outlook", "correio", "caixa postal",

    # Acesso (específicas)
    "senha", "bloqueado", "bloqueada", "bloqueio", "desbloquear",
    "esqueci",
}


# ---------------------------------------------------------------------
# Chamada ao Gemini: throttle + cache + retry
# ---------------------------------------------------------------------
def _chamar_gemini(prompt: str) -> dict:
    global _ultima_chamada_gemini

    chave_cache = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if chave_cache in _gemini_cache:
        entrada = _gemini_cache[chave_cache]
        if time.time() - entrada["ts"] < _GEMINI_CACHE_TTL:
            print("[GEMINI] cache hit")
            return entrada["resposta"]

    agora = time.time()
    espera = _GEMINI_INTERVALO_MIN - (agora - _ultima_chamada_gemini)
    if espera > 0:
        print(f"[GEMINI] aguardando {espera:.1f}s (throttle)")
        time.sleep(espera)

    resp = None
    for tentativa in range(4):
        _ultima_chamada_gemini = time.time()
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )

        if resp.status_code == 200:
            break

        if resp.status_code in (429, 503):
            espera = 5 * (2 ** tentativa)
            print(f"[GEMINI] HTTP {resp.status_code} — aguardando {espera}s "
                  f"(tentativa {tentativa + 1}/4)")
            time.sleep(espera)
            continue

        break

    resp.raise_for_status()
    data = resp.json()

    _gemini_cache[chave_cache] = {"resposta": data, "ts": time.time()}
    return data


# ---------------------------------------------------------------------
# Classificação do TIPO (Impressora, Rede, ...)
# ---------------------------------------------------------------------
def _classificar_tipo_por_keyword(texto: str):
    texto_lower = texto.lower()
    for palavra, tipo in KEYWORDS_TIPO.items():
        if palavra in texto_lower:
            return tipo
    return None


def _classificar_tipo_com_gemini(texto: str) -> str:
    prompt = (
        "Classifique o problema de TI abaixo em UMA destas categorias: "
        f"{', '.join(CATEGORIAS_GEMINI)}, ou 'Outro' se não se encaixar. "
        "Responda APENAS com o nome da categoria, sem mais nada.\n\n"
        f"Problema: {texto}"
    )

    try:
        data = _chamar_gemini(prompt)
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[GEMINI] falhou classificação de tipo: {e}")
        return "Outro"


def classificar_problema(texto: str) -> str:
    """Retorna o TIPO do problema (usado no form de manutenção)."""
    tipo = _classificar_tipo_por_keyword(texto)
    if tipo:
        return tipo
    if not GEMINI_API_KEY:
        return "Outro"
    return _classificar_tipo_com_gemini(texto)


# ---------------------------------------------------------------------
# Abordagem D: o texto é um CHAMADO de verdade?
# ---------------------------------------------------------------------
def _e_chamado_com_gemini(texto: str) -> bool:
    """
    Pergunta ao Gemini se o texto é uma solicitação de suporte de TI.
    Retorna True se for, False se não.
    """
    prompt = (
        "Você é um classificador de e-mails de suporte de TI.\n"
        "\n"
        "Responda APENAS 'SIM' ou 'NAO' (sem mais nada) se o e-mail "
        "abaixo é uma SOLICITAÇÃO DE SUPORTE DE TI que deve virar "
        "um chamado.\n"
        "\n"
        "É chamado (responda SIM) quando o usuário relata um problema "
        "de TI ou pede algo de TI. Exemplos:\n"
        "- 'minha impressora está atolando papel'\n"
        "- 'não consigo acessar o Outlook'\n"
        "- 'preciso de acesso ao FlexSmart'\n"
        "- 'o wifi caiu aqui'\n"
        "- 'esqueci minha senha'\n"
        "\n"
        "NÃO é chamado (responda NAO) quando:\n"
        "- o usuário só está pedindo pra você olhar outro e-mail\n"
        "- é uma conversa informal ('bom dia', 'tudo bem?')\n"
        "- é resposta a um chamado anterior\n"
        "- é newsletter, aviso, comunicado\n"
        "- é dúvida que não é de TI\n"
        "- o texto é vago demais e não descreve nada acionável\n"
        "\n"
        f"E-mail do usuário: {texto}\n"
        "\n"
        "Resposta (SIM ou NAO):"
    )

    try:
        data = _chamar_gemini(prompt)
        resposta = (
            data["candidates"][0]["content"]["parts"][0]["text"]
            .strip().upper()
        )
        print(f"[GEMINI] 'é chamado?' → {resposta}")
    except Exception as e:
        print(f"[GEMINI] falhou checagem 'é chamado': {e}")
        # Em caso de falha, ASSUME que é chamado (não perde e-mail)
        return True

    return resposta.startswith("SIM")


def e_chamado(texto: str) -> bool:
    """
    Decide se o texto parece um chamado de TI.

    Ordem:
      1. Se keyword FORTE de TI bateu (impressora, wifi, etc) → SIM
      2. Senão → pergunta pro Gemini
    """
    texto_lower = texto.lower()

    # 1. Alguma keyword FORTE bateu? Então é chamado
    for kw in KEYWORDS_FORTES:
        if kw in texto_lower:
            return True

    # 2. Sem keyword forte — pergunta pro Gemini
    if not GEMINI_API_KEY:
        return False

    return _e_chamado_com_gemini(texto)


# ---------------------------------------------------------------------
# Classificação do FORMULÁRIO (manutencao vs flexsmart)
# ---------------------------------------------------------------------
def _classificar_form_por_keyword(texto: str, formularios: dict):
    texto_lower = texto.lower()
    melhor_chave = None
    melhor_qtd = 0

    for chave, form in formularios.items():
        if chave == "cadastro":
            continue
        qtd = sum(1 for kw in form.keywords if kw in texto_lower)
        if qtd > melhor_qtd:
            melhor_qtd = qtd
            melhor_chave = chave

    return melhor_chave, melhor_qtd


def _classificar_form_com_gemini(texto: str, formularios: dict):
    opcoes = {
        chave: form.nome
        for chave, form in formularios.items()
        if chave != "cadastro"
    }
    lista = "\n".join(f"- {k}: {nome}" for k, nome in opcoes.items())

    prompt = (
        "Um cliente mandou o e-mail de suporte abaixo. Escolha qual dos "
        "formulários abaixo melhor se encaixa. Responda APENAS com a "
        "chave do formulário (a palavra antes dos dois-pontos), ou "
        "'nenhum' se não se encaixar em nenhum.\n\n"
        f"Formulários disponíveis:\n{lista}\n\n"
        f"E-mail do cliente: {texto}"
    )

    try:
        data = _chamar_gemini(prompt)
        resposta = (
            data["candidates"][0]["content"]["parts"][0]["text"]
            .strip().lower()
        )
    except Exception as e:
        print(f"[GEMINI] falhou classificação de form: {e}")
        return None

    return resposta if resposta in formularios else None


def classificar_email(texto: str) -> dict:
    formularios = carregar_formularios("forms.yaml")

    chave, qtd = _classificar_form_por_keyword(texto, formularios)
    if chave:
        return {
            "formulario": chave,
            "metodo": "keyword",
            "detalhe": f"{qtd} keyword(s)",
            "form_obj": formularios[chave],
        }

    if not GEMINI_API_KEY:
        return {
            "formulario": None,
            "metodo": "nenhum",
            "detalhe": "sem keyword e sem GEMINI_API_KEY",
            "form_obj": None,
        }

    chave_gemini = _classificar_form_com_gemini(texto, formularios)
    if chave_gemini:
        return {
            "formulario": chave_gemini,
            "metodo": "gemini",
            "detalhe": "classificado pelo Gemini",
            "form_obj": formularios[chave_gemini],
        }

    return {
        "formulario": None,
        "metodo": "nenhum",
        "detalhe": "não identificado nem por keyword nem por Gemini",
        "form_obj": None,
    }