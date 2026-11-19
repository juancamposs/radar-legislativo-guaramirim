"""Regras de classificação das proposições — a MESMA regra para todos os vereadores.

A regra é aplicada em ordem; a primeira que casar define o grupo. O texto desta
regra também aparece no site (seção "Como classificamos").
"""
from __future__ import annotations

import re

from parse_portal import limpa, sem_acento

GRUPOS = {
    "bairros": "Melhorias nos bairros",
    "informacao": "Pedidos de informação e cobranças",
    "homenagens": "Homenagens e datas",
    "leis": "Projetos de lei e normas",
    "outros": "Outros pedidos e propostas",
}

REGRAS_TEXTO = [
    ("homenagens", "Moções de aplauso, pesar, congratulação ou apoio; títulos de cidadão, comendas, nomes de rua/prédio público e datas comemorativas (inclusive quando vêm como projeto de lei)."),
    ("informacao", "Pedidos de informação e requerimentos que pedem dados, explicações ou providências a algum órgão."),
    ("leis", "Projetos de lei ordinária ou complementar, emendas à Lei Orgânica, projetos de resolução e de decreto legislativo, emendas, substitutivos e vetos."),
    ("bairros", "Indicações que pedem obra ou serviço em um lugar: pavimentação, drenagem e tubulação, iluminação, sinalização, limpeza e roçada, água e esgoto, pontes, calçadas, lombadas, abrigos de ônibus, estradas e outros serviços urbanos."),
    ("outros", "Indicações de programas, estudos e políticas sem obra em local específico, e qualquer outra matéria que não se encaixe acima."),
]

TERMOS_HOMENAGEM = r"(aplauso|pesar|congratula|louvor|homenage|cidad[aã]o honor|t[ií]tulo de cidad|comenda|denomina|d[aá] (o )?nome|calend[aá]rio oficial|institui o dia|institui a semana|dia municipal|semana municipal|m[eê]s municipal|reconhecimento|apoio)"
TERMOS_OBRA = r"(paviment|asfalt|recape|tapa.?buraco|lajot|paralelep|cascalh|macadam|patrol|ensaibr|drenag|tubula|bueiro|boca.?de.?lobo|bocas de lobo|galeria|pluvia|fluvia|ilumina|l[aâ]mpada|poste|lumin[aá]ria|sinaliza|faixa de pedestre|placa|lombada|redutor|quebra.?mola|ro[çc]ada|ro[çc]agem|capina|limpeza|desassorea|draga|ponte|pontilh|passarela|cal[çc]ada|passeio|meio.?fio|ciclovia|abrigo de [oô]nibus|ponto de [oô]nibus|rede de [aá]gua|[aá]gua tratada|esgoto|hidrante|muro de conten|guarda.?corpo|alargamento|duplica|rotat[oó]ria|estacionamento|academia ao ar livre|playground|parquinho|pra[çc]a|quadra|canaliza|vala|constru|reforma|revitaliza|manuten|conserto|concerto|amplia|recupera|melhoria|cobertura|abrigo)"
RE_LOCAL = r"\b(rua|estrada|avenida|av\.|servid[aã]o|sd\s*-?\s*n|travessa|rodovia|bairro|localidade|loteamento|vila)\b"


def norm(txt: str) -> str:
    return sem_acento(limpa(txt)).lower()


def classificar(tipo: str, ementa: str) -> tuple[str, str]:
    """Retorna (grupo, motivo curto)."""
    t = norm(tipo or "")
    e = norm(ementa or "")
    if "mocao" in t:
        return "homenagens", "Moção"
    if re.search(sem_acento(TERMOS_HOMENAGEM), e) and any(k in t for k in ("projeto", "decreto", "resolucao")):
        return "homenagens", "Projeto que concede homenagem, nome ou data"
    if "pedido de informa" in t or "requerimento" in t:
        return "informacao", "Pedido de informação / requerimento"
    if any(k in t for k in ("projeto", "emenda", "veto", "substitutivo")):
        return "leis", "Projeto de lei ou norma"
    if "indicacao" in t:
        if re.search(sem_acento(TERMOS_OBRA), e) and re.search(sem_acento(RE_LOCAL), e):
            return "bairros", "Indicação de obra/serviço em local"
        return "outros", "Indicação sem obra em local específico"
    return "outros", "Outro tipo de matéria"


# ------------------------------------------------------------- locais
RE_VIA = re.compile(
    r"\b(?P<tipo>rua|estrada|avenida|av\.|servid[aã]o|sd|travessa|rodovia)\s*(?:geral\s+)?"
    r"(?P<nome>(?:n[º°o]?\.?\s*\d+\s*[-–]?\s*)?[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç0-9'\.]+(?:\s+(?:d[aeo]s?|de|e|[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'\.-]*)){0,6})",
    re.I,
)
RE_BAIRRO = re.compile(
    r"\b(?i:bairro|localidade|loteamento|vila)\s+(?P<nome>[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'’´-]*(?:\s+(?:d[aeo]s?|de|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'’´-]*)){0,4})"
)
CORTA_FIM = re.compile(r"\s+(?:d[aeo]s?|de|e|no|na|em)$", re.I)

