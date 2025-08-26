async function enviarEmail() {
    const btn = document.getElementById("btnAnalisar");
    const texto_email = document.getElementById("texto_email").value.trim();
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
        const resposta = await fetch("/processar_email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto_email })
        });

        let dados = {};
        try { dados = await resposta.json(); } catch (_) { dados = {}; }

        if (!resposta.ok) {
            const msg = (dados && dados.erro) ? dados.erro : ("Erro " + resposta.status);
            alerta.innerText = msg;
            alerta.style.display = "block";
            return;
        }

        // Preenche os resultados
        categoriaSpan.innerText = dados.categoria ? dados.categoria : "-";
        respostaP.innerText = dados.sugestao_resposta ? dados.sugestao_resposta : "-";

        // Remove classes antigas antes de aplicar a nova
        resultado.classList.remove("produtivo", "improdutivo");

        if (dados.categoria === "Produtivo") {
            resultado.classList.add("produtivo");
        } else if (dados.categoria === "Improdutivo") {
            resultado.classList.add("improdutivo");
        }

        resultado.style.display = "block";
    } catch (e) {
        alerta.innerText = "Erro de rede ao comunicar com o servidor.";
        alerta.style.display = "block";
    } finally {
        btn.disabled = false;
        btn.innerText = "Analisar";
    }
}

// Evento no botão
document.getElementById("btnAnalisar").addEventListener("click", enviarEmail);

// Healthcheck simples
window.addEventListener("DOMContentLoaded", async function() {
    const health = document.getElementById("health");
    try {
        const r = await fetch("/healthz");
        health.textContent = r.ok ? "ok" : "falhou (" + r.status + ")";
    } catch (_) {
        health.textContent = "falhou (network)";
    }
});