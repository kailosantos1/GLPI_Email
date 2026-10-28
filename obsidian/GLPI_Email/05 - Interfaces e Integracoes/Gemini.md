# Gemini

`triagem.py` chama a API Generative Language por HTTP (`requests`) usando `GEMINI_MODEL` e `GEMINI_API_KEY`. Gemini é fallback, não é requisito para todas as classificações:

- `e_chamado()` só consulta o modelo quando não encontra keyword forte.
- `classificar_email()` só consulta o modelo quando nenhuma keyword de formulário corresponde.
- `classificar_problema()` só consulta o modelo quando nenhuma keyword de tipo corresponde.

O módulo aplica throttle de cinco segundos, cache de respostas em memória por 24 horas e retry em status HTTP 429/503. Não foi identificada uma dependência SDK Gemini no `requirements.txt`.

O comportamento em erro varia por finalidade e está detalhado em [[02 - Modulos/Triagem|Triagem e classificação]].

## Referências

- [`triagem.py`](../../../triagem.py) — `_chamar_gemini()` e funções de classificação.
- [`config.py`](../../../config.py) — nomes das configurações.

[[05 - Interfaces e Integracoes/Índice|← Índice de Integrações]]
