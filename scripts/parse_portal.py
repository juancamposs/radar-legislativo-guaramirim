"""Interpretação do HTML público do portal da Câmara Municipal de Guaramirim (Softcam).

Fonte: https://www.guaramirim.sc.leg.br  (listagem de matérias e atas plenárias)
Só lê o que a Câmara publica. Não infere nada que não esteja escrito.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from bs4 import BeautifulSoup

BASE = "https://www.guaramirim.sc.leg.br"

RE_TITULO = re.compile(r"^(?P<tipo>.+?)\s+N\.?\s*º\s*(?P<num>\d+)\s*/\s*(?P<ano>\d{4})", re.I)


def limpa(txt: str | None) -> str:
    return re.sub(r"\s+", " ", (txt or "")).strip()


def sem_acento(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")


def chave_nome(nome: str) -> str:
    return re.sub(r"[^a-z ]", "", sem_acento(nome).lower()).strip()


def data_br(txt: str) -> str | None:
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})(?:\s+(\d{2}):(\d{2}))?", txt or "")
    if not m:
        return None
    d, mo, a, h, mi = m.groups()
    return f"{a}-{mo}-{d}" + (f"T{h}:{mi}" if h else "")


def url_canonica(href: str) -> str:
    href = (href or "").split("?")[0]
    if href.startswith("/"):
        href = BASE + href
    return href


def parse_lista_materias(html: str) -> list[dict]:
    """Listagem /tramitacoes: pares (linhatitulo-3, materia_conteudo)."""
    s = BeautifulSoup(html, "html.parser")
    out, atual = [], None
    for div in s.find_all("div", recursive=False):
        cls = " ".join(div.get("class") or [])
        if "pbw_linhatitulo-3" in cls:
            a = div.find("a")
            partes = [limpa(x.get_text()) for x in div.find_all("div", recursive=False)]
            titulo = limpa(a.get_text()) if a else ""
            atual = {
                "titulo": titulo,
                "data_publicacao": data_br(partes[0] if partes else ""),
                "url": url_canonica(a.get("href")) if a else None,
            }
            m = RE_TITULO.match(titulo)
            if m:
                atual.update(tipo=limpa(m["tipo"]).upper(), numero=int(m["num"]), ano=int(m["ano"]))
            out.append(atual)
        elif "pbw_materia_conteudo" in cls and atual is not None:
            em = div.find("em")
            atual["ementa"] = limpa(em.get_text()) if em else ""
            for sp in div.find_all("span"):
                rot = limpa(sp.find("strong").get_text()) if sp.find("strong") else ""
                val = limpa(sp.get_text().replace(rot, "", 1))
                if rot.startswith("Autoria"):
                    atual["autoria_texto"] = val
                elif rot.startswith("Situação"):
                    atual["situacao"] = val
            atual = None
    for m in out:
        mid = re.search(r"/tramitacoes/\d+/(\d+)", m.get("url") or "") or re.search(r"/proposicoes/.+/(\d+)$", m.get("url") or "")
        m["id"] = int(mid.group(1)) if mid else None
    return out


def separa_autores(txt: str) -> list[str]:
    """'A; B' ou 'A e B' → ['A','B'] (só separa por ';' e ' e ' entre nomes)."""
    if not txt:
        return []
    partes = re.split(r"\s*;\s*|\s*,\s*(?=[A-ZÁÉÍÓÚ])|\s+e\s+(?=[A-ZÁÉÍÓÚ])", txt)
    return [limpa(p) for p in partes if limpa(p)]


# ---------------------------------------------------------------- atas
RE_VOT = re.compile(
    r"Votação\s*-\s*(?P<turno>[^:]+?):\s*(?P<resultado>[^-]+?)\s*-\s*(?P<resto>.+)$", re.I
)


def parse_votos_resto(resto: str) -> dict:
    """'Favoráveis: A, B; Contrários: C;' → {'favoraveis':[...], ...}"""
    out: dict[str, list[str]] = {}
    for rot, nomes in re.findall(r"([A-Za-zÀ-ú ]+?):\s*([^;]*);?", resto):
        k = chave_nome(rot).replace(" ", "_")
        lista = [limpa(n) for n in nomes.split(",") if limpa(n)]
        if k:
            out[k] = lista
    return out


def parse_ata(html: str, url: str) -> dict:
    s = BeautifulSoup(html, "html.parser")
    txt = s.get_text("\n")
    linhas = [limpa(x) for x in txt.split("\n") if limpa(x)]
    ata: dict = {"url": url_canonica(url)}
    # cabeçalho: data/hora e título
    for i, ln in enumerate(linhas):
        if re.fullmatch(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", ln) and i + 1 < len(linhas) and linhas[i + 1].startswith("Ata"):
            ata["data"] = data_br(ln)
            ata["titulo"] = linhas[i + 1]
            break
    # pdf anexo
    pdfs = [a.get("href") for a in s.find_all("a") if (a.get("href") or "").lower().endswith(".pdf")]
    ata["pdf"] = pdfs[0] if pdfs else None
    ata["pdfs"] = pdfs
    # itens da ordem do dia com votação
    itens, atual = [], None
    for ln in linhas:
        m_item = re.match(r"^(\d{2})\)\s*(.+)$", ln)
        if m_item:
            atual = {"ordem": int(m_item.group(1)), "texto": m_item.group(2), "votacoes": []}
            mt = re.match(r"(?P<tipo>[A-ZÇÃÕÉÍÓÚÂÊÔ ]+?)\s+N\.?\s*º\s*(?P<num>\d+)/(?P<ano>\d{4})\s*\((?P<aut>[^)]*)\)", m_item.group(2))
            if mt:
                atual.update(tipo=limpa(mt["tipo"]), numero=int(mt["num"]), ano=int(mt["ano"]), autoria_texto=limpa(mt["aut"]))
            itens.append(atual)
            continue
        mv = RE_VOT.match(ln)
        if mv and atual is not None:
            atual["votacoes"].append(
                {"turno": limpa(mv["turno"]), "resultado": limpa(mv["resultado"]).lower(), **parse_votos_resto(mv["resto"])}
            )
        elif ln.startswith("Votação") and atual is not None:
            atual["votacoes"].append({"bruto": ln})
    ata["itens"] = itens
    return ata


RE_PRESENCA = re.compile(
    r"(?:com\s+a\s+presen[çc]a\s+d[oa]s?\s+(?:seguintes\s+)?vereador(?:es|as)?(?:\s+e\s+vereadoras?)?"
    r"|estiveram\s+presentes\s+(?:os|as)\s+(?:senhores\s+)?vereador(?:es|as)?"
    r"|reuniram-se\s+em\s+sess[ãa]o\s+\w+\s+os\s+vereadores\s+eleitos"
    r"|presentes\s+(?:os|as)\s+(?:seguintes\s+)?vereador(?:es|as)?)"
    r"\s*[:,]?\s*(?P<nomes>.+?)\.\s+(?=[A-ZÁ])",
    re.I | re.S,
)


def _normaliza_abrev(t: str) -> str:
    """Tira os pontos de abreviações que cortariam a frase ('Prof.', 'Z.', 'Sr.')."""
    t = re.sub(r"\bProf(?:a|ª)?\.\s*", "Professora ", t)
    t = re.sub(r"\b(Sr|Sra|Srª|Dr|Dra|Vdr|Ver)\.\s*", r"\1 ", t)
    t = re.sub(r"\b([A-Z])\.\s+(?=[A-Z])", r"\1 ", t)  # iniciais do meio: 'Maria Rosana Z. Franz'
    return t
RE_AUSENCIA = re.compile(
    r"(?:ausente|aus[eê]ncia|n[ãa]o\s+compareceu|justificou\s+(?:a\s+)?aus[eê]ncia)", re.I
)


def parse_presenca_pdf(texto: str) -> dict:
    """Extrai a lista de presentes do texto da ata em PDF.

    Retorna {'presentes': [...], 'trecho': '...'} ou {} se o padrão não for encontrado.
    """
    t = re.sub(r"-\s*\n\s*", "", texto)  # junta palavras hifenizadas na quebra
    t = re.sub(r"\s+", " ", t)
    t = _normaliza_abrev(t)
    m = RE_PRESENCA.search(t)
    if not m:
        return {}
    nomes_txt = re.sub(r"\([^)]*\)", "", m.group("nomes"))  # tira '(Presidente)'
    nomes = [limpa(n) for n in re.split(r",\s*|\s+e\s+(?=[A-ZÁÉÍÓÚ])", nomes_txt) if limpa(n)]
    ini = max(0, m.start() - 40)
    trecho = t[ini : m.end() + 5]
    frases_aus = [limpa(f) for f in re.findall(r"[^.]*?(?:ausente|aus[eê]ncia|n[ãa]o compareceu)[^.]*\.", t, re.I)]
    return {"presentes": nomes, "trecho": trecho, "frases_ausencia": frases_aus[:5]}


def ano_de(iso: str | None) -> int | None:
    try:
        return datetime.fromisoformat(iso[:10]).year if iso else None
    except ValueError:
        return None
