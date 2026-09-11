"""Gera o kit físico das estações Trilhas Poéticas a partir de CSV local.

CSV mínimo: code,name
Colunas opcionais: station_type,physical_code,points,location_hint

O physical_code fica apenas no material local de impressão; o banco armazena seu hash.
"""
from __future__ import annotations

import argparse
import csv
import html
import logging
import re
from pathlib import Path
from urllib.parse import quote

import qrcode


def safe_filename(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return clean or "qr"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera QR Codes físicos do Trilhas Poéticas")
    parser.add_argument("--input", type=Path, default=Path("qrs.csv"), help="CSV das estações")
    parser.add_argument("--base-url", required=True, help="URL pública da aplicação")
    parser.add_argument("--output", type=Path, default=Path("qr_output"), help="Diretório de saída")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not args.input.exists():
        raise SystemExit(f"Arquivo não encontrado: {args.input}")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    with args.input.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or not {"code", "name"}.issubset(set(reader.fieldnames)):
            raise SystemExit("O CSV precisa conter as colunas code e name.")
        for line, row in enumerate(reader, start=2):
            code = (row.get("code") or "").strip().upper()
            name = (row.get("name") or "").strip()
            if not code or not name:
                raise SystemExit(f"Linha {line}: code/name obrigatório")
            url = f"{args.base_url.rstrip('/')}/q/{quote(code, safe='')}"
            filename = f"{safe_filename(code)}.png"
            image = qrcode.make(url)
            image.save(args.output / filename)
            manifest.append({
                "code": code,
                "name": name,
                "station_type": (row.get("station_type") or "permanent").strip(),
                "physical_code": (row.get("physical_code") or "").strip().upper(),
                "points": (row.get("points") or "").strip(),
                "location_hint": (row.get("location_hint") or "").strip(),
                "url": url,
                "file": filename,
            })

    fields = ["code", "name", "station_type", "physical_code", "points", "location_hint", "url", "file"]
    with (args.output / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(manifest)

    cards = []
    for item in manifest:
        physical = html.escape(item["physical_code"] or "—")
        points = html.escape(item["points"] or "—")
        location = html.escape(item["location_hint"] or "A definir pela equipe de espaços")
        cards.append(f"""
<article class="card">
  <h2>{html.escape(item['name'])}</h2>
  <img src="{html.escape(item['file'])}" alt="QR Code da estação {html.escape(item['name'])}">
  <p><strong>Código:</strong> {html.escape(item['code'])}</p>
  <p><strong>Tipo:</strong> {html.escape(item['station_type'])} • <strong>Pontos:</strong> {points}</p>
  <p><strong>Código físico:</strong> <span class="physical">{physical}</span></p>
  <p><strong>Referência:</strong> {location}</p>
</article>""")
    page = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Trilhas Poéticas — QRs</title><style>
@page{{size:A4;margin:10mm}}body{{font-family:Arial,sans-serif;color:#111;margin:0}}main{{display:grid;grid-template-columns:1fr 1fr;gap:8mm}}.card{{border:2px solid #222;border-radius:10px;padding:6mm;break-inside:avoid;text-align:center}}img{{width:55mm;height:55mm;image-rendering:pixelated}}h2{{font-size:17px;margin:0 0 4mm}}p{{font-size:12px;margin:2mm 0}}.physical{{font-size:22px;font-weight:700;letter-spacing:2px}}@media print{{.card{{page-break-inside:avoid}}}}
</style></head><body><main>{''.join(cards)}</main></body></html>"""
    (args.output / "folha_impressao.html").write_text(page, encoding="utf-8")
    logging.info("Concluído: %s estações em %s", len(manifest), args.output.resolve())
    print("Arquivos gerados: PNGs, manifest.csv e folha_impressao.html")


if __name__ == "__main__":
    main()
