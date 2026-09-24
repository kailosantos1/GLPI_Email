import os
from dotenv import load_dotenv

load_dotenv()

# =====================================================================
# GLPI
# =====================================================================
GLPI_URL        = os.getenv("GLPI_URL", "")
GLPI_APP_TOKEN  = os.getenv("GLPI_APP_TOKEN", "")
GLPI_USER_TOKEN = os.getenv("GLPI_USER_TOKEN", "")

# ID do usuário "bot.email" no GLPI — usado pra remover ele dos atores
# do chamado depois de criar (o requerente deve ser o solicitante real).
GLPI_BOT_USER_ID = int(os.getenv("GLPI_BOT_USER_ID", "286"))

# =====================================================================
# Formcreator — Form "Solicitações de Manutenção" (id=1)
# =====================================================================
FORM_ID_MANUTENCAO = 1

CAMPO_MANUT_TIPO_SOLICITACAO   = 2
CAMPO_MANUT_DESCRICAO          = 3
CAMPO_MANUT_URGENCIA           = 4
CAMPO_MANUT_LOCAL_SOLICITACAO  = 6
CAMPO_MANUT_FILIAL             = 7
CAMPO_MANUT_EQUIPAMENTO        = 26
CAMPO_MANUT_CANAL_CONTATO      = 70
CAMPO_MANUT_WHATSAPP           = 71
CAMPO_MANUT_EMAIL_TEAMS        = 72
CAMPO_MANUT_SISTEMA_PROBLEMA   = 104

# =====================================================================
# Formcreator — Form "Solicitações sistema FlexSmart" (id=5)
# =====================================================================
FORM_ID_FLEXSMART = 5

CAMPO_FLEX_TIPO_ATENDIMENTO       = 106
CAMPO_FLEX_QUAL_LIBERACAO         = 107
CAMPO_FLEX_QUAL_TELA              = 108
CAMPO_FLEX_LIBERACAO_PARA_USUARIO = 109
CAMPO_FLEX_NOME_USUARIO           = 110
CAMPO_FLEX_QUAL_LIBERACAO_SISTEMA = 111
CAMPO_FLEX_URGENCIA               = 112
CAMPO_FLEX_DESCRICAO              = 42
CAMPO_FLEX_CANAL_CONTATO          = 73
CAMPO_FLEX_WHATSAPP               = 74
CAMPO_FLEX_EMAIL_TEAMS            = 75

# =====================================================================
# Padrões dos chamados abertos por e-mail
# =====================================================================
CANAL_CONTATO_PADRAO = "Microsoft Teams"
URGENCIA_PADRAO      = "Média"

# Nome e e-mail que aparecem no "De:" do auto-reply
REMETENTE_NOME  = "Suporte COMPASI"
REMETENTE_EMAIL = "suporte@compasi.com.br"

# =====================================================================
# Gemini (fallback de classificação)
# =====================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# =====================================================================
# IMAP / SMTP (Microsoft 365)
# =====================================================================
IMAP_SERVER           = os.getenv("IMAP_SERVER", "outlook.office365.com")
IMAP_PORT             = 993
IMAP_USER             = os.getenv("IMAP_USER", "")
IMAP_FOLDER           = os.getenv("IMAP_FOLDER", "INBOX")
POLL_INTERVAL_SECONDS = 30

# =====================================================================
# Domínios permitidos
# =====================================================================
ALLOWED_DOMAINS = [
    "@compasi.com.br",
    "@compasiimple.onmicrosoft.com",
]

# =====================================================================
# Azure AD / OAuth2 (M365)
# =====================================================================
AZURE_CLIENT_ID     = os.getenv("AZURE_CLIENT_ID", "")
AZURE_TENANT_ID     = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")

# =====================================================================
# Unidades conhecidas (extraídas do DN do AD)
# =====================================================================
UNIDADES_CONHECIDAS = {
    "MATRIZ",
    "MARAVILHA",
    "LAGES",
    "VIDEIRA",
    "CONCORDIA",
    "CATANDUVAS",
    "_SUPORTE",     # equipe de TI da matriz
}