ASSUNTOS = [
    ("Pavimentação e asfalto", r"paviment|asfalt|recape|tapa.?buraco|lajot|paralelep|cascalh|macadam|patrol|ensaibr|concreto usinado"),
    ("Drenagem e tubulação", r"drenag|tubula|bueiro|boca.?de.?lobo|bocas de lobo|galeria|pluvia|fluvia|canaliza|vala"),
    ("Iluminação pública", r"ilumina|lampada|poste|luminaria"),
    ("Sinalização e trânsito", r"sinaliza|faixa de pedestre|placa|lombada|redutor|quebra.?mola|rotatoria|transito|demutran"),
    ("Limpeza e roçada", r"rocada|rocagem|capina|limpeza|desassorea|draga|entulho"),
    ("Água e esgoto", r"rede de agua|agua tratada|esgoto|hidrante|aguas de guaramirim"),
    ("Pontes, calçadas e passeios", r"ponte|pontilh|passarela|calcada|passeio|meio.?fio|ciclovia|guarda.?corpo"),
    ("Transporte coletivo", r"abrigo de onibus|ponto de onibus|transporte coletivo|linha de onibus"),
    ("Praças, quadras e lazer", r"praca|quadra|academia ao ar livre|playground|parquinho"),
]


def assunto(ementa: str) -> str:
    e = norm(ementa)
    for nome, rx in ASSUNTOS:
        if re.search(rx, e):
            return nome
    return "Outros serviços"


def _arruma(nome: str) -> str:
    nome = limpa(nome).strip(" ,.;:–-")
    while True:
        novo = CORTA_FIM.sub("", nome)
        if novo == nome:
            break
        nome = novo
    return nome


RE_RUA_NUM = re.compile(
    r"\b(?P<tipo>rua|servid[aã]o|sd|estrada|travessa)\s*(?:-\s*)?n[º°o]?\.?\s*(?P<num>\d+)\s*(?:[-–]\s*(?P<nome>[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'\.]*(?:\s+(?:d[aeo]s?|de|e|[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç'\.]*)){0,5}))?",
    re.I,
)


def extrair_locais(ementa: str) -> dict:
    vias, bairros = [], []
    ocupado = []
    for m in RE_RUA_NUM.finditer(ementa or ""):
        tipo = norm(m["tipo"])
        tipo = {"sd": "servidão", "servidao": "servidão"}.get(tipo, tipo)
        nome = _arruma(m["nome"] or "")
        nome = re.split(r",|\s+numa\s|\s+na extens|\s+localizad|\s+bairro\s|\s+no bairro|\s+lateral", nome, flags=re.I)[0]
        nome = _arruma(nome)
        vias.append(f"{tipo.capitalize()} Nº {m['num']}" + (f" – {nome}" if nome else ""))
        ocupado.append((m.start(), m.end()))
    for m in RE_VIA.finditer(ementa or ""):
        if any(a <= m.start() < b for a, b in ocupado):
            continue
        tipo = norm(m["tipo"]).rstrip(".")
        tipo = {"av": "avenida", "sd": "servidão", "servidao": "servidão"}.get(tipo, tipo)
        nome = _arruma(m["nome"])
        nome = re.split(r",|\s+[-–]\s+(?=[a-z])|\s+numa\s|\s+na extens|\s+localizad|\s+bairro\s|\s+no bairro|\s+lateral", nome, flags=re.I)[0]
        nome = _arruma(nome)
        if len(nome) < 2 or norm(nome) in {"municipal", "municipio", "competente"}:
            continue
        vias.append(f"{tipo.capitalize()} {nome}")
    for m in RE_BAIRRO.finditer(ementa or ""):
        nome = _arruma(m["nome"])
        if len(nome) >= 3:
            bairros.append(nome)
    # sem duplicatas mantendo ordem
    return {"vias": list(dict.fromkeys(vias)), "bairros": list(dict.fromkeys(bairros))}


def chave_local(txt: str) -> str:
    """Normaliza nome de via/bairro para agrupar (sem acento, minúsculas).
    Ruas numeradas agrupam pelo número oficial ('rua 385'), com ou sem o nome."""
    t = norm(txt)
    m = re.match(r"(rua|servidao|estrada|travessa) n[ºo°]?\.?\s*(\d+)", t)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    t = re.sub(r"\bn[ºo°]?\.?\s*", "", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()
