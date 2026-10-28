# GLPI REST e Formcreator

## Autenticação e sessão

`GLPIClient.iniciar_sessao()` chama `initSession` com App-Token e `Authorization: user_token ...`. O Session-Token é usado nos headers seguintes; `encerrar_sessao()` chama `killSession`.

## Endpoints observados

Os caminhos abaixo são relativos à base `GLPI_URL`:

- `POST /initSession` e `GET /killSession`: ciclo de sessão.
- `GET /search/User` e `GET /User/{id}`: localização e leitura do usuário.
- `GET /PluginFormcreatorForm/{id}/PluginFormcreatorSection` e `GET /PluginFormcreatorSection/{id}/PluginFormcreatorQuestion`: perguntas do formulário.
- `POST /PluginFormcreatorFormanswer`: criação do FormAnswer.
- `GET /PluginFormcreatorFormAnswer/{id}/Item_Ticket`: descoberta do ticket associado.
- `POST /Ticket/{id}/Ticket_User` e `GET/DELETE /Ticket/{id}/Ticket_User[/actor_id]`: requerente e atores.

Os nomes dos endpoints e os métodos HTTP refletem as chamadas presentes no cliente. Versões específicas de GLPI/Formcreator não estão registradas.

## Resultado e pós-processamento

Depois de criar o FormAnswer, o cliente tenta descobrir o ticket, adicionar o usuário solicitante como requerente e remover o usuário bot de todos os papéis no ticket. Falhas dessas ações são registradas, mas a criação já pode ter sido concluída.

## Referências

- [`glpi_client.py`](../../../glpi_client.py) — `iniciar_sessao()`, `buscar_usuario_por_email()`, `criar_chamado()` e helpers.
- [`config.py`](../../../config.py)
- [[02 - Modulos/GLPI e Formcreator|Responsabilidade do cliente]]
- [[04 - Dados/Formularios e payloads|Payloads]]

[[05 - Interfaces e Integracoes/Índice|← Índice de Integrações]]
