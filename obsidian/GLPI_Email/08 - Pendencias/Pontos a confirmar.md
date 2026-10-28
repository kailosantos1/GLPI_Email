# Pontos a confirmar

Os itens abaixo são limitações documentais ou inconsistências verificadas no checkout; não foram corrigidos porque a solicitação restringe as alterações à documentação.

## Dependência YAML não declarada

`forms_loader.py` importa `yaml`, mas `requirements.txt` declara somente MSAL, Requests, python-dotenv e BeautifulSoup. Confirme como PyYAML é fornecido no ambiente. Um ambiente limpo instalado apenas pelo arquivo de requisitos pode não conseguir importar o loader.

## Testes citados, porém ausentes

`README.md` documenta `testar_unitarios.py`, `testar_tudo.py` e `testar_formcreator.py`; nenhum desses arquivos está presente na árvore versionada. O teste de integração mencionado pode criar chamados reais, portanto requer ambiente e autorização adequados.

## Configuração duplicada de formulários

IDs e metadados de perguntas estão em `forms.yaml`, IDs de formulário/campo também estão em `config.py`, e os payloads são montados manualmente em `glpi_client.py`. Não foi localizada validação cruzada entre essas fontes; confirme qual delas é a referência de manutenção e como alinhar alterações de formulário no GLPI.

## Integrações/ambiente remoto

O código não documenta versão de GLPI/Formcreator, configuração de OAuth/Azure, permissões efetivas, endpoint de produção, deploy ou mecanismo de operação como serviço. Isso depende de confirmação com os responsáveis pelo ambiente.

## Lacunas de comportamento e governança

- Não há registro de idempotência/deduplicação de e-mails, política de retentativa global ou como tratar mensagens rejeitadas além dos logs observados.
- Os arquivos de erro locais podem conter conteúdo de e-mail; retenção, acesso e limpeza não estão documentados.
- As regras de keywords, domínios permitidos, mapeamento de unidades e IDs de formulário são específicas da configuração atual e devem ser confirmadas antes de mudanças.

Os pontos acima descrevem ausência de evidência nesta árvore, não afirmam que os recursos não existam na infraestrutura externa.

## Referências

- [`requirements.txt`](../../../requirements.txt)
- [`README.md`](../../../README.md)
- [`forms_loader.py`](../../../forms_loader.py)
- [`forms.yaml`](../../../forms.yaml)
- [`config.py`](../../../config.py)
- [`glpi_client.py`](../../../glpi_client.py)

[[08 - Pendencias/Índice|← Índice de Pendências]]
