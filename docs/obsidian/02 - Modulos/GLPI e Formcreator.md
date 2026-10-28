# Cliente GLPI e Formcreator

`GLPIClient` encapsula chamadas REST ao GLPI usando `requests`. `iniciar_sessao()` usa App-Token e user token e guarda o Session-Token; `_headers()` o envia nas chamadas subsequentes. `encerrar_sessao()` tenta invalidar a sessão.

## Busca de usuário

`buscar_usuario_por_email()` consulta `/search/User`, extrai o ID e carrega o registro detalhado em `/User/{id}`. `extrair_dn()` tenta chaves alternativas do registro para obter o DN sincronizado.

## Criação de chamados

`criar_chamado()` seleciona um builder por `form_chave` (`manutencao` ou `flexsmart`). Os builders montam campos com IDs definidos em `config.py` e enviam `PluginFormcreatorFormanswer`. `_enviar_form()` consulta as perguntas do formulário e preenche valores textuais vazios para tipos text/email/textarea ausentes.

Após criar o FormAnswer, o cliente procura o ticket real associado pelo endpoint `Item_Ticket`; quando encontrado, tenta adicionar o solicitante como requerente e remover o usuário de bot dos atores do ticket. O dicionário de retorno inclui `ticket_id` quando aplicável.

## Mapeamentos e limites

Para manutenção, tipo do problema é mapeado para tipo de solicitação e equipamento, e a unidade é mapeada para Matriz/Filial e filial conhecida. FlexSmart recebe campos padrão com tipo de atendimento `Outro`. O canal e a urgência padrão vêm de `config.py`.

Os IDs de formulário/pergunta configurados em Python e no YAML precisam corresponder ao ambiente GLPI/Plugin Formcreator; a documentação não confirma versão ou configuração remota.

## Referências

- [`glpi_client.py`](../../../glpi_client.py) — `GLPIClient`, `criar_chamado()`, builders e pós-processamento.
- [`config.py`](../../../config.py) — IDs de formulários e campos.
- [`forms.yaml`](../../../forms.yaml) — definições locais de perguntas e opções.
- [[05 - Interfaces e Integracoes/GLPI REST e Formcreator|Endpoints e integração]]
- [[04 - Dados/Formularios e payloads|Dados enviados]]

[[02 - Modulos/Índice|← Índice de Módulos]]
