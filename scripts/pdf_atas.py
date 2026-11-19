"""Baixa (com cache) os PDFs oficiais das atas e extrai a lista de presença.

Os PDFs ficam em cloudsoftcam.com.br (armazenamento oficial do portal da Câmara).
Coleta educada: identifica o robô, 1 requisição por segundo, nunca baixa o mesmo PDF duas vezes.
Saída: dados/brutos/presencas-pdf.json  {url_pdf: {presentes, trecho, numero_ata, ...}}
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path

import requests
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent))
from parse_portal import parse_ata, parse_presenca_pdf  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "dados" / "pdf-atas"
SAIDA = RAIZ / "dados" / "brutos" / "presencas-pdf.json"
UA = "RadarLegislativoGuaramirim/1.0 (projeto civico; Adriano Machado Advocacia; coleta 1 req/s)"


def texto_pdf(url: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    arq = CACHE / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt")
    if arq.exists():
        return arq.read_text()
    r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError("resposta não é PDF")
    txt = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(r.content)).pages)
    arq.write_text(txt)
    time.sleep(1)
    return txt


def main() -> int:
    atas = json.loads((RAIZ / "dados" / "brutos" / "navegador-atas.json").read_text())
    saida = json.loads(SAIDA.read_text()) if SAIDA.exists() else {}
    erros = 0
    for url, html in atas.get("det", {}).items():
        if html.startswith("SEM CONTEUDO"):
            continue
        ata = parse_ata(html, url)
        pdf = ata.get("pdf")
        if not pdf or (pdf in saida and saida[pdf].get("presentes")):
            continue
        try:
            txt = texto_pdf(pdf)
        except Exception as e:  # noqa: BLE001
            saida[pdf] = {"erro": str(e)}
            erros += 1
            continue
        info = parse_presenca_pdf(txt)
        num = re.search(r"ATA\s*N[º°o]?\s*(\d+\s*/\s*\d{4})", txt, re.I)
        info["numero_ata"] = num.group(1).replace(" ", "") if num else None
        info["ata_url"] = url
        info["chars"] = len(txt)
        saida[pdf] = info
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=1))
    ok = sum(1 for v in saida.values() if v.get("presentes"))
    print(f"PDFs: {len(saida)} | com presença extraída: {ok} | erros: {erros}")
    for k, v in saida.items():
        if not v.get("presentes"):
            print("  sem presença:", v.get("ata_url"), v.get("erro", ""), v.get("chars"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
