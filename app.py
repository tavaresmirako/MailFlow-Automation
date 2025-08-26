import os
import re
import json
import logging
import unicodedata
from typing import Any, Dict, Optional, Tuple

from flask import Flask, render_template, request, jsonify, abort
from flask_cors import CORS
from dotenv import load_dotenv

# ===================== Config =====================
load_dotenv()

API_KEY   = (os.getenv("OPENAI_API_KEY") or "").strip()
MODEL     = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
MOCK_MODE = (os.getenv("MOCK_MODE") or "0").strip().lower() in ("1", "true", "yes")
VERBOSE   = (os.getenv("DEBUG_VERBOSE") or "0").strip().lower() in ("1", "true", "yes")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB

# ===== Ativar CORS (antes das rotas) =====
# Ajuste via .env se quiser:
# FRONTEND_ORIGIN=https://tavaresmirako.github.io
# FRONTEND_ORIGIN2=https://tavaresmirako.github.io/MailFlow-Automation
frontend_origin  = (os.getenv("FRONTEND_ORIGIN")  or "https://tavaresmirako.github.io").strip()
frontend_origin2 = (os.getenv("FRONTEND_ORIGIN2") or "https://tavaresmirako.github.io/MailFlow-Automation").strip()

CORS(
    app,
    resources={r"/*": {"origins": [frontend_origin, frontend_origin2, "*"]}},  # "*" apenas para testes
    supports_credentials=False,
    allow_headers="*",
    methods=["GET", "POST", "OPTIONS"],
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
log = logging.getLogger("mailflow")

# Só importa OpenAI quando realmente for usar
client = None
if not MOCK_MODE:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY)
    except Exception:
        log.exception("Falha ao inicializar OpenAI")
        # segue adiante; as chamadas retornarão fallback

# ===================== Utils comuns =====================
def _limpa_json_bruto(txt: str) -> str:
    if not txt:
        return txt
    t = txt.strip()
    if t.startswith("```"):
        t = t.split("```", 1)[-1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
        if "```" in t:
            t = t.rsplit("```", 1)[0]
    return t.strip()

def _parse_json_seguro(txt: str) -> Optional[Dict[str, Any]]:
    if not txt:
        return None
    for candidate in (txt, _limpa_json_bruto(txt)):
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return None

def _fallback() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "sugestao_resposta": (
            "Olá! Não consegui processar sua solicitação agora. "
            "Pode reenviar com mais detalhes, por favor?"
        ),
    }

def _norm(s: str) -> str:
    """minúsculas + remove acentos."""
    s = s.lower()
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))

def _normaliza_categoria(val: Optional[str]) -> str:
    if not val:
        return "Improdutivo"
    v = _norm(val)
    if "produt" in v:
        return "Produtivo"
    if "improdut" in v:
        return "Improdutivo"
    return "Improdutivo"

# ===================== Classificador MOCK =====================
_ID_RE   = re.compile(r'(pedido|chamado|ticket|protocolo)\s*[:#-]?\s*(\d{3,})', re.I)
_URL_RE  = re.compile(r'(https?://|www\.)', re.I)
_QMARK   = re.compile(r'\?')

def _classificar_mock(texto_email: str) -> Tuple[str, str]:
    raw = (texto_email or "").strip()
    t = _norm(raw)

    produtivas = {
        "status","atualizacao","prazo","suporte","problema","erro","relatorio",
        "entrega","agendar","reuniao","orcamento","proposta","contrato","pendencia",
        "protocolo","ticket","pedido","anexo","fatura","nota fiscal","boleto"
    }
    improdutivas = {"bom dia","boa tarde","boa noite","parabens","obrigado","obrigada"}

    score = 0
    if any(k in t for k in produtivas):   score += 2
    if any(k in t for k in improdutivas): score -= 2

    # Exemplos extras que podem influenciar
    if _ID_RE.search(raw): score += 1         # referência formal ajuda
    if _URL_RE.search(raw): score -= 1        # link solto pode ser ruído
    if _QMARK.search(raw):  score += 1        # pergunta sugere chamada à ação

    categoria = "Produtivo" if score >= 2 else "Improdutivo"
    sugestao = (
        "Olá! Registramos sua solicitação. Nossa equipe vai verificar e retornar em breve."
        if categoria == "Produtivo"
        else "Obrigado pela mensagem! Não identificamos ação necessária. Se precisar de suporte, descreva a demanda."
    )
    return categoria, sugestao

# ===================== Rotas =====================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route("/processar_email", methods=["POST"])
def processar_email():
    if not request.is_json:
        abort(400, description="Envie JSON no corpo (Content-Type: application/json).")
    dados = request.get_json(silent=True) or {}
    texto_email = (dados.get("texto_email") or "").strip()
    if not texto_email:
        return jsonify({"erro": "O texto do e-mail não pode estar vazio."}), 400

    # ---------- MOCK ----------
    if MOCK_MODE:
        log.info("MOCK_MODE=on → classificador simples")
        categoria, sugestao = _classificar_mock(texto_email)
        return jsonify({"categoria": categoria, "sugestao_resposta": sugestao}), 200

    # ---------- OPENAI REAL ----------
    if not API_KEY:
        return jsonify({"erro": "OPENAI_API_KEY ausente"}), 500
    if client is None:
        return jsonify({"erro": "Cliente OpenAI não inicializado"}), 500

    prompt = f"""
Classifique este e-mail em "Produtivo" ou "Improdutivo" e sugira uma resposta curta.
Responda APENAS em JSON válido com as chaves "categoria" e "sugestao_resposta".

E-mail:
---
{texto_email}
---
"""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            timeout=40,
        )
        if not resp or not getattr(resp, "choices", None) or not resp.choices[0].message:
            log.warning("OpenAI sem choices/mensagem.")
            return jsonify(_fallback()), 502

        content = resp.choices[0].message.content
        parsed = _parse_json_seguro(content)
        if not parsed:
            return jsonify(_fallback()), 502

        categoria = _normaliza_categoria(parsed.get("categoria"))
        sugestao = (parsed.get("sugestao_resposta") or "").strip() or _fallback()["sugestao_resposta"]

        return jsonify({"categoria": categoria, "sugestao_resposta": sugestao}), 200

    except Exception as e:
        log.exception("Erro na OpenAI")
        # Se VERBOSE ativo, devolve mais detalhes
        msg = "Erro ao comunicar com a IA."
        if VERBOSE:
            msg += f" Detalhes: {type(e).__name__}: {e}"
        return jsonify({"erro": msg}), 502

# ===================== Run =====================
if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "8000"))
    app.run(host=host, port=port, debug=True)
