"""
Carrega a definicao dos formularios do GLPI (forms.yaml) e expoe
utilitarios pra casar keywords com o formulario certo.
"""

from dataclasses import dataclass, field
import yaml


@dataclass
class Pergunta:
    id: int
    label: str
    required: bool = True
    options: list = field(default_factory=list)
    depends_on: dict = None
    multiple: bool = False


@dataclass
class Formulario:
    chave: str
    id: int
    nome: str
    keywords: list
    perguntas: dict  # nome_campo -> Pergunta


def carregar_formularios(caminho: str = "forms.yaml") -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        dados = yaml.safe_load(f)

    formularios = {}
    for chave, form_dados in dados["forms"].items():
        perguntas = {}
        for nome_campo, p in form_dados.get("questions", {}).items():
            perguntas[nome_campo] = Pergunta(
                id=p["id"],
                label=p["label"],
                required=p.get("required", True),
                options=p.get("options", []),
                depends_on=p.get("depends_on"),
                multiple=p.get("multiple", False),
            )

        formularios[chave] = Formulario(
            chave=chave,
            id=form_dados["id"],
            nome=form_dados["name"],
            keywords=[k.lower() for k in form_dados.get("keywords", [])],
            perguntas=perguntas,
        )

    return formularios