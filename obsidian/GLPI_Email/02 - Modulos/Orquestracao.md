# Orquestração e ciclo de vida

`main.py` inicializa logging e a sessão GLPI, executa o polling de e-mails e encerra a sessão GLPI no bloco `finally`. Os sinais SIGINT e SIGTERM pedem encerramento controlado do loop.

## Tratamento por mensagem

`processar_email()` aplica as etapas nesta ordem:

1. Usa o corpo da mensagem, com fallback para o assunto, e chama `e_chamado()`.
2. Busca o usuário no GLPI pelo endereço do remetente.
3. Extrai o DN e exige que uma unidade conhecida seja reconhecida.
4. Chama `classificar_email()`; para manutenção, também classifica o tipo do problema.
5. Monta a descrição HTML e solicita a criação do chamado a `GLPIClient`.
6. Tenta enviar a confirmação HTML.

Mensagens descartadas por validações são registradas em log. Exceções ao processar uma mensagem são registradas e a mensagem é gravada como JSON por `salvar_email_com_erro()`.

## Loop e recuperação

`main()` consulta e-mails a cada `POLL_INTERVAL_SECONDS` (30 s). Erros consecutivos ao buscar e-mails incrementam um contador e o processo levanta erro após cinco falhas. Um sucesso na busca zera esse contador. Exceções de processamento individuais são tratadas separadamente.

## Referências

- [`main.py`](../../../main.py) — `main()`, `processar_email()`, `salvar_email_com_erro()`, `montar_descricao()` e `montar_html_confirmacao()`.
- [[03 - Fluxos/Fluxo de processamento|Fluxo completo]]
- [[02 - Modulos/Triagem|Triagem]]
- [[02 - Modulos/GLPI e Formcreator|Integração GLPI]]

[[02 - Modulos/Índice|← Índice de Módulos]]
