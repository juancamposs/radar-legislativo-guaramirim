"""Confere as contagens do Radar com as contagens oficiais da ficha de cada vereador.

Fonte oficial: bloco 'Atividades Legislativas' de guaramirim.sc.leg.br/camara/membros/show/<id>/0/<ano>
Saída: docs/conferencia-fichas.json e resumo no terminal.
"""
import collections
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
R = json.loads((RAIZ / "site/dados/radar.json").read_text())
O = json.loads((RAIZ / "dados/brutos/fichas-contagens-oficiais.json").read_text())
MAPA = {"Indi": "Indicações", "Moçõ": "Moções", "Pedi": "Pedidos de informação", "Requ": "Requerimentos", "Proj": "Projetos"}


def tipo(t):
    if t.startswith("MOÇÃO"):
        return "Moções"
    if t.startswith("PROJETO"):
        return "Projetos"
    return {"INDICAÇÃO": "Indicações", "PEDIDO DE INFORMAÇÃO": "Pedidos de informação", "REQUERIMENTO": "Requerimentos"}.get(t, t)


meu = collections.Counter()
for m in R["materias"]:
    for a in m["autores"]:
        meu[(a, m["ano"], tipo(m["tipo"]))] += 1
linhas = []
for k, s in O["contagens"].items():
    vid, ano = k.split("_")
    slug, ano = O["ids"][vid], int(ano)
    of = collections.Counter()
    for x in s.split(","):
        of[MAPA[x[3:]]] += int(x[:3])
    for t in MAPA.values():
        linhas.append({"vereador": slug, "ano": ano, "tipo": t, "ficha_oficial": of[t], "radar": meu[(slug, ano, t)],
                       "url": f"https://www.guaramirim.sc.leg.br/camara/membros/show/{vid}/0/{ano}"})
dif = [l for l in linhas if l["ficha_oficial"] != l["radar"]]
(RAIZ / "docs").mkdir(exist_ok=True)
(RAIZ / "docs/conferencia-fichas.json").write_text(json.dumps({"comparacoes": len(linhas), "iguais": len(linhas) - len(dif), "divergencias": dif, "todas": linhas}, ensure_ascii=False, indent=1))
print(f"{len(linhas) - len(dif)} de {len(linhas)} contagens iguais à ficha oficial")
for l in dif:
    print("  DIVERGE", l["vereador"], l["ano"], l["tipo"], "ficha", l["ficha_oficial"], "radar", l["radar"])
