# MailFlow-Automation

# 📧 MailFlow Automation

Classificador inteligente de e-mails capaz de distinguir automaticamente entre **Produtivo** e **Improdutivo**, sugerindo uma resposta adequada de forma rápida e organizada.  

Este projeto tem duas versões:
1. **Client-side (GitHub Pages)** → roda totalmente no navegador com regras determinísticas (não precisa de servidor nem IA).
2. **Server-side (Flask + OpenAI)** → roda com API no backend, integrando modelos da OpenAI para classificação mais avançada.

---

## 🎥 Demonstração em Vídeo
👉 [Assista ao vídeo explicativo no YouTube](https://www.youtube.com/watch?v=DAIHWwJXdg4)  

---

## ⚡ Versão atual (rodando sem IA)
Atualmente, a versão publicada no **GitHub Pages** está rodando **sem Inteligência Artificial**, apenas com **regras determinísticas** em **JavaScript**, ou seja:

- Não precisa de servidor.
- Não precisa de chave de API.
- Toda a classificação acontece localmente no navegador.

### 🔎 Como funciona sem IA
- Procura **palavras-chave produtivas** (ex.: `status`, `prazo`, `suporte`, `contrato`, `anexo`) → aumenta a pontuação.
- Detecta **palavras-chave improdutivas** (ex.: `bom dia`, `parabéns`, `obrigado`) → diminui a pontuação.
- Links promocionais/spam → penalizam.
- **Pedido/protocolo/ticket** → soma pontos.
- **Perguntas (?)** → soma pontos.

📌 Resultado:
- **Pontuação ≥ 2** → **Produtivo**
- **Pontuação < 2** → **Improdutivo**

Em seguida, o sistema gera uma **resposta padrão** adequada ao tipo de e-mail.

### ✅ Vantagens
- Gratuito (GitHub Pages).
- Sem dependência de servidores externos.
- Funciona offline, rápido e simples.

### ❌ Limitações
- Não entende contexto.
- Pode classificar errado se o e-mail tiver palavras fora da lista.
- Respostas são pré-definidas, não adaptativas.

---

## 🤖 Versão com IA (OpenAI)
Além do modo client-side, o projeto também possui versão **com Inteligência Artificial real**, usando **Flask + OpenAI GPT**.  

### Como funciona:
- O texto do e-mail é enviado para a API (Flask).
- O modelo da OpenAI (`gpt-4o-mini`) analisa o conteúdo.
- Retorna um JSON válido com:
  ```json
  {
    "categoria": "Produtivo",
    "sugestao_resposta": "Olá! Registramos sua solicitação referente ao pedido 123. Nossa equipe vai verificar e retornar em breve."
  }
