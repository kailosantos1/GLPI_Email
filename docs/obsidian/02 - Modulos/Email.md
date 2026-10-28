# Leitura e envio de e-mail

## Leitura — `email_reader.py`

`buscar_emails_novos()` conecta ao IMAP SSL com `IMAP_SERVER` e `IMAP_PORT`, autentica com XOAUTH2 e busca mensagens `UNSEEN` na pasta configurada. O token de aplicação é obtido pelo MSAL com fluxo client credentials e armazenado em cache em memória até próximo do vencimento.

O remetente deve terminar com um dos sufixos definidos em `ALLOWED_DOMAINS`. A extração prefere `text/plain`; quando só há HTML, `_limpar_html()` remove elementos não textuais e converte o conteúdo. `_extrair_corpo()` limita o resultado a `MAX_CORPO_CHARS` (50.000 caracteres).

## Envio — `email_sender.py`

`enviar_email()` constrói uma mensagem multipart alternativa (texto e HTML), conecta ao SMTP com STARTTLS e XOAUTH2, e envia a confirmação. Usa o token compartilhado de `email_reader.obter_access_token()`. A função retorna sucesso/falha e registra erros no logger.

## Dependências de configuração

As opções de servidor, caixa e Azure são definidas em `config.py`; nomes e propósito estão em [[02 - Modulos/Configuracao e logging|Configuração]]. O código pressupõe permissões de aplicação e configuração de OAuth2 no Microsoft 365, mas os passos de provisionamento não estão descritos no repositório.

## Referências

- [`email_reader.py`](../../../email_reader.py) — `obter_access_token()`, `_extrair_corpo()`, `_remetente_valido()` e `buscar_emails_novos()`.
- [`email_sender.py`](../../../email_sender.py) — `enviar_email()`.
- [[05 - Interfaces e Integracoes/Email e Microsoft 365|Integração Microsoft 365]]
- [[03 - Fluxos/Fluxo de processamento|Fluxo de processamento]]

[[02 - Modulos/Índice|← Índice de Módulos]]
