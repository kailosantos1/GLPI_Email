# E-mail e Microsoft 365

## Leitura por IMAP

`email_reader.py` usa `imaplib.IMAP4_SSL`, seleciona a pasta IMAP configurada e pesquisa mensagens não lidas (`UNSEEN`). A autenticação usa XOAUTH2 com token emitido pelo MSAL no fluxo client credentials. O código define escopo de Outlook e mantém o token em cache local até 60 segundos antes da expiração.

Mensagens cujo endereço não termina com um domínio em `ALLOWED_DOMAINS` são rejeitadas. O corpo de HTML é convertido para texto quando não existe conteúdo `text/plain`; o corpo é truncado se exceder 50.000 caracteres.

## Resposta por SMTP

`email_sender.py` conecta ao host SMTP derivado de `IMAP_SERVER`, porta 587, inicia STARTTLS e autentica por XOAUTH2. Envia uma mensagem multipart texto/HTML com remetente fixo em configuração.

## O que não está especificado

O repositório não documenta consentimento/administração de permissões, registro de aplicação Azure, configuração de mailbox, destinatários autorizados na plataforma, política de retenção nem implantação.

## Referências

- [`email_reader.py`](../../../email_reader.py)
- [`email_sender.py`](../../../email_sender.py)
- [`config.py`](../../../config.py)
- [[02 - Modulos/Email|Módulo de e-mail]]
- [[06 - Desenvolvimento/Configuração e execução|Variáveis de configuração]]

[[05 - Interfaces e Integracoes/Índice|← Índice de Integrações]]
