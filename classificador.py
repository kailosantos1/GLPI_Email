"""
Escolhe qual formulario do GLPI melhor se encaixa no texto do email.

1) Conta quantas keywords de cada formulario aparecem no texto.
2) Se algum formulario tiver pelo menos 1 keyword batendo, escolhe o
   que tiver MAIS keywords batendo (empate: fica o primeiro definido
   no yaml).
3) Se nenhum formulario bater nenhuma keyword, cai no Gemini, que
   escolhe entre os formularios disponiveis (ou None -> fila de
   triagem manual).
"""

import time

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL


def classificar_por_keyword(texto: str, formularios: dict):
    """
    Retorna (chave_formulario, quantidade_de_matches) ou (None, 0)
    se nenhuma keyword bateu em nenhum formulario.
    """
    texto_lower = texto.lower()
    melhor_chave = None
    melhor_qtd = 0

    for chave, form in formularios.items():
        qtd = sum(1 for kw in form.keywords if kw in texto_lower)
        if qtd > melhor_qtd:
            melhor_qtd = qtd
            melhor_chave = chave

    return melhor_chave, melhor_qtd


def classificar_com_gemini(texto: str, formularios: dict):
    """Fallback: so e chamado quando nenhuma keyword bateu em nada."""
    opcoes = {chave: form.nome for chave, form in formularios.items()}
    lista_opcoes = "\n".join(f"- {chave}: {nome}" for chave, nome in opcoes.items())

    prompt = (
        "Um cliente mandou o email de suporte abaixo. Escolha qual dos "
        "formularios abaixo melhor se encaixa. Responda APENAS com a "
        "chave do formulario (a palavra antes dos dois-pontos), ou "
        "'nenhum' se nao se encaixar em nenhum.\n\n"
        f"Formularios disponiveis:\n{lista_opcoes}\n\n"
        f"Email do cliente: {texto}"
    )

    # retry simples: o modelo pode dar 503 (sobrecarregado) de vez em
    # quando. Tenta 3 vezes com uma pausa curta antes de desistir.
    resp = None
    for tentativa in range(3):
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        if resp.status_code != 503:
            break
        time.sleep(2 * (tentativa + 1))  # 2s, 4s, 6s

    resp.raise_for_status()
    data = resp.json()

    try:
        resposta = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
    except (KeyError, IndexError):
        return None

    return resposta if resposta in formularios else None


def classificar_email(texto: str, formularios: dict) -> dict:
    """
    Retorna dict com: formulario (chave ou None), metodo ("keyword",
    "gemini" ou "nenhum") e detalhe (qtd de matches ou explicacao).
    """
    chave, qtd = classificar_por_keyword(texto, formularios)
    if chave:
        return {"formulario": chave, "metodo": "keyword", "detalhe": f"{qtd} keyword(s)"}

    if not GEMINI_API_KEY:
        return {"formulario": None, "metodo": "nenhum", "detalhe": "sem keyword e sem GEMINI_API_KEY configurada"}

    chave_gemini = classificar_com_gemini(texto, formularios)
    if chave_gemini:
        return {"formulario": chave_gemini, "metodo": "gemini", "detalhe": "classificado pelo Gemini"}

    return {"formulario": None, "metodo": "nenhum", "detalhe": "nao identificado nem por keyword nem por Gemini"}