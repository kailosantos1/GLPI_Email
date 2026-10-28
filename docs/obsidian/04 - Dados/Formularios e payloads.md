# Formulários, mensagens e payloads

## Estruturas em memória

- O leitor retorna uma lista de dicionários de e-mail contendo `remetente`, `assunto` e `corpo`.
- `forms_loader.py` cria objetos `Formulario` e `Pergunta` a partir do YAML.
- A triagem devolve um dicionário com `formulario`, `metodo`, `detalhe` e `form_obj`.
- O cliente GLPI envia um payload JSON com `plugin_formcreator_forms_id` e campos no formato `formcreator_field_<id>`.
- A criação retorna o FormAnswer do GLPI e acrescenta `ticket_id` quando localizado.

Os nomes/estruturas acima são derivados diretamente dos retornos e payloads no código.

## Formulários

`forms.yaml` contém os IDs, nomes, palavras-chave e metadados das perguntas dos formulários de manutenção e FlexSmart. Entre os campos há tipo de atendimento/solicitação, descrição, urgência, localização/filial, equipamento, canal e campos específicos do sistema. Perguntas podem depender de outra resposta.

O conteúdo enviado na prática é montado em `glpi_client.py`; o YAML é usado pelo classificador e loader, não é uma geração automática completa de payload.

## DN e usuário

O GLPI fornece registro de usuário com e-mail/ID e um atributo de DN. `ad_parser.py` deriva `nome`, `departamento` e `unidade` a partir de CN/OU. O departamento é inferido pela posição relativa das OU.

## Persistência local observada

- `emails_com_erro/`: arquivos JSON de mensagens que geraram exceção ao processar.
- `bot.log`: log rotativo.
- Cache do Gemini: apenas memória do processo, com TTL configurado no módulo.

Não foram identificadas tabelas, migrações, banco ou outro mecanismo de persistência no repositório.

## Referências

- [`forms.yaml`](../../../forms.yaml)
- [`forms_loader.py`](../../../forms_loader.py)
- [`glpi_client.py`](../../../glpi_client.py)
- [`ad_parser.py`](../../../ad_parser.py)
- [[02 - Modulos/Formularios e diretorio|Formulários e parsing do diretório]]

[[04 - Dados/Índice|← Índice de Dados]]
