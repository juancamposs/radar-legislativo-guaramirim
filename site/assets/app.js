/* Radar Legislativo de Guaramirim — site estático, lê dados/radar.json */
(() => {
  "use strict";
  const CONTATO = {
    whatsapp: "554733709463", // Fone/Whats público do escritório (47) 3370-9463
    site: "https://adrianomachadoadvocacia.com.br/",
  };
  const $main = document.getElementById("conteudo");
  let D = null;

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const dt = (iso) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "—");
  const n = (x) => Number(x || 0).toLocaleString("pt-BR");
  const pct = (a, b) => (b ? Math.round((a / b) * 1000) / 10 : null);
  const norm = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const ver = (slug) => D.vereadores.find((v) => v.slug === slug);
  const nomeVer = (slug) => (ver(slug) || {}).nome || slug;
  const link = (url, txt) => (url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${txt}</a>` : `<span class="indisp">dado indisponível</span>`);
  const selo = (g) => `<span class="selo ${g}">${esc(D.grupos[g] || g)}</span>`;
  const periodoTxt = () => `de ${dt(D.periodo.inicio)} a ${dt(D.periodo.fim)}`;
  const periodoBox = (extra = "") => `<p class="periodo"><span>Período consultado:</span> <strong>${periodoTxt()}</strong>${extra}</p>`;
  const iniciais = (nome) => nome.split(/\s+/).filter((p) => p.length > 2).slice(0, 2).map((p) => p[0]).join("");
  const semFoto = (v) => `<span class="foto" aria-hidden="true" style="display:grid;place-items:center;font:600 20px var(--serif);color:var(--dourado-forte)">${esc(iniciais(v.nome))}</span>`;
  const foto = (v) => v.foto
    ? `<img class="foto" src="${esc(v.foto)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.outerHTML=this.dataset.f" data-f="${esc(semFoto(v))}">`
    : semFoto(v);

  function itemMateria(m, mostrarAutor = true) {
    return `<li>
      <div class="item-t">${link(m.url, esc(m.titulo))}</div>
      <p class="item-e">${esc(m.ementa)}</p>
      <div class="item-m"><span>${dt(m.data)}</span>${mostrarAutor ? `<span>· ${esc(m.autoria || "autoria não informada")}</span>` : ""}${selo(m.grupo)}${m.situacao ? `<span>· ${esc(m.situacao)}</span>` : ""}</div>
    </li>`;
  }

  function listaPaginada(itens, render, passo = 20) {
    const id = "l" + Math.random().toString(36).slice(2, 8);
    setTimeout(() => {
      const ul = document.getElementById(id), bt = document.getElementById(id + "b");
      if (!ul) return;
      let mostrados = 0;
      const mais = () => {
        ul.insertAdjacentHTML("beforeend", itens.slice(mostrados, mostrados + passo).map(render).join(""));
        mostrados += passo;
        if (bt) bt.hidden = mostrados >= itens.length;
      };
      mais();
      bt && bt.addEventListener("click", mais);
    });
    if (!itens.length) return `<p class="vazio">Nenhum registro no período.</p>`;
    return `<ul class="lista" id="${id}"></ul>${itens.length > passo ? `<button class="botao claro mais" id="${id}b">Mostrar mais</button>` : ""}`;
  }

  // ------------------------------------------------------------ páginas
  function pgInicio() {
    const totalM = D.materias.length;
    const nominais = D.votacoes.filter((v) => v.nominal).length;
    const comLista = D.sessoes.filter((s) => s.presentes).length;
    const vs = [...D.vereadores].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
    return `
      <h1>O que fazem os vereadores de Guaramirim</h1>
      <p class="lead">Presenças, propostas e votos de cada vereador, só com documentos oficiais da Câmara Municipal. Toque em um nome para ver a ficha. Os vereadores aparecem em ordem alfabética: aqui não há nota nem ranking.</p>
      ${periodoBox(` <span>· legislatura ${esc(D.periodo.legislatura)}</span>`)}
      <div class="numeros" role="list">
        <div class="num" role="listitem"><div class="v">${n(totalM)}</div><div class="r">matérias de vereadores e do Executivo na listagem oficial</div></div>
        <div class="num" role="listitem"><div class="v">${n(D.sessoes.length)}</div><div class="r">sessões plenárias com ata publicada</div></div>
        <div class="num" role="listitem"><div class="v">${n(comLista)}</div><div class="r">atas com lista de presença lida no PDF</div></div>
        <div class="num" role="listitem"><div class="v">${n(nominais)}</div><div class="r">votações com voto de cada vereador registrado</div></div>
      </div>
      <h2>Vereadores em exercício</h2>
      <div class="grade vers">
        ${vs.map((v) => `<a class="cartao ver-card" href="#/vereador/${v.slug}">${foto(v)}<span><span class="nome">${esc(v.nome)}</span><br><span class="meta">${esc(v.partido || "partido: dado indisponível")}</span></span></a>`).join("")}
      </div>
      <h2>Procure pelo seu bairro ou rua</h2>
      <form class="busca" onsubmit="location.hash='#/bairros?q='+encodeURIComponent(this.q.value);return false" role="search">
        <label class="sr" for="qhome">Bairro ou rua</label>
        <input id="qhome" name="q" placeholder="Ex.: Bananal do Sul, Rua 385, Avaí" autocomplete="off">
        <button>Buscar</button>
      </form>
      <p class="aviso cinza" style="margin-top:14px">Este é um projeto do <strong>Adriano Machado Advocacia</strong>. A fonte dos dados é a <strong>Câmara Municipal de Guaramirim</strong>. Veja <a href="#/metodo">como os números são calculados</a> e <a href="#/metodo#lacunas">o que ainda falta</a>.</p>`;
  }

  function pgVereador(slug) {
    const v = ver(slug);
    if (!v) return `<p>Vereador não encontrado. <a href="#/">Voltar</a></p>`;
    const mats = D.materias.filter((m) => m.autores.includes(slug));
    const p = v.presenca;
    const percP = pct(p.presente, p.sessoes_com_lista);
    const votos = D.votacoes.filter((x) => x.nominal);
    const meus = votos.filter((x) => x.votos[slug]);
    const ordemG = ["bairros", "informacao", "homenagens", "leis", "outros"];
    return `
      <p><a href="#/">← Todos os vereadores</a></p>
      <div style="display:flex;gap:14px;align-items:center">${foto(v)}<div><h1 style="margin:0">${esc(v.nome)}</h1>
        <div class="item-m">${esc(v.partido || "Partido: dado indisponível")}${v.url_ficha ? ` · ${link(v.url_ficha, "ficha oficial na Câmara")}` : ""}</div></div></div>
      ${v.cargos && v.cargos.length ? `<p class="item-m">${v.cargos.map(esc).join(" · ")}</p>` : ""}
      ${periodoBox()}
      <div class="numeros">
        <div class="num"><div class="v">${p.sessoes_com_lista ? n(p.presente) + " de " + n(p.sessoes_com_lista) : "—"}</div>
          <div class="r">sessões em que o nome consta na lista de presença da ata</div>
          <span class="calc">CALCULADO${percP !== null ? " · " + String(percP).replace(".", ",") + "%" : ""}</span> <a href="#/sessoes?v=${slug}">ver sessões</a></div>
        <div class="num"><div class="v">${n(mats.length)}</div><div class="r">matérias com o nome na autoria</div><span class="calc">CONTAGEM</span></div>
        <div class="num"><div class="v">${n(v.votos_nominais.registrados)} de ${n(votos.length)}</div><div class="r">votações nominais com voto dado${v.votos_nominais.ausente_na_votacao ? ` · ${n(v.votos_nominais.ausente_na_votacao)} como ausente` : ""}</div><span class="calc">CONTAGEM</span> <a href="#/votacoes?v=${slug}">ver votos</a></div>
        <div class="num"><div class="v">${n(v.materias_por_grupo.bairros)}</div><div class="r">pedidos de melhoria em bairros</div><span class="calc">CLASSIFICAÇÃO</span></div>
      </div>
      ${p.sessoes_sem_lista ? `<p class="aviso cinza">${n(p.sessoes_sem_lista)} sessão(ões) do período não têm lista de presença legível na ata em PDF: nelas a presença é <strong>dado indisponível</strong> e não entra na conta.</p>` : ""}
      <p class="item-m">Presidente da sessão não vota em votações comuns; licenças e faltas justificadas não aparecem nesta conta. Veja <a href="#/metodo#calculos">como calculamos</a>.</p>
      ${v.contatos && v.contatos.length ? `<h2>Contato público do gabinete</h2><p>${v.contatos.map(esc).join("<br>")}</p>` : ""}
      <h2>Propostas por grupo</h2>
      <p class="item-m">Toque em um grupo para ler matéria por matéria. <a href="#/metodo#regras">Como classificamos</a>.</p>
      ${ordemG.map((g) => {
        const lista = mats.filter((m) => m.grupo === g);
        return `<details class="grupo"><summary><span>${esc(D.grupos[g])}</span><span class="selo ${g}">${n(lista.length)}</span></summary><div class="corpo">${listaPaginada(lista, (m) => itemMateria(m, true), 15)}</div></details>`;
      }).join("")}
      <h2>Votos nominais</h2>
      <p class="item-m">As atas passaram a trazer o nome de quem votou a partir de ${dt(v.votos_nominais.primeira_nominal)}. Antes disso, só o resultado geral está disponível (veja <a href="#/votacoes">Votações</a>).</p>
      ${listaPaginada(votos, (x) => {
        const r = x.votos[slug];
        const cls = r === "favoraveis" ? "voto-fav" : r === "contrarios" ? "voto-con" : "voto-out";
        const txt = r ? rotuloVoto(r) : "sem voto registrado";
        return `<li><div class="item-t">${x.materia_id ? link(D.materias.find((m) => m.id === x.materia_id)?.url, esc(x.materia)) : esc(x.materia)}</div>
          <p class="item-e">${esc(x.ementa)}</p>
          <div class="item-m"><span>${dt(x.data)}</span><span>· ${esc(x.turno)}</span><span>· resultado: ${esc(x.resultado)}</span><span>· voto: <span class="${r ? cls : "indisp"}">${esc(txt)}</span></span><span>· ${link(x.ata_url, "ata")}</span></div></li>`;
      }, 10)}`;
  }

  const rotuloVoto = (r) => ({ favoraveis: "favorável", contrarios: "contrário", abstencoes: "abstenção", abstencao: "abstenção", ausentes: "ausente" }[r] || r.replace(/_/g, " "));

  function pgBairros(q) {
    setTimeout(() => {
      const f = document.getElementById("fb");
      f.addEventListener("submit", (e) => { e.preventDefault(); location.hash = "#/bairros?q=" + encodeURIComponent(f.q.value); });
    });
    const sugest = topLocais(12);
    let res = "";
    if (q) {
      const nq = norm(q).replace(/\bn[º°o]?\.?\s*/g, "").trim();
      const termos = nq.split(/\s+/).filter(Boolean);
      const achados = D.materias.filter((m) => {
        const alvo = norm([m.vias.join(" "), m.bairros.join(" "), m.ementa].join(" ")).replace(/\bn[º°o]?\.?\s*/g, "");
        return termos.every((t) => alvo.includes(t));
      });
      const grupos = agrupaLocais(achados, termos);
      res = `<h2>Resultados para “${esc(q)}”</h2>
        <p>${n(achados.length)} matéria(s) mencionam esse lugar no período ${periodoTxt()}.</p>
        <p class="aviso"><strong>Atenção:</strong> quando o mesmo pedido aparece várias vezes para o mesmo lugar, isso mostra que ele foi repetido na Câmara. <strong>A repetição, sozinha, não prova que a Prefeitura deixou de atender</strong> — o pedido pode ter sido atendido em parte, estar em andamento ou depender de orçamento.</p>
        ${grupos.map((g) => `<section class="repete"><div class="cont">${esc(g.local)} — ${esc(g.assunto)}: ${n(g.itens.length)} pedido(s)</div>
          <div class="item-m">Datas: ${g.itens.map((m) => dt(m.data)).join(", ")} · Autoria: ${[...new Set(g.itens.flatMap((m) => m.autores.map(nomeVer)))].map(esc).join(", ") || "—"}</div>
          <ul class="lista">${g.itens.map((m) => itemMateria(m)).join("")}</ul></section>`).join("")}
        ${achados.length && !grupos.length ? `<ul class="lista">${achados.map((m) => itemMateria(m)).join("")}</ul>` : ""}`;
    }
    return `<h1>Busca por bairro ou rua</h1>
      <p class="lead">Digite um bairro, rua ou estrada e veja o que foi pedido para lá, por quem e quando.</p>
      ${periodoBox()}
      <form class="busca" id="fb" role="search"><label class="sr" for="qb">Bairro ou rua</label>
        <input id="qb" name="q" value="${esc(q || "")}" placeholder="Ex.: Ilha da Figueira, Rua 385, Estrada Bananal do Sul" autocomplete="off"><button>Buscar</button></form>
      <div class="chips" aria-label="Lugares mais citados">${sugest.map((s) => `<a class="chip" href="#/bairros?q=${encodeURIComponent(s)}">${esc(s)}</a>`).join("")}</div>
      ${res || `<p class="item-m">Os lugares acima são os mais citados nas indicações do período. Ruas numeradas podem ser buscadas pelo número (ex.: “Rua 385”).</p>`}
      <p class="item-m">Como agrupamos: pedidos são juntados quando citam a <strong>mesma via</strong> (ruas numeradas pelo número oficial) e tratam do <strong>mesmo assunto</strong> (ex.: pavimentação, drenagem, iluminação). O agrupamento é automático e cada grupo mostra os documentos que o sustentam. <a href="#/metodo#lugares">Detalhes</a>.</p>`;
  }

  function chaveLocal(t) {
    let x = norm(t);
    const m = x.match(/^(rua|servidao|estrada|travessa) n[º°o]?\.?\s*(\d+)/);
    if (m) return m[1] + " " + m[2];
    return x.replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  }
  function agrupaLocais(mats, termos) {
    const g = new Map();
    for (const m of mats) {
      if (m.grupo !== "bairros") continue;
      const locs = m.vias.length ? m.vias : m.bairros.map((b) => "Bairro " + b);
      for (const l of locs) {
        const k = chaveLocal(l);
        if (termos && !termos.every((t) => (k + " " + norm(l)).includes(t)) && !termos.every((t) => norm(m.bairros.join(" ")).includes(t))) continue;
        const key = k + "|" + (m.assunto || "");
        if (!g.has(key)) g.set(key, { local: l, assunto: m.assunto || "Outros serviços", itens: [] });
        const it = g.get(key);
        if (!it.itens.includes(m)) it.itens.push(m);
        if (l.length > it.local.length) it.local = l;
      }
    }
    return [...g.values()].sort((a, b) => b.itens.length - a.itens.length || a.local.localeCompare(b.local));
  }
  function topLocais(k) {
    const c = new Map();
    for (const m of D.materias) for (const b of m.bairros) c.set(b, (c.get(b) || 0) + 1);
    return [...c.entries()].sort((a, b) => b[1] - a[1]).slice(0, k).map((x) => x[0]);
  }

  function pgVotacoes(vslug) {
    const lista = [...D.votacoes].reverse();
    const nom = lista.filter((v) => v.nominal).length;
    return `<h1>Votações em plenário</h1>
      ${periodoBox()}
      <p class="lead">Votações registradas nas atas publicadas. Quando a ata traz o nome de quem votou, mostramos o voto de cada vereador. Quando não traz, mostramos só o resultado geral.</p>
      <p>${n(lista.length)} votações · ${n(nom)} com registro nominal · ${n(lista.length - nom)} só com resultado geral. O registro nominal aparece nas atas a partir de ${dt((D.votacoes.find((x) => x.nominal) || {}).data)}.</p>
      ${vslug ? `<p class="periodo">Destacando o voto de <strong>${esc(nomeVer(vslug))}</strong> · <a href="#/votacoes">ver todas</a></p>` : ""}
      ${listaPaginada(lista, (x) => {
        const m = x.materia_id ? D.materias.find((mm) => mm.id === x.materia_id) : null;
        const grupos = {};
        Object.entries(x.votos).forEach(([s, r]) => (grupos[r] = grupos[r] || []).push(s));
        const det = x.nominal
          ? Object.entries(grupos).map(([r, ss]) => `<div><span class="${r === "favoraveis" ? "voto-fav" : r === "contrarios" ? "voto-con" : "voto-out"}">${esc(rotuloVoto(r))} (${ss.length}):</span> ${ss.map((s) => (s === vslug ? `<mark>${esc(nomeVer(s))}</mark>` : esc(nomeVer(s)))).join(", ")}</div>`).join("")
          : `<div class="indisp">Sem registro nominal na ata: só o resultado geral está disponível.</div>`;
        return `<li><div class="item-t">${m ? link(m.url, esc(x.materia)) : esc(x.materia)}</div>
          <p class="item-e">${esc(x.ementa)}</p>
          <div class="item-m"><span>${dt(x.data)}</span><span>· ${esc(x.turno)}</span><span>· resultado: <strong>${esc(x.resultado)}</strong></span><span>· ${link(x.ata_url, "ata oficial")}</span></div>
          <div style="font-size:14.5px;margin-top:4px">${det}</div></li>`;
      }, 15)}`;
  }

  function pgSessoes(vslug) {
    const lista = [...D.sessoes].reverse();
    return `<h1>Sessões e presenças</h1>
      ${periodoBox()}
      <p class="lead">Cada ata em PDF começa com a lista dos vereadores presentes. Lemos essa lista e mostramos aqui, com o link da ata.</p>
      ${vslug ? `<p class="periodo">Destacando <strong>${esc(nomeVer(vslug))}</strong> · <a href="#/sessoes">ver todas</a></p>` : ""}
      <div class="tabela"><table><thead><tr><th>Data</th><th>Sessão</th><th>Presentes (conforme a ata)</th><th>Fonte</th></tr></thead><tbody>
      ${lista.map((s) => {
        const pres = s.presentes
          ? (vslug ? (s.presentes.includes(vslug) ? `<span class="voto-fav">consta na lista</span>` : `<span class="voto-out">não consta na lista</span>`) + ` · ${s.presentes.length} presentes` : `${s.presentes.length}: ${s.presentes.map(nomeVer).map(esc).join(", ")}`)
          : `<span class="indisp">dado indisponível</span>`;
        return `<tr><td>${dt(s.data)}</td><td>${esc(s.titulo.replace("Ata da ", ""))}${s.numero_ata ? `<br><span class="item-m">Ata nº ${esc(s.numero_ata)}</span>` : ""}</td><td>${pres}</td><td>${link(s.url, "página")}${s.pdf ? " · " + link(s.pdf, "PDF") : ""}</td></tr>`;
      }).join("")}
      </tbody></table></div>
      <p class="item-m">“Não consta na lista” significa apenas que o nome não aparece na lista de presença da ata. Pode ter havido licença, falta justificada ou suplente em exercício — a ata nem sempre registra o motivo.</p>`;
  }

  function pgMetodo() {
    const lac = D.lacunas || [];
    return `<h1>Como funciona</h1>
      ${periodoBox(` · atualizado em ${dt(D.gerado_em)}`)}
      <h2 id="fontes">Fontes oficiais</h2>
      <ul>
        <li>Matérias (indicações, moções, pedidos de informação, requerimentos, projetos): ${link(D.fontes.materias, "Matérias em Tramitação")}</li>
        <li>Atas das sessões plenárias, com votações e PDF assinado: ${link(D.fontes.atas, "Atas — Sessões Plenárias")}</li>
        <li>Vereadores em exercício: ${link(D.fontes.vereadores, "página oficial")}</li>
        <li>API de dados abertos da Câmara: ${link(D.fontes.dados_abertos, "Dados Abertos")}</li>
        <li>Portal da Transparência da Câmara: ${link(D.fontes.transparencia, "camaraguaramirim.atende.net")}</li>
      </ul>
      <h2 id="regras">Como classificamos as propostas</h2>
      <p>A mesma regra vale para todos os vereadores. Ela é aplicada nesta ordem; a primeira que servir define o grupo:</p>
      <ol>${D.regras.map(([g, t]) => `<li>${selo(g)} ${esc(t)}</li>`).join("")}</ol>
      <p class="item-m">A classificação é automática, feita por palavras do texto oficial (ementa). Pode errar em casos de fronteira; por isso cada matéria tem o link do documento original.</p>
      <h2 id="calculos">Indicadores calculados</h2>
      <ul>
        <li><strong>Presença</strong> = número de atas em cuja lista de presença o nome aparece ÷ número de atas do período com lista de presença legível. Atas sem lista legível ficam fora da conta (dado indisponível).</li>
        <li><strong>Votos nominais</strong> = votações em que a ata traz os nomes de quem votou. O presidente da sessão, em regra, não vota; por isso o nome dele pode não aparecer.</li>
        <li><strong>Matérias por vereador</strong> = matérias em que o nome está no campo “Autoria” da página oficial. Matérias em coautoria contam para cada coautor.</li>
        <li>Nenhum número é nota ou avaliação. Não há ranking.</li>
      </ul>
      <h2 id="lugares">Busca por lugar e pedidos repetidos</h2>
      <p>Lemos no texto das indicações os nomes de ruas, estradas, servidões e bairros. Pedidos são agrupados quando citam a mesma via (ruas numeradas pelo número oficial) e tratam do mesmo assunto. Repetição de pedido <strong>não</strong> indica, por si só, que a demanda não foi atendida.</p>
      <h2 id="lacunas">O que ainda falta (lacunas conhecidas)</h2>
      ${lac.length ? `<div class="tabela"><table><thead><tr><th>Tipo</th><th>Ano</th><th>Encontradas</th><th>Maior número</th><th>Faltando</th></tr></thead><tbody>${lac.map((l) => `<tr><td>${esc(l.tipo)}</td><td>${l.ano}</td><td>${n(l.encontradas)}</td><td>${n(l.maior_numero)}</td><td>${n(l.faltando)}</td></tr>`).join("")}</tbody></table></div>
      <p class="item-m">“Faltando” = números da sequência oficial que não aparecem na listagem pública de matérias. Os projetos de lei do Poder Executivo, em geral, não aparecem nessa listagem; quando são votados, aparecem na seção Votações a partir das atas.</p>` : "<p>Nenhuma lacuna de numeração encontrada.</p>"}
      <h2 id="correcoes">Pedir correção</h2>
      <p>Viu um número errado, um nome trocado ou uma matéria fora do grupo certo? Avise com o link da matéria ou da ata. Corrigimos e registramos a correção.</p>
      <p><a class="botao" href="https://wa.me/${CONTATO.whatsapp}?text=${encodeURIComponent("Olá! Encontrei um possível erro no Radar Legislativo de Guaramirim: ")}" target="_blank" rel="noopener">Pedir correção pelo WhatsApp</a>
      <a class="botao claro" href="${CONTATO.site}" target="_blank" rel="noopener">Site do escritório</a></p>
      <p class="item-m">Canal do Adriano Machado Advocacia: (47) 3370-9463.</p>`;
  }

  // ------------------------------------------------------------ rotas
  function rota() {
    if (!D) return;
    const h = location.hash.replace(/^#\/?/, "");
    const [caminho, qs] = h.split("?");
    const params = new URLSearchParams(qs || "");
    const partes = caminho.split("/");
    let html, ativo = partes[0];
    if (partes[0] === "vereador") { html = pgVereador(partes[1]); ativo = ""; }
    else if (partes[0] === "bairros") html = pgBairros(params.get("q"));
    else if (partes[0] === "votacoes") html = pgVotacoes(params.get("v"));
    else if (partes[0] === "sessoes") html = pgSessoes(params.get("v"));
    else if (partes[0] === "metodo") html = pgMetodo();
    else { html = pgInicio(); ativo = ""; }
    $main.innerHTML = html;
    document.querySelectorAll(".nav a").forEach((a) => a.toggleAttribute("aria-current", a.dataset.rota === ativo) || a.removeAttribute("aria-current"));
    document.querySelectorAll(".nav a").forEach((a) => { if (a.dataset.rota === ativo) a.setAttribute("aria-current", "page"); });
    const ancora = location.hash.split("#")[2];
    if (ancora) document.getElementById(ancora)?.scrollIntoView(); else window.scrollTo(0, 0);
  }

  fetch("dados/radar.json", { cache: "no-cache" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((j) => {
      D = j;
      document.getElementById("atualizado").textContent = `Dados atualizados em ${new Date(D.gerado_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })} · período ${periodoTxt()}.`;
      rota();
    })
    .catch(() => { $main.innerHTML = `<p class="aviso">Não foi possível carregar os dados agora. Tente de novo em alguns minutos.</p>`; });
  window.addEventListener("hashchange", rota);
})();
