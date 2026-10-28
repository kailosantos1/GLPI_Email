# Fluxo de processamento de e-mail

```mermaid
sequenceDiagram
    participant Loop as main.py
    participant Mail as email_reader.py
    participant Triage as triagem.py
    participant GLPI as glpi_client.py
    participant AD as ad_parser.py
    participant Reply as email_sender.py
    Loop->>Mail: buscar_emails_novos()
    Mail-->>Loop: mensagens aceitas
    Loop->>Triage: e_chamado(corpo ou assunto)
    Triage-->>Loop: sim/não
    Loop->>GLPI: buscar_usuario_por_email(remetente)
    GLPI-->>Loop: usuário
    Loop->>GLPI: extrair_dn(usuario)
    GLPI-->>Loop: DN
    Loop->>AD: extrair_info_dn(DN)
    AD-->>Loop: nome, departamento, unidade
    Loop->>Triage: classificar_email(texto)
    Triage-->>Loop: formulario
    Loop->>GLPI: criar_chamado(...)
    GLPI-->>Loop: FormAnswer + ticket_id
    Loop->>Reply: enviar_email(confirmação)
```

## Condições de bloqueio ou descarte

- Remetente fora de `ALLOWED_DOMAINS`: não é retornado pelo leitor.
- Mensagem não considerada chamado: ignorada antes de buscar usuário.
- Usuário inexistente, sem DN ou sem unidade reconhecida: interrompe o processamento daquela mensagem.
- Formulário não identificado: não cria chamado.
- Falha inesperada na mensagem: registra erro e tenta salvá-la em `emails_com_erro/`.
- A confirmação é enviada somente depois da criação; uma falha no envio é registrada sem desfazer o chamado.

## Integrações envolvidas

- [[05 - Interfaces e Integracoes/Email e Microsoft 365|IMAP, OAuth2 e SMTP]]
- [[05 - Interfaces e Integracoes/GLPI REST e Formcreator|GLPI/Formcreator]]
- [[05 - Interfaces e Integracoes/Gemini|Classificação de fallback]]
- [[04 - Dados/Formularios e payloads|Dados e estruturas]]

## Referências

- [`main.py`](../../../main.py) — `processar_email()` e `main()`.
- [`email_reader.py`](../../../email_reader.py) — `buscar_emails_novos()`.

[[03 - Fluxos/Índice|← Índice de Fluxos]]
