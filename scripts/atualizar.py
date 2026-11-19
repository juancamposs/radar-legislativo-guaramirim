"""Atualização diária: coleta → processa → valida → publica (ou mantém a última versão boa).

Uso: python scripts/atualizar.py
Código de saída 0 = publicado ou nada novo; 1 = coleta reprovada (site mantido, erro registrado).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PY = sys.executable
PUBLICADO = RAIZ / "site" / "dados" / "radar.json"
BACKUP = RAIZ / "dados" / "radar-ultima-validada.json"
LOG = RAIZ / "dados" / "historico-coleta.jsonl"


def roda(script: str) -> tuple[int, str]:
    p = subprocess.run([PY, str(RAIZ / "scripts" / script)], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)[-4000:]


def registra(status: str, detalhes: dict) -> None:
    with LOG.open("a") as f:
        f.write(json.dumps({"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "status": status, **detalhes}, ensure_ascii=False) + "\n")


def main() -> int:
    etapas = {}
    if PUBLICADO.exists():
        shutil.copy(PUBLICADO, BACKUP)

    cod, out = roda("coletar_api.py")
    etapas["api"] = {"codigo": cod, "saida": out[-800:]}  # 3 = sem token (não é erro)
    if cod not in (0, 3):
        registra("erro_coleta", etapas)
        print(out)
        return 1

    cod, out = roda("pdf_atas.py")
    etapas["pdf_atas"] = {"codigo": cod, "saida": out[-800:]}
    if cod != 0:
        registra("erro_pdf", etapas)
        print(out)
        return 1

    cod, out = roda("processar.py")
    etapas["processar"] = {"codigo": cod, "saida": out[-800:]}
    if cod != 0:
        if BACKUP.exists():
            shutil.copy(BACKUP, PUBLICADO)
        registra("erro_processamento", etapas)
        print(out)
        return 1

    p = subprocess.run([PY, str(RAIZ / "scripts" / "validar.py"), str(PUBLICADO), str(BACKUP)], capture_output=True, text=True)
    etapas["validar"] = {"codigo": p.returncode, "saida": p.stdout[-1500:]}
    print(p.stdout)
    if p.returncode != 0:
        if BACKUP.exists():
            shutil.copy(BACKUP, PUBLICADO)  # mantém a última versão validada
        registra("reprovado", etapas)
        return 1
    registra("aprovado", etapas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
