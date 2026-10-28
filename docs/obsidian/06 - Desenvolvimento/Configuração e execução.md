# Configuração e execução

## Requisitos observados

O projeto é Python e declara em `requirements.txt`: `msal`, `requests`, `python-dotenv` e `beautifulsoup4`, com limites mínimos de versão. O código também importa `yaml` em `forms_loader.py`; o pacote que fornece esse módulo não aparece na lista declarada. Confirme e resolva essa dependência antes de preparar um ambiente limpo; veja [[08 - Pendencias/Pontos a confirmar|pendências]].

## Preparação identificada no README

O README orienta copiar `.env.example` para `.env`, preencher as configurações e instalar com:

```bash
pip install -r requirements.txt
python main.py
```

Esses comandos foram identificados no README, mas não foram executados nesta validação. Os nomes de configuração usados pelo código estão listados sem valores em [[02 - Modulos/Configuracao e logging|Configuração e logging]]. Não inclua segredos nas notas ou no controle de versão.

## Execução

`main.py` inicia o loop de polling e mantém o processo ativo até receber SIGINT/SIGTERM ou atingir o limite de falhas consecutivas ao consultar IMAP. O ciclo depende de acesso externo ao GLPI e ao Microsoft 365; Gemini só é consultado nos casos de fallback e quando configurado.

## Referências

- [`README.md`](../../../README.md)
- [`requirements.txt`](../../../requirements.txt)
- [`main.py`](../../../main.py)
- [[07 - Operacao/Execução e diagnóstico|Execução e diagnóstico]]

[[06 - Desenvolvimento/Índice|← Índice de Desenvolvimento]]
