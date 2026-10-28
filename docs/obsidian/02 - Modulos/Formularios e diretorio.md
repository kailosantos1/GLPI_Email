# Formulários e dados do diretório

## Definições Formcreator

`forms.yaml` declara os formulários `flexsmart` (ID 5) e `manutencao` (ID 1), palavras-chave de classificação e perguntas com ID, rótulo, obrigatoriedade, opções e dependências condicionais. `forms_loader.py` converte as definições em objetos `Formulario` e `Pergunta`; `triagem.py` consome a chave, o nome e as palavras-chave.

Existe uma duplicação de configuração: IDs de formulários e campos também aparecem em `config.py` e os valores enviados são montados em `glpi_client.py`. Não há validação automática entre as duas fontes no código examinado.

## DN do Active Directory

`ad_parser.py` extrai atributos `OU` e `CN` do texto DN. Compara OU com `UNIDADES_CONHECIDAS`, normalizando caixa e acentos; o departamento é inferido como a OU imediatamente anterior à unidade encontrada. Isso é uma regra implementada, não uma consulta direta ao Active Directory.

## Referências

- [`forms.yaml`](../../../forms.yaml)
- [`forms_loader.py`](../../../forms_loader.py) — `Pergunta`, `Formulario` e `carregar_formularios()`.
- [`config.py`](../../../config.py) — `UNIDADES_CONHECIDAS` e IDs.
- [`ad_parser.py`](../../../ad_parser.py) — `extrair_info_dn()` e auxiliares.
- [[04 - Dados/Formularios e payloads|Dados e payloads]]
- [[08 - Pendencias/Pontos a confirmar|Questões sobre consistência de configuração]]

[[02 - Modulos/Índice|← Índice de Módulos]]
