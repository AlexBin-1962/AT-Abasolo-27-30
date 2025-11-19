#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV -> JSON (mínimo) para ET-27 (nivel SECCIÓN)
Usa únicamente las columnas: SECCION, CASILLA, LOCALIDAD, DOMICILIO.

Salida:
  - casillas_min_rows.json
  - casillas_min_por_seccion.json

Uso:
  python casillas_min_csv_a_json.py --csv "ruta/al.csv" --outdir "salida/"
"""

import argparse, csv, json, unicodedata, re, os
from collections import defaultdict

def nfc(s):
    return unicodedata.normalize("NFC", s) if isinstance(s, str) else s

def norm_key(s:str)->str:
    if s is None: return ""
    s = nfc(str(s)).strip().upper()
    s = s.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U").replace("Ñ","N")
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

# Map flexible de encabezados
MAP = {
    "SECCION": {"SECCION","SECC","SECCION_ID"},
    "CASILLA": {"CASILLA","TIPO","TIPO_CASILLA"},
    "LOCALIDAD": {"LOCALIDAD","LOC","POBLACION"},
    "DOMICILIO": {"DOMICILIO","DIRECCION","DIRECCION_CASILLA"}
}

def canonicalize(headers):
    canon = []
    for h in headers:
        nk = norm_key(h)
        found = None
        for target, variants in MAP.items():
            if nk in {norm_key(v) for v in variants}:
                found = target
                break
        canon.append(found or f"COLUMN")
    return canon

def read_rows(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.reader(f)
        headers = next(rdr, [])
        canon = canonicalize(headers)
        out = []
        for r in rdr:
            d = {}
            for k, v in zip(canon, r):
                if k in {"SECCION","CASILLA","LOCALIDAD","DOMICILIO"}:
                    d[k] = nfc(v).strip() if isinstance(v,str) else v
            # garantizar las 4 llaves aunque falten
            for k in ("SECCION","CASILLA","LOCALIDAD","DOMICILIO"):
                d.setdefault(k, "")
            out.append(d)
        return out

def aggregate(rows):
    idx = {}
    for r in rows:
        sec = str(r.get("SECCION") or "").strip()
        if not sec: 
            continue
        it = idx.get(sec)
        if not it:
            it = {"SECCION": sec, "req_rep": 0, "casillas": []}
            idx[sec] = it
        it["req_rep"] += 1
        it["casillas"].append({
            "CASILLA": r.get("CASILLA",""),
            "LOCALIDAD": r.get("LOCALIDAD",""),
            "DOMICILIO": r.get("DOMICILIO","")
        })
    # ordenar por SECCION asc (num si se puede)
    def keyfn(x):
        s = x["SECCION"]
        return (0,int(s)) if s.isdigit() else (1,s)
    return sorted(idx.values(), key=keyfn)

def write_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    rows = read_rows(args.csv)
    write_json(rows, os.path.join(args.outdir, "casillas_min_rows.json"))
    agg  = aggregate(rows)
    write_json(agg, os.path.join(args.outdir, "casillas_min_por_seccion.json"))
    print(f"[OK] Filas leídas: {len(rows)}")
    print(f"[OK] Secciones únicas: {len(agg)}")
    print("[OUT]", os.path.join(args.outdir, "casillas_min_rows.json"))
    print("[OUT]", os.path.join(args.outdir, "casillas_min_por_seccion.json"))

if __name__ == "__main__":
    main()
