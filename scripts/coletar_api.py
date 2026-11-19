"""Coleta pela API oficial de dados abertos da Câmara de Guaramirim.

Documentação: https://www.guaramirim.sc.leg.br/dadosabertos
URL: /jsonweb/web-aplicativo.php?keysoft=<TOKEN>&call=<serviço>
O token é pessoal (cadastro no portal) e fica no segredo CAMARA_TOKEN do GitHub — nunca no código.

Salva as respostas brutas em dados/brutos/api/ para o processar.py usar.
Sem token: avisa e sai com código 3 (o orquestrador mantém os dados atuais).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
DEST = RAIZ / "dados" / "brutos" / "api"
URL = "https://www.guaramirim.sc.leg.br/jsonweb/web-aplicativo.php"
UA = "RadarLegislativoGuaramirim/1.0 (projeto civico; Adriano Machado Advocacia; 1 req/s)"
# tipos de proposição que interessam ao Radar (o 'contract' real vem de proposicoes_tipos)
MAX_PAGINAS = 80


def chama(token: str, call: str, **params) -> object:
    r = requests.get(URL, params={"keysoft": token, "call": call, **params}, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    time.sleep(1)
    txt = r.text.strip()
    if not txt:
        raise RuntimeError(f"resposta vazia em {call} (token inválido?)")
    return r.json()


def main() -> int:
    token = os.environ.get("CAMARA_TOKEN", "").strip()
    if not token:
        print("CAMARA_TOKEN não configurado: coleta pela API pulada (dados atuais mantidos).")
        return 3
    DEST.mkdir(parents=True, exist_ok=True)
    salvos = {}
    for call in ("vereadores", "proposicoes_tipos", "bairros"):
        salvos[call] = chama(token, call)
        (DEST / f"{call}.json").write_text(json.dumps(salvos[call], ensure_ascii=False, indent=1))
    tipos = salvos["proposicoes_tipos"]
    lista_tipos = tipos if isinstance(tipos, list) else tipos.get("dados", tipos.get("data", []))
    for t in lista_tipos:
        contract = t.get("contract") if isinstance(t, dict) else None
        if not contract:
            continue
        paginas = []
        for p in range(1, MAX_PAGINAS + 1):
            resp = chama(token, "proposicoes", tipo=contract, pagina=p)
            itens = resp if isinstance(resp, list) else resp.get("dados", resp.get("data", []))
            if not itens:
                break
            paginas.append(resp)
        (DEST / f"proposicoes-{contract}.json").write_text(json.dumps(paginas, ensure_ascii=False, indent=1))
    pautas = []
    for p in range(1, 30):
        resp = chama(token, "pautas", pagina=p)
        itens = resp if isinstance(resp, list) else resp.get("dados", resp.get("data", []))
        if not itens:
            break
        pautas.append(resp)
    (DEST / "pautas.json").write_text(json.dumps(pautas, ensure_ascii=False, indent=1))
    print(f"API: {len(lista_tipos)} tipos de proposição, {len(pautas)} páginas de pautas salvas em {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
