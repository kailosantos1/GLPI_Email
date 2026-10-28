# Configuração e logging

## Configuração

`config.py` carrega variáveis de ambiente com `python-dotenv`. Os nomes abaixo foram identificados no código; valores não são reproduzidos:

| Grupo | Nomes configuráveis | Observação |
|---|---|---|
| GLPI | `GLPI_URL`, `GLPI_APP_TOKEN`, `GLPI_USER_TOKEN`, `GLPI_BOT_USER_ID` | O ID do bot tem default `286`. |
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | O modelo tem default definido no código. |
| IMAP/Microsoft 365 | `IMAP_SERVER`, `IMAP_USER`, `IMAP_FOLDER`, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` | Porta e intervalo de polling são constantes no código. |

`config.py` também contém defaults de urgência/canal, endereços de remetente, domínios aceitos, IDs dos formulários/campos e unidades reconhecidas. Consulte a fonte para valores operacionais; não copie segredos para notas.

## Logging

`configurar_logging()` grava em `bot.log` e no console. O arquivo é rotativo, com limite de 5 MiB e até cinco cópias antigas. A configuração ignora nova inicialização se o logger raiz já tiver handlers.

## Referências

- [`config.py`](../../../config.py)
- [`logger_setup.py`](../../../logger_setup.py) — `configurar_logging()` e `get_logger()`.
- [[06 - Desenvolvimento/Configuração e execução|Setup e execução]]
- [[07 - Operacao/Execução e diagnóstico|Operação e diagnóstico]]

[[02 - Modulos/Índice|← Índice de Módulos]]
