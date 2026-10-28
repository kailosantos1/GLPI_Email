# Bot GLPI Email — documentação

Este vault descreve o bot Python que monitora e-mails de suporte, identifica solicitações de TI e abre chamados no GLPI via Formcreator. As notas foram produzidas a partir dos arquivos versionados e distinguem fatos observados de pontos que dependem de confirmação.

## Comece por aqui

- [[01 - Arquitetura/Índice|Arquitetura]]
- [[02 - Modulos/Índice|Módulos]]
- [[03 - Fluxos/Índice|Fluxos]]
- [[04 - Dados/Índice|Dados e persistência]]
- [[05 - Interfaces e Integracoes/Índice|Interfaces e integrações]]
- [[06 - Desenvolvimento/Índice|Desenvolvimento]]
- [[07 - Operacao/Índice|Operação]]
- [[08 - Pendencias/Índice|Pendências e dúvidas]]

## Visão rápida

O processo é iniciado por `main.py`. Ele consulta mensagens não lidas por IMAP/OAuth2, filtra remetentes, avalia se cada mensagem é uma solicitação de TI, localiza o usuário no GLPI, extrai dados de unidade do DN sincronizado do Active Directory, classifica o formulário, cria um FormAnswer/chamado e tenta enviar uma confirmação por SMTP/OAuth2.

## Cobertura da análise

Foram examinados os módulos Python da raiz (`main.py`, `email_reader.py`, `email_sender.py`, `glpi_client.py`, `triagem.py`, `ad_parser.py`, `forms_loader.py`, `config.py` e `logger_setup.py`), `forms.yaml`, `requirements.txt`, `.gitignore`, `.gitattributes` e `README.md`. A árvore versionada não contém diretórios de testes, configuração de empacotamento, CI ou deploy. O conteúdo de `.env.example` não foi lido, conforme a orientação de não acessar valores de configuração que possam conter segredos.

O README contém referências a scripts de teste que não estão presentes na árvore atual; isso está detalhado em [[08 - Pendencias/Pontos a confirmar|Pontos a confirmar]].

## Navegação

Use os índices no começo de cada seção. As referências ao código são links Markdown relativos ao arquivo da nota; os links entre notas usam caminhos completos a partir da raiz deste vault.

