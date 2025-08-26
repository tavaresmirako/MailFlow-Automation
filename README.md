# MailFlow-Automation
MailFlow: Smart Email Automation é uma ferramenta para o desafio AutoU, focada na classificação inteligente de e-mails e na geração de respostas automáticas por meio de inteligência artificial.
MailFlow-Automation
Aplicação web simples para classificar e-mails e sugerir respostas automáticas usando IA.
Funciona em dois modos:

Mock Mode (desenvolvimento/segurança): não chama a OpenAI; retorna resposta simulada para testar fluxo e UI.

Modo Real (produção/demo): usa sua chave da OpenAI para classificar/generar respostas de verdade.

📦 Tecnologias
Backend: Python 3.10+ (Flask)

Frontend: HTML + CSS + JS (fetch API)

IA: OpenAI (SDK 1.x)

Env vars: python-dotenv

📁 Estrutura
bash
Copiar
Editar
MailFlow-Automation/
│
├── app.py
├── requirements.txt
├── .gitignore
├── .env                  # (NÃO faça commit)
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
✅ Pré-requisitos
Python 3.10+

(Opcional) Conta e chave da OpenAI (para o modo real)

⚙️ Instalação
bash
Copiar
Editar
# 1) Clone e entre na pasta
git clone <seu-repo>
cd MailFlow-Automation

# 2) Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3) Instale as dependências
pip install -r requirements.txt
requirements.txt (sugestão):

ini
Copiar
Editar
Flask==3.1.2
openai==1.101.0
python-dotenv==1.1.1
gunicorn==23.0.0
🔐 Configuração do .env
Crie um arquivo .env na raiz do projeto:

dotenv
Copiar
Editar
# IA real (necessário no modo real)
OPENAI_API_KEY="sk-...sua_chave..."

# Modelo padrão (pode manter)
OPENAI_MODEL=gpt-4o-mini

# Porta do Flask
FLASK_RUN_PORT=8000

# Ativa/desativa o MOCK (1=on, 0=off)
MOCK_MODE=0
Importante: .env já deve estar no .gitignore para não vazar a chave.

▶️ Execução
Modo 1 — Mock Mode (sem OpenAI)
Retorna resposta simulada (ideal para testes e demo offline).

bash
Copiar
Editar
source venv/bin/activate
MOCK_MODE=1 FLASK_RUN_PORT=8000 python app.py
Acesse: http://127.0.0.1:8000

Modo 2 — Real (OpenAI)
Usa a chave do .env para classificar e responder.

bash
Copiar
Editar
source venv/bin/activate
FLASK_RUN_PORT=8000 python app.py
Acesse: http://127.0.0.1:8000

🧪 Testes rápidos
Interface (UI)
Abra http://127.0.0.1:8000

Cole um e-mail no campo

Clique Analisar

Veja Categoria e Sugestão de Resposta

Healthcheck / Diagnóstico
GET /healthz → {"status":"ok"}

GET /diag → mostra mock_mode, se encontrou index.html, script.js, style.css, etc.

bash
Copiar
Editar
curl -s http://127.0.0.1:8000/healthz
curl -s http://127.0.0.1:8000/diag
Endpoint principal (via curl)
bash
Copiar
Editar
curl -s -X POST http://127.0.0.1:8000/processar_email \
  -H "Content-Type: application/json" \
  -d '{"texto_email":"Olá, poderiam atualizar o status do chamado 123?"}'
Esperado (MOCK_MODE=1):

json
Copiar
Editar
{"categoria":"Produtivo","sugestao_resposta":"Olá! Já registrei sua solicitação. Em breve retornaremos com o status atualizado. 👍"}
🚑 Troubleshooting rápido
Connection refused / não conecta
Garanta que o servidor está rodando e na porta certa:

bash
Copiar
Editar
ss -ltnp | grep 8000
Se a porta estiver ocupada, mate o processo:

bash
Copiar
Editar
lsof -i :8000
kill -9 <PID>
Clicou Analisar e não aconteceu nada
Abra o DevTools (F12 → Console) e veja se há erro de JS.
No terminal do Flask, verifique se chegou POST /processar_email 200.

OpenAI erro 401/429/502
Verifique OPENAI_API_KEY no .env. Se a API estiver instável, rode com MOCK_MODE=1 para a demo.

Nada aparece, mas healthz ok
Confirme se os arquivos existem (use /diag) e se o script.js está igual ao entregue (sem ?.).

☁️ Deploy (Render – simples)
Faça push do repositório no GitHub (sem .env).

Crie um arquivo Procfile:

makefile
Copiar
Editar
web: gunicorn app:app
Render.com → New → Web Service → conecte seu repo

Runtime: Python

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

Environment Variables:

OPENAI_API_KEY=<sua_chave>

OPENAI_MODEL=gpt-4o-mini

MOCK_MODE=0 (ou 1 para demo)

PORT=10000 (Render injeta automaticamente; o gunicorn respeita)

Para rodar em provedores que exigem binding dinâmico de porta, use gunicorn (ele usa a env PORT).

