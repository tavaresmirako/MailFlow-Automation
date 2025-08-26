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




🏗️ Estrutura do Projeto
bash
Copiar
Editar
MailFlow-Automation/
├── app.py                 # API Flask (quando usar backend/IA)
├── requirements.txt       # Dependências do backend
├── templates/
│   └── index.html         # Interface web
├── static/
│   ├── css/style.css      # Estilos (backend)
│   └── js/script.js       # Lógica frontend (backend)
└── docs/                  # Versão estática para GitHub Pages (sem IA)
    ├── index.html
    └── static/
        ├── css/style.css
        └── js/script.js
        
🔧 Instalação (versão backend com IA)
Clone o repositório e instale as dependências:

bash
Copiar
Editar
git clone https://github.com/tavaresmirako/MailFlow-Automation.git
cd MailFlow-Automation
pip install -r requirements.txt
Crie um arquivo .env com:

env
Copiar
Editar
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
MOCK_MODE=0
DEBUG_VERBOSE=1
Execute:

bash
Copiar
Editar
python app.py
Acesse em: http://127.0.0.1:8000

🌐 Publicação no GitHub Pages (sem IA)
A versão client-side está em /docs.
Para publicar:

Commit/push para a branch main.

No GitHub: Settings → Pages → Source → main /docs.

Acesse a URL pública gerada.

🛠️ Tecnologias Utilizadas
Flask (backend API com IA)

Flask-CORS (CORS no backend)

OpenAI (IA avançada)

HTML5, CSS3 e JavaScript (frontend sem IA)

GitHub Pages (deploy gratuito do frontend)

📌 Roadmap
 Classificação básica (mock/local sem IA)

 Deploy client-side no GitHub Pages

 Deploy backend (Flask + OpenAI) em Railway/Render

 Dashboard de histórico de e-mails

 Treinamento de modelos customizados

📜 Licença
Este projeto está sob a licença MIT – sinta-se livre para usar e modificar.

