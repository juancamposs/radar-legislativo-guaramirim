"""Gera site/dados/radar.json a partir dos dados brutos oficiais.

Entradas (dados/brutos/):
  navegador-materias.json   listagem /tramitacoes (HTML bruto por página)
  navegador-atas.json       atas plenárias (HTML bruto por ata)
  navegador-vereadores.json fichas dos vereadores em exercício
  presencas-pdf.json        presenças extraídas dos PDFs das atas (gerado por pdf_atas.py)
  api-*.json                respostas da API de dados abertos (quando houver token)

Saída: site/dados/radar.json (+ relatorio-coleta.json com contagens e avisos).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classificar import GRUPOS, REGRAS_TEXTO, assunto, chave_local, classificar, extrair_locais  # noqa: E402
from parse_portal import chave_nome, limpa, parse_ata, parse_lista_materias, sem_acento, separa_autores  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
SAIDA = RAIZ / "site" / "dados"
CONF = json.loads((RAIZ / "config" / "vereadores.json").read_text())
INICIO = CONF["inicio_periodo"]


def carrega(nome: str, padrao=None):
    p = BRUTOS / nome
    return json.loads(p.read_text()) if p.exists() else padrao


# ---------------------------------------------------------------- nomes
def monta_resolvedor():
    idx = {}
    for v in CONF["vereadores"]:
        for n in [v["nome"], *v.get("apelidos", [])]:
            idx[chave_nome(n)] = v["slug"]
    nao_resolvidos = Counter()

    def resolve(nome: str) -> str | None:
        k = chave_nome(nome)
        if not k:
            return None
        if k in idx:
            return idx[k]
        # tolerância: mesmo primeiro e último nome
        partes = k.split()
        for kk, slug in idx.items():
            pp = kk.split()
            if len(partes) >= 2 and len(pp) >= 2 and partes[0] == pp[0] and partes[-1] == pp[-1]:
                return slug
        nao_resolvidos[nome] += 1
        return None

    return resolve, nao_resolvidos


def main() -> int:
    resolve, nao_resolvidos = monta_resolvedor()
    avisos: list[str] = []

    # ------------------------------------------------------------ matérias
    bruto_m = carrega("navegador-materias.json", {"paginas": {}})
    # listas de projetos por vereador (fichas oficiais) completam o que a listagem geral não mostra
    bruto_p = carrega("navegador-projetos.json", {"listas": {}})
    fontes_html = [h for _, h in sorted(bruto_m["paginas"].items(), key=lambda x: int(x[0]))]
    fontes_html += list(bruto_p.get("listas", {}).values())
    materias = {}
    for html in fontes_html:
        for m in parse_lista_materias(html):
            if m.get("id") in materias:
                continue
            if not m.get("id") or not m.get("tipo"):
                continue
            if (m.get("data_publicacao") or "") < INICIO:
                continue
            autores_txt = separa_autores(m.get("autoria_texto", ""))
            autores = [s for s in (resolve(a) for a in autores_txt) if s]
            grupo, motivo = classificar(m["tipo"], m.get("ementa", ""))
            locais = extrair_locais(m.get("ementa", "")) if grupo in ("bairros", "outros") and m["tipo"].startswith("INDICA") else {"vias": [], "bairros": []}
            materias[m["id"]] = {
                "id": m["id"],
                "tipo": m["tipo"].replace("(URGÊNCIA) ", ""),
                "numero": m["numero"],
                "ano": m["ano"],
                "titulo": m["titulo"],
                "data": m["data_publicacao"][:10],
                "ementa": m.get("ementa", ""),
                "autoria": m.get("autoria_texto", ""),
                "autores": autores,
                "situacao": m.get("situacao", ""),
                "url": m["url"],
                "grupo": grupo,
                "motivo": motivo,
                "assunto": assunto(m.get("ementa", "")) if grupo == "bairros" else None,
                "vias": locais["vias"],
                "bairros": locais["bairros"],
            }

    # unifica grafias do mesmo bairro (ex.: "Caixa D´água", "Caixa da Água" → "Caixa D'Água")
    def chave_bairro(b: str) -> str:
        k = re.sub(r"[^a-z]", "", sem_acento(b).lower())
        return "caixadagua" if k.startswith("caixad") else k
    formas = defaultdict(Counter)
    for m in materias.values():
        for b in m["bairros"]:
            formas[chave_bairro(b)][b] += 1
    canon = {k: ("Caixa D'Água" if k == "caixadagua" else c.most_common(1)[0][0]) for k, c in formas.items()}
    for m in materias.values():
        m["bairros"] = list(dict.fromkeys(canon[chave_bairro(b)] for b in m["bairros"]))

    # lacunas de numeração (matérias que a listagem pública não mostrou)
    numeros = defaultdict(set)
    for m in materias.values():
        numeros[(m["tipo"], m["ano"])].add(m["numero"])
    lacunas = []
    for (tipo, ano), ns in sorted(numeros.items()):
        falt = sorted(set(range(1, max(ns) + 1)) - ns)
        if falt:
            lacunas.append({"tipo": tipo, "ano": ano, "encontradas": len(ns), "maior_numero": max(ns), "faltando": len(falt), "exemplos": falt[:15]})

    # ------------------------------------------------------------ sessões e votos
    bruto_a = carrega("navegador-atas.json", {"lista": {}, "det": {}})
    pres_pdf = carrega("presencas-pdf.json", {})
    sessoes, votacoes = [], []
    for url, html in bruto_a.get("det", {}).items():
        if html.startswith("SEM CONTEUDO"):
            avisos.append(f"Ata sem conteúdo: {url}")
            continue
        ata = parse_ata(html, url)
        if not ata.get("data") or ata["data"][:10] < INICIO:
            continue
        sid = re.search(r"/(\d+)$", ata["url"]).group(1)
        titulo = ata.get("titulo", "")
        tipo_sessao = (re.search(r"Sessão\s+(\w+)", titulo) or [None, "Outra"])[1]
        p = pres_pdf.get(ata["pdf"] or "", {})
        presentes = None
        if p.get("presentes"):
            presentes = sorted({s for s in (resolve(n) for n in p["presentes"]) if s})
            nao = [n for n in p["presentes"] if not resolve(n)]
            if nao:
                avisos.append(f"Ata {sid}: nomes na presença sem correspondência: {nao}")
        sessoes.append({
            "id": sid,
            "data": ata["data"][:10],
            "hora": ata["data"][11:16],
            "titulo": titulo,
            "tipo": tipo_sessao,
            "numero_ata": p.get("numero_ata"),
            "url": ata["url"],
            "pdf": ata["pdf"],
            "presentes": presentes,
            "presenca_trecho": p.get("trecho"),
        })
        for it in ata["itens"]:
            for v in it["votacoes"]:
                if "bruto" in v:
                    continue
                listas = {k: v.get(k, []) for k in v if k not in ("turno", "resultado")}
                nominal = any(listas.values())
                votos = {}
                for rot, nomes in listas.items():
                    for n in nomes:
                        s = resolve(n)
                        if s:
                            votos[s] = rot
                votacoes.append({
                    "sessao": sid,
                    "data": ata["data"][:10],
                    "ata_url": ata["url"],
                    "materia": f'{it.get("tipo", "")} Nº {it.get("numero", "")}/{it.get("ano", "")}'.strip(),
                    "tipo": it.get("tipo"),
                    "numero": it.get("numero"),
                    "ano": it.get("ano"),
                    "autoria": it.get("autoria_texto"),
                    "ementa": limpa(re.sub(r"^.*?\)\s*,?\s*que\s*", "", it["texto"]))[:400],
                    "turno": v["turno"],
                    "resultado": v["resultado"],
                    "nominal": nominal,
                    "votos": votos,
                    "contagem": {k: len(x) for k, x in listas.items()},
                })
    sessoes.sort(key=lambda s: (s["data"], s["hora"]))
    votacoes.sort(key=lambda v: v["data"])

    # liga votação à matéria (quando a matéria está na listagem)
    por_ref = {(m["tipo"], m["numero"], m["ano"]): m["id"] for m in materias.values()}
    for v in votacoes:
        v["materia_id"] = por_ref.get(((v.get("tipo") or "").upper(), v.get("numero"), v.get("ano")))

    # ------------------------------------------------------------ vereadores
    fichas = carrega("navegador-vereadores.json", {})
    vereadores = []
    sess_com_presenca = [s for s in sessoes if s["presentes"] is not None]
    for v in CONF["vereadores"]:
        slug = v["slug"]
        f = fichas.get(slug, {})
        mats = [m for m in materias.values() if slug in m["autores"]]
        grupos = Counter(m["grupo"] for m in mats)
        pres = sum(1 for s in sess_com_presenca if slug in s["presentes"])
        votos_v = [x for x in votacoes if x["nominal"]]
        participou = sum(1 for x in votos_v if x["votos"].get(slug) not in (None, "ausentes"))
        ausente_vot = sum(1 for x in votos_v if x["votos"].get(slug) == "ausentes")
        vereadores.append({
            "slug": slug,
            "nome": v["nome"],
            "partido": f.get("partido"),
            "foto": f.get("foto"),
            "url_ficha": f.get("url"),
            "contatos": f.get("contatos", []),
            "cargos": f.get("cargos", []),
            "materias_total": len(mats),
            "materias_por_grupo": {g: grupos.get(g, 0) for g in GRUPOS},
            "presenca": {
                "presente": pres,
                "sessoes_com_lista": len(sess_com_presenca),
                "sessoes_sem_lista": len(sessoes) - len(sess_com_presenca),
            },
            "votos_nominais": {"registrados": participou, "ausente_na_votacao": ausente_vot, "votacoes_nominais": len(votos_v),
                               "primeira_nominal": min((x["data"] for x in votos_v), default=None)},
        })

    periodo_fim = max([m["data"] for m in materias.values()] + [s["data"] for s in sessoes] or [INICIO])
    radar = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "periodo": {"inicio": INICIO, "fim": periodo_fim, "legislatura": CONF["legislatura"]},
        "grupos": GRUPOS,
        "regras": REGRAS_TEXTO,
        "vereadores": vereadores,
        "materias": sorted(materias.values(), key=lambda m: (m["data"], m["id"]), reverse=True),
        "sessoes": sessoes,
        "votacoes": votacoes,
        "lacunas": lacunas,
        "fontes": {
            "portal": "https://www.guaramirim.sc.leg.br",
            "materias": "https://www.guaramirim.sc.leg.br/tramitacoes",
            "atas": "https://www.guaramirim.sc.leg.br/atas/plenaria",
            "vereadores": "https://www.guaramirim.sc.leg.br/camara/membros/exercicio/0",
            "dados_abertos": "https://www.guaramirim.sc.leg.br/dadosabertos",
            "transparencia": "https://camaraguaramirim.atende.net/transparencia/",
        },
    }
    relatorio = {
        "gerado_em": radar["gerado_em"],
        "materias": len(materias),
        "materias_por_tipo": Counter(m["tipo"] for m in materias.values()),
        "materias_por_grupo": Counter(m["grupo"] for m in materias.values()),
        "sessoes": len(sessoes),
        "sessoes_com_presenca": len(sess_com_presenca),
        "votacoes": len(votacoes),
        "votacoes_nominais": sum(1 for v in votacoes if v["nominal"]),
        "nomes_nao_resolvidos": dict(nao_resolvidos.most_common()),
        "lacunas": lacunas,
        "avisos": avisos,
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "radar.json").write_text(json.dumps(radar, ensure_ascii=False, separators=(",", ":")))
    (RAIZ / "dados" / "relatorio-coleta.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, default=list))
    print(json.dumps({k: v for k, v in relatorio.items() if k not in ("lacunas", "avisos")}, ensure_ascii=False, indent=1, default=list))
    print("avisos:", len(avisos), "| lacunas:", len(lacunas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
