"""Confere se um radar.json novo é seguro para publicar.

Regras (se qualquer uma falhar, NÃO publica e mantém a última versão validada):
  1. Estrutura: campos obrigatórios presentes; 9 vereadores; período coerente.
  2. Não encolher: matérias, sessões e votações não podem cair mais de 2% em relação à versão publicada
     (registros oficiais não somem; queda indica coleta incompleta).
  3. Sanidade: toda matéria tem URL oficial, data e grupo; toda sessão tem URL; votos só com nomes conhecidos.
  4. Presença: pelo menos 80% das sessões com lista de presença lida.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validar(novo: dict, anterior: dict | None) -> list[str]:
    erros = []
    for campo in ("gerado_em", "periodo", "vereadores", "materias", "sessoes", "votacoes", "grupos", "regras", "fontes"):
        if campo not in novo:
            erros.append(f"campo ausente: {campo}")
    if erros:
        return erros
    slugs = {v["slug"] for v in novo["vereadores"]}
    if len(slugs) < 9:
        erros.append(f"esperados 9 vereadores, vieram {len(slugs)}")
    if novo["periodo"]["fim"] < novo["periodo"]["inicio"]:
        erros.append("período incoerente")
    if len(novo["materias"]) < 100:
        erros.append(f"poucas matérias ({len(novo['materias'])})")
    if len(novo["sessoes"]) < 20:
        erros.append(f"poucas sessões ({len(novo['sessoes'])})")
    for m in novo["materias"]:
        if not (m.get("url", "").startswith("https://www.guaramirim.sc.leg.br/") and m.get("data") and m.get("grupo")):
            erros.append(f"matéria incompleta: {m.get('titulo')}")
            break
    for s in novo["sessoes"]:
        if not s.get("url", "").startswith("https://www.guaramirim.sc.leg.br/"):
            erros.append(f"sessão sem URL oficial: {s.get('id')}")
            break
    for v in novo["votacoes"]:
        if set(v["votos"]) - slugs:
            erros.append(f"voto com nome desconhecido em {v['materia']}")
            break
    com_lista = sum(1 for s in novo["sessoes"] if s.get("presentes"))
    if novo["sessoes"] and com_lista / len(novo["sessoes"]) < 0.8:
        erros.append(f"só {com_lista}/{len(novo['sessoes'])} sessões com presença lida")
    if anterior:
        for chave in ("materias", "sessoes", "votacoes"):
            a, b = len(anterior.get(chave, [])), len(novo[chave])
            if a and b < a * 0.98:
                erros.append(f"{chave} caiu de {a} para {b}")
    return erros


def main() -> int:
    novo = json.loads(Path(sys.argv[1]).read_text())
    ant_p = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    anterior = json.loads(ant_p.read_text()) if ant_p and ant_p.exists() else None
    erros = validar(novo, anterior)
    if erros:
        print("REPROVADO:\n- " + "\n- ".join(erros))
        return 1
    print(f"APROVADO: {len(novo['materias'])} matérias, {len(novo['sessoes'])} sessões, {len(novo['votacoes'])} votações")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
