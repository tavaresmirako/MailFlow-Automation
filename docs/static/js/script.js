function norm(s) {
    return (s || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, ""); // remove acentos
}

const PROD = [
    "status", "atualizacao", "prazo", "suporte", "problema", "erro", "falha",
    "relatorio", "documentacao", "entrega", "agendar", "reuniao",
    "orcamento", "proposta", "contrato", "pendencia", "protocolo",
    "ticket", "pedido", "anexo", "segue anexo", "fatura", "nota fiscal", "boleto"
];

const IMPROD = [
    "feliz natal", "feliz ano novo", "bom dia", "boa tarde", "boa noite",
    "parabens", "obrigado", "obrigada", "agradeco", "agradecemos", "abracos", "abraços"
];

const PROMO = [
    "promocao", "desconto", "oferta", "imperdivel", "cupom", "ganhe", "gratis",
    "gratuito", "aproveite", "compre agora", "propaganda", "publicidade", "spam"
];

const ANEXOS = ["anexo", "segue anexo", "em anexo", "anexado"];

const ID_RE = /(pedido|chamado|ticket|protocolo)\s*[:#-]?\s*(\d{3,})/i;
const URL_RE = /(https?:\/\/|www\.)/i;
const QMARK = /\?/;

function classificarLocal(texto) {
    const raw = (texto || "").trim();
    const t = norm(raw);

    let score = 0;

    const posHits = PROD.filter(k => t.includes(k));
    const negHits = IMPROD.filter(k => t.includes(k));
    const promoHit = PROMO.some(k => t.includes(k));
    const anexHit = ANEXOS.some(k => t.includes(k));
    const refMatch = raw.match(ID_RE);
    const hasQ = QMARK.test(raw);
    const hasURL = URL_RE.test(raw);

    score += 2 * posHits.length;
    score -= 2 * negHits.length;
    if (refMatch) score += 2;
    if (hasQ) score += 1;
    if (anexHit) score += 1;
    if (hasURL) score -= 2;
    if (promoHit) score -= 3;

    // saudação curta sem pedido
    const greetings = ["bom dia", "boa tarde", "boa noite", "ola", "olá", "hello", "hi"].some(g => t.includes(g));
    if (greetings && raw.length < 60 && posHits.length === 0 && !refMatch && !hasQ) {
        score -= 2;
    }

    const categoria = score >= 2 ? "Produtivo" : "Improdutivo";

    // sugestão
    let sugestao;
    if (categoria === "Produtivo") {
        const ref = refMatch ? `${refMatch[1].toLowerCase()} ${refMatch[2]}` : null;
        sugestao = `Olá! Registramos sua solicitação${ref ? " referente ao " + ref : ""}. Nossa equipe vai verificar e retornar em breve. Se possível, compartilhe anexos ou detalhes adicionais para agilizar o atendimento.`;
    } else {
        if (promoHit || hasURL) {
            sugestao = "Olá! Esta mensagem aparenta ser promocional e não requer ação da nossa equipe. Permanecemos à disposição.";
        } else {
            sugestao = "Obrigado pela mensagem! Não identificamos nenhuma ação necessária no momento. Se precisar de suporte, descreva a demanda.";
        }
    }

    return { categoria, sugestao_resposta: sugestao };
}

async function enviarEmail() {
    const btn = document.getElementById("btnAnalisar");
    const texto_email = (document.getElementById("texto_email").value || "").trim();
    const categoriaSpan = document.getElementById("categoria");
    const respostaP = document.getElementById("sugestao_resposta");
    const alerta = document.getElementById("alerta");
    const resultado = document.getElementById("resultado");

    alerta.style.display = "none";
    resultado.style.display = "none";

    if (!texto_email) {
        alerta.innerText = "O texto do e-mail não pode estar vazio.";
        alerta.style.display = "block";
        return;
    }

    btn.disabled = true;
    btn.innerText = "Analisando...";

    try {
        const dados = classificarLocal(texto_email);
        categoriaSpan.textContent = dados.categoria;
        respostaP.textContent = dados.sugestao_resposta;
        resultado.style.display = "block";
    } catch (err) {
        alerta.innerText = `Erro: ${err.message || err}`;
        alerta.style.display = "block";
    } finally {
        btn.disabled = false;
        btn.innerText = "Analisar";
    }
}