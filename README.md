# Bot GLPI Email

Bot que lê e-mails de suporte, classifica o problema e abre chamados
automaticamente no GLPI via Formcreator.

## Como funciona

1. Conecta via IMAP (OAuth2) na caixa `suporte@compasi.com.br`
2. Filtra e-mails do domínio `@compasi.com.br` e `@compasiimple.onmicrosoft.com`
3. Busca o usuário no GLPI pelo e-mail e extrai o DN do AD (setor/filial)
4. Classifica o problema por keyword (fallback: Gemini)
5. Cria o chamado no Formcreator (form `manutencao` ou `flexsmart`)
6. Corrige o requerente e remove o `bot.email` dos atores
7. Envia auto-reply HTML de confirmação

## Setup

1. Copia `.env.example` para `.env` e preenche os valores
2. Instala as dependências:
   ```bash
   pip install -r requirements.txt

Roda:

bash
python main.py
Testes
bash
python testar_unitarios.py    # 38 asserts
python testar_tudo.py         # 22 testes dos itens de robustez
python testar_formcreator.py  # integração GLPI (cria chamados reais)
Estrutura
main.py — loop principal

email_reader.py — IMAP + OAuth2 + limpeza de HTML

email_sender.py — SMTP OAuth2 (auto-reply)

glpi_client.py — GLPI + Formcreator

triagem.py — classificação keyword + Gemini

ad_parser.py — parse do DN do AD

forms_loader.py + forms.yaml — definição dos formulários

logger_setup.py — logging rotativo

config.py — configurações

text

---

## 🎯 Passo a passo pra organizar

```powershell
cd C:\Automacoes\GLPI_Email

# 1. Deleta os arquivos inúteis
Remove-Item debug_dn_ti_externo.py, debug_glpi.py -ErrorAction SilentlyContinue
Remove-Item testar_busca_user.py, testar_cor_descricao.py, testar_cor_verde.py -ErrorAction SilentlyContinue
Remove-Item testar_email.py, testar_gemini.py, testar_gemini_isolado.py -ErrorAction SilentlyContinue
Remove-Item testar_imap.py, testar_parse_email.py, testar_pipeline.py -ErrorAction SilentlyContinue
Remove-Item testar_prefixo_glpi.py, testar_requerente.py, testar_smtp.py -ErrorAction SilentlyContinue

# 2. Deleta o __pycache__ (será recriado)
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue

# 3. Confere o que ficou
Get-ChildItem -Name
Saída esperada:

text
.env
ad_parser.py
bot.log
config.py
email_reader.py
email_sender.py
forms_loader.py
forms.yaml
glpi_client.py
logger_setup.py
main.py
testar_formcreator.py
testar_tudo.py
testar_unitarios.py
triagem.py
Se classificador.py ainda existir, olha se o main.py importa dele ou de triagem. Se for de triagem, deleta o classificador.py.

✅ Checklist final
□ Deletar arquivos inúteis (comando acima)
□ Criar .gitignore
□ Criar .env.example
□ Criar requirements.txt
□ Criar README.md
□ Conferir se main.py importa de triagem (não classificador)
□ Verificar se .env não está versionado (git status)