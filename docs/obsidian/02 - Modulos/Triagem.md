# Triagem e classificação

`triagem.py` implementa três decisões distintas:

1. **É uma solicitação de suporte?** `e_chamado()` verifica primeiro palavras-chave fortes. Sem correspondência, consulta Gemini quando existe chave configurada; sem chave, classifica como não chamado.
2. **Qual formulário?** `classificar_email()` lê `forms.yaml`, compara palavras-chave por formulário e, se não houver correspondência, usa Gemini como fallback quando habilitado.
3. **Qual tipo de problema?** `classificar_problema()` classifica categorias como Impressora, Rede, Email, Desempenho, Hardware ou Acesso/Senha por palavra-chave. Sem correspondência, tenta Gemini; sem chave, retorna `Outro`.

As palavras-chave são verificadas por ocorrência de substring no texto em minúsculas; não há tokenização descrita. A ordem das regras e as palavras-chave fortes influenciam o resultado.

## Gemini

`_chamar_gemini()` usa HTTP via `requests`, aplica throttle mínimo de 5 segundos entre chamadas e mantém respostas em cache local em memória por até 24 horas. Há retry com espera exponencial para respostas HTTP 429 e 503. Os fluxos de classificação tratam falhas de formas diferentes: o classificador de tipo usa `Outro`, o classificador de formulário pode retornar nenhum e `e_chamado()` considera chamado em caso de falha na consulta Gemini. Esse comportamento está confirmado na implementação e deve ser considerado na operação.

## Relações

- [[02 - Modulos/Formularios e diretorio|`forms.yaml` e loader]]
- [[02 - Modulos/Orquestracao|Uso da classificação pelo fluxo principal]]
- [[05 - Interfaces e Integracoes/Gemini|Integração Gemini]]
- [[08 - Pendencias/Pontos a confirmar|Pontos em aberto]]

## Referências

- [`triagem.py`](../../../triagem.py) — `e_chamado()`, `classificar_email()`, `classificar_problema()` e `_chamar_gemini()`.
- [`forms_loader.py`](../../../forms_loader.py) — `carregar_formularios()`.
- [`forms.yaml`](../../../forms.yaml) — palavras-chave, IDs, perguntas e opções.

[[02 - Modulos/Índice|← Índice de Módulos]]
