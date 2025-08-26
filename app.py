import os
import re
import json
import logging
import unicodedata
from typing import Any, Dict, Optional, Tuple

from flask import Flask, render_template, request, jsonify, abort
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

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
log = logging.getLogger("mailflow")

# Só importa OpenAI quando realmente for usar
client = None
if not MOCK_MODE:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY)
    except Exception as e:
        log.exception("Falha ao inicializar OpenAI")
        # Se der erro de import/SDK, continuamos mas retornaremos erro claro nas chamadas


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
    # Qualquer outra coisa, caímos para improdutivo por segurança
    return "Improdutivo"


# ===================== Classificador MOCK (score) =====================
_ID_RE   = re.compile(r'(pedido|chamado|ticket|protocolo)\s*[:#-]?\s*(\d{3,})', re.I)
_URL_RE  = re.compile(r'(https?://|www\.)', re.I)
_QMARK   = re.compile(r'\?')

def _classificar_mock(texto_email: str) -> Tuple[str, str]:
    """
    Score determinístico para separar Produtivo x Improdutivo.
    Regras (exemplos):
      +2 por palavra-chave produtiva
      -2 por palavra-chave improdutiva (saudação/elogio social)
      +2 se tiver referência (pedido/chamado/ticket/protocolo + número)
      +1 se tiver interrogação (indica pedido)
      +1 se mencionar anexo
      -2 se tiver URL
      -3 se tiver termos promocionais (tendência spam)
      -2 se for só saudação curta sem pedido
    """
    raw = (texto_email or "").strip()
    t = _norm(raw)

    produtivas = {
        "status","atualizacao","prazo","suporte","problema","erro","falha",
        "relatorio","documentacao","entrega","agendar","reuniao",
        "orcamento","proposta","contrato","pendencia","protocolo",
        "ticket","pedido","anexo","segue anexo","fatura","nota fiscal","boleto"
    }
    improdutivas = {
        "feliz natal","feliz ano novo","bom dia","boa tarde","boa noite",
        "parabens","obrigado","obrigada","agradeco","agradecemos","abraços","abracos"
    }
    promo = {
        "promocao","desconto","oferta","imperdivel","cupom","ganhe","gratis",
        "gratuito","aproveite","compre agora","propaganda","publicidade","spam"
    }
    anexos = {"anexo","segue anexo","em anexo","anexado"}

    score = 0

    pos_hits = [k for k in produtivas if k in t]
    neg_hits = [k for k in improdutivas if k in t]
    promo_hit = any(k in t for k in promo)
    anex_hit  = any(k in t for k in anexos)
    ref_match = _ID_RE.search(raw)
    has_q     = bool(_QMARK.search(raw))
    has_url   = bool(_URL_RE.search(raw))

    score += 2 * len(pos_hits)
    score -= 2 * len(neg_hits)
    if ref_match: score += 2
    if has_q:     score += 1
    if anex_hit:  score += 1
    if has_url:   score -= 2
    if promo_hit: score -= 3

    # saudações curtas sem pedido → improdutivo
    greetings = any(g in t for g in ["bom dia","boa tarde","boa noite","ola","olá","hello","hi"])
    if greetings and len(raw) < 60 and not (pos_hits or ref_match or has_q):
        score -= 2

    categoria = "Produtivo" if score >= 2 else "Improdutivo"

    # Resposta contextual
    ref = None
    if ref_match:
        ref = f"{ref_match.group(1).lower()} {ref_match.group(2)}"

    if categoria == "Produtivo":
        sugestao = (
            f"Olá! Registramos sua solicitação{(' referente ao ' + ref) if ref else ''}. "
            "Nossa equipe vai verificar e retornar com uma atualização em breve. "
            "Se possível, compartilhe anexos ou detalhes adicionais para agilizar o atendimento."
        )
    else:
        if promo_hit or has_url:
            sugestao = "Olá! Esta mensagem aparenta ser promocional e não requer ação da nossa equipe. Permanecemos à disposição."
        else:
            sugestao = "Obrigado pela mensagem! Não identificamos nenhuma ação necessária no momento. Se precisar de suporte, descreva a demanda."
    return categoria, sugestao


# ===================== Rotas =====================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route("/diag")
def diag():
    return jsonify({
        "mock_mode": MOCK_MODE,
        "model": MODEL,
        "has_api_key": bool(API_KEY),
        "template_ok": os.path.exists(os.path.join(app.template_folder, "index.html")),
        "static_js_ok": os.path.exists(os.path.join(app.static_folder, "js", "script.js")),
        "static_css_ok": os.path.exists(os.path.join(app.static_folder, "css", "style.css")),
    }), 200

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
        log.info("MOCK_MODE=on → classificador por score.")
        categoria, sugestao = _classificar_mock(texto_email)
        return jsonify({"categoria": categoria, "sugestao_resposta": sugestao}), 200

    # ---------- OPENAI REAL ----------
    if not API_KEY:
        return jsonify({"erro": "OPENAI_API_KEY ausente no .env."}), 500
    if client is None:
        return jsonify({"erro": "Cliente OpenAI não inicializado."}), 500

    prompt = f"""
Você é um classificador de e-mails corporativos.

Tarefas:
1) Classifique o e-mail em EXATAMENTE UMA categoria: "Produtivo" ou "Improdutivo".
2) Gere uma resposta curta, objetiva e profissional, adequada à categoria.

Regras:
- Responda APENAS com JSON VÁLIDO.
- Chaves: "categoria" e "sugestao_resposta".
- "categoria" deve ser exatamente "Produtivo" ou "Improdutivo" (nada além disso).
- Não inclua texto fora do JSON.

E-mail:
---
{texto_email}
---
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Você responde sempre em JSON válido com as chaves solicitadas."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            timeout=40,
        )

        if not resp or not getattr(resp, "choices", None) or not resp.choices[0].message:
            log.warning("OpenAI sem choices/mensagem.")
            return jsonify(_fallback()), 502

        content = resp.choices[0].message.content
        parsed = _parse_json_seguro(content)
        if not parsed or not isinstance(parsed, dict):
            log.warning(f"Falha ao parsear JSON da IA: {content!r}")
            return jsonify(_fallback()), 502

        categoria = _normaliza_categoria(parsed.get("categoria"))
        sugestao = (parsed.get("sugestao_resposta") or "").strip() or _fallback()["sugestao_resposta"]

        return jsonify({"categoria": categoria, "sugestao_resposta": sugestao}), 200

    except Exception as e:
        log.exception("Erro ao chamar a OpenAI")
        msg = "Erro ao comunicar com a IA."
        if VERBOSE:
            msg += f" Detalhes: {type(e).__name__}: {e}"
        return jsonify({"erro": msg}), 502


# ===================== Handlers de erro =====================
@app.errorhandler(400)
def h400(err): return jsonify({"erro": getattr(err, "description", "Requisição inválida.")}), 400
@app.errorhandler(404)
def h404(_):  return jsonify({"erro": "Rota não encontrada."}), 404
@app.errorhandler(405)
def h405(_):  return jsonify({"erro": "Método HTTP não permitido."}), 405
@app.errorhandler(413)
def h413(_):  return jsonify({"erro": "Payload muito grande."}), 413
@app.errorhandler(500)
def h500(_):  return jsonify({"erro": "Erro interno do servidor."}), 500


# ===================== Run =====================
if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "8000"))
    app.run(host=host, port=port, debug=True, use_reloader=True)
