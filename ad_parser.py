"""
Extrai informações do DN (Distinguished Name) do Active Directory
que vem no cadastro do usuário sincronizado no GLPI.

Exemplo:
CN=Juliana Galves,OU=Usuarios,OU=Financeiro,OU=MATRIZ,OU=COMPASI,DC=compasi,DC=local
"""

import re
from config import UNIDADES_CONHECIDAS


def extrair_ous(dn: str) -> list:
    return re.findall(r"OU=([^,]+)", dn)


def extrair_cn(dn: str):
    match = re.search(r"CN=([^,]+)", dn)
    return match.group(1) if match else None


def _normalizar(s: str) -> str:
    return (
        s.upper()
        .replace("Á", "A").replace("Â", "A").replace("Ã", "A")
        .replace("É", "E").replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ó", "O").replace("Ô", "O").replace("Õ", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
    )


def extrair_unidade(ous: list):
    """
    Procura entre os valores de OU qual bate com uma unidade conhecida.
    Normaliza acentos e caixa para evitar mismatch.
    """
    conhecidas_norm = {_normalizar(u): u for u in UNIDADES_CONHECIDAS}

    for ou in ous:
        chave = _normalizar(ou)
        if chave in conhecidas_norm:
            return conhecidas_norm[chave]
    return None


def extrair_departamento(ous: list, unidade):
    """
    Assume que o departamento é a OU que vem logo antes da unidade.
    (OU=Financeiro,OU=MATRIZ -> departamento = Financeiro)
    """
    if not unidade:
        return None
    for i, ou in enumerate(ous):
        if _normalizar(ou) == _normalizar(unidade) and i > 0:
            return ous[i - 1]
    return None


def extrair_info_dn(dn: str) -> dict:
    ous = extrair_ous(dn)
    unidade = extrair_unidade(ous)
    return {
        "nome": extrair_cn(dn),
        "departamento": extrair_departamento(ous, unidade),
        "unidade": unidade,
    }