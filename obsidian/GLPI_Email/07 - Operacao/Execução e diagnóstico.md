# Execução e diagnóstico

## Ciclo do processo

O bot consulta e-mails a cada 30 segundos. São tratados SIGINT e SIGTERM para encerrar o loop e fechar a sessão GLPI. Após cinco erros consecutivos de busca IMAP, o fluxo registra erro crítico e propaga a falha. Erros de mensagens individuais são registrados e o processamento segue para a próxima mensagem.

## Observabilidade

- Logs são enviados ao console e a `bot.log`.
- O arquivo de log é rotativo: 5 MiB por arquivo, até cinco backups.
- Mensagens que lançam exceção durante o processamento são salvas como JSON em `emails_com_erro/`.
- Os arquivos JSON nessa pasta são ignorados pelo `.gitignore`.

Os limites são valores definidos em `logger_setup.py` e `main.py`. Nenhum dashboard, alerta externo, health check ou política de limpeza dos arquivos de erro foi encontrado.

## Diagnóstico inicial

1. Verifique a configuração necessária sem expor tokens/segredos.
2. Consulte `bot.log` para erros de IMAP, Gemini, GLPI ou SMTP.
3. Verifique se o remetente está em domínio permitido e se o usuário existe no GLPI com DN e unidade reconhecidos.
4. Para falhas de processamento, examine o motivo registrado nos arquivos locais de erro, protegendo o conteúdo do e-mail.
5. Confirme a correspondência entre IDs de campos locais e os formulários do GLPI.

Esses passos derivam das verificações e logs existentes; não substituem runbook operacional validado pelo ambiente.

## Deploy não documentado

Não há configuração de serviço de sistema, container, agendador, pipeline de deploy ou instrução para ambiente de produção nos arquivos analisados. Não se presume forma de hospedagem.

## Referências

- [`main.py`](../../../main.py)
- [`logger_setup.py`](../../../logger_setup.py)
- [`.gitignore`](../../../.gitignore)
- [[06 - Desenvolvimento/Configuração e execução|Configuração e execução]]

[[07 - Operacao/Índice|← Índice de Operação]]
