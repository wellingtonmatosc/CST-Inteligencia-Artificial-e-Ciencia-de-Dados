"""Gera PNGs de QR Code a partir de um CSV, sem depender do banco."""
from __future__ import annotations

import argparse
import csv
import logging
import re
from pathlib import Path
from urllib.parse import quote

import qrcode


def safe_filename(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return clean or "qr"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera QR Codes físicos do evento.")
    parser.add_argument("--input", required=True, type=Path, help="CSV com colunas code,name")
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
        for row in reader:
            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()
            if not code or not name:
                logging.warning("Linha ignorada por code/name vazio: %s", row)
                continue
            url = f"{args.base_url.rstrip('/')}/q/{quote(code, safe='')}"
            filename = f"{safe_filename(code)}.png"
            image = qrcode.make(url)
            image.save(args.output / filename)
            manifest.append({"code": code, "name": name, "url": url, "file": filename})
    with (args.output / "manifest.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["code", "name", "url", "file"])
        writer.writeheader(); writer.writerows(manifest)
    logging.info("Concluído: %s QR Codes em %s", len(manifest), args.output.resolve())


if __name__ == "__main__":
    main()
