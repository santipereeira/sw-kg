"""
step_final.py — Paso final antes de ejecutar Yatter + Morph-KGC
================================================================
Los CSVs de PDI extra (clean_castillos.csv, etc.) no tienen id_concello
porque se generaron antes del catálogo unificado.
Este script los enriquece con id_concello e id_provincia
haciéndoles un join contra catalog_concellos.csv.

Ejecutar desde la raíz del proyecto:
    python scripts/step_final.py
"""

import pandas as pd
import unicodedata
import re
from pathlib import Path

CLEAN_DIR = Path("data/clean")

PDI_SLUGS = [
    "castillos", "fervenzas", "iglesias", "construccion_tradicional",
    "monasterios", "espacios_naturales", "otros", "puentes", "yacimientos",
    "playas_genericas",
]


def slugify(text):
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower().strip())
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


PROV_CANON = {
    "a coruña": "A Coruña", "la coruña": "A Coruña", "coruña": "A Coruña",
    "a coruña province": "A Coruña", "a coruna province": "A Coruña",
    "lugo": "Lugo", "lugo province": "Lugo",
    "ourense": "Ourense", "orense": "Ourense", "ourense province": "Ourense",
    "pontevedra": "Pontevedra", "pontevedra province": "Pontevedra",
    "viana do castelo": "Viana Do Castelo", "viana de castelo": "Viana Do Castelo",
    "braga": "Braga", "bragança": "Bragança", "braganca": "Bragança",
    "vila real": "Vila Real",
}

PAIS_CANON = {
    "españa": "España", "espana": "España", "spain": "España",
    "portugal": "Portugal",
}


def canon_prov(raw):
    if not isinstance(raw, str):
        return "Descoñecida"
    return PROV_CANON.get(raw.strip().lower(), raw.strip().title())


def canon_pais(raw):
    if not isinstance(raw, str):
        return "Descoñecido"
    return PAIS_CANON.get(raw.strip().lower(), raw.strip().title())


def concello_id(concello, provincia, pais):
    return f"{slugify(concello)}-{slugify(provincia)}-{slugify(pais)}"


# ── Cargar catálogo unificado ─────────────────────────────────────────────────
cat = pd.read_csv(CLEAN_DIR / "catalog_concellos.csv", encoding="utf-8-sig")
# Crear clave de join igual que la función concello_id
cat["_join_key"] = cat["id_concello"]
cat_lookup = cat.set_index("id_concello")[["id_provincia"]].to_dict(orient="index")

print(f"Catálogo cargado: {len(cat)} concellos\n")

# ── Procesar cada CSV de PDI ──────────────────────────────────────────────────
for slug in PDI_SLUGS:
    path = CLEAN_DIR / f"clean_{slug}.csv"
    if not path.exists():
        print(f"⚠️  No encontrado: {path.name}")
        continue

    df = pd.read_csv(path, encoding="utf-8-sig")

    # Normalizar provincia y pais por si acaso
    if "provincia" in df.columns:
        df["provincia"] = df["provincia"].apply(canon_prov)
    if "country" in df.columns:
        df["pais"] = df["country"].apply(canon_pais)
    elif "pais" not in df.columns:
        df["pais"] = "España"

    # Calcular id_concello desde las columnas del CSV
    df["id_concello"] = df.apply(
        lambda r: concello_id(
            r.get("concello", ""),
            r.get("provincia", ""),
            r.get("pais", "España")
        ), axis=1
    )

    # Añadir id_provincia desde el catálogo
    df["id_provincia"] = df["id_concello"].map(
        lambda k: cat_lookup.get(k, {}).get("id_provincia", "")
    )

    # Detectar concellos que no matchean el catálogo
    sin_prov = df[df["id_provincia"] == ""]
    if len(sin_prov) > 0:
        print(f"  ⚠️  {slug}: {len(sin_prov)} filas sin provincia en catálogo:")
        for _, r in sin_prov.head(3).iterrows():
            print(f"       → concello='{r.get('concello','')}' provincia='{r.get('provincia','')}' pais='{r.get('pais','')}'")

    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"✅ {path.name}: {len(df)} filas, id_concello e id_provincia añadidos")

# ── Procesar playas bandera azul ──────────────────────────────────────────────
azul_path = CLEAN_DIR / "clean_praias_bandera_azul.csv"
if azul_path.exists():
    df_azul = pd.read_csv(azul_path, encoding="utf-8-sig")

    if "id_concello" not in df_azul.columns:
        df_azul["provincia_canon"] = df_azul["PROVINCIA"].apply(canon_prov)
        df_azul["pais"] = "España"
        df_azul["id_concello"] = df_azul.apply(
            lambda r: concello_id(r["CONCELLO"].strip().title(), r["provincia_canon"], "España"),
            axis=1
        )

    df_azul["id_provincia"] = df_azul["id_concello"].map(
        lambda k: cat_lookup.get(k, {}).get("id_provincia", "a-coruna")
    )
    df_azul.to_csv(azul_path, index=False, encoding="utf-8-sig")
    print(f"✅ {azul_path.name}: id_provincia añadido")

# ── Exportar playas genéricas sin duplicados ──────────────────────────────────
gen_path = CLEAN_DIR / "clean_playas_genericas.csv"
if gen_path.exists():
    df_gen = pd.read_csv(gen_path, encoding="utf-8-sig")
    if "es_duplicado" in df_gen.columns:
        df_sin = df_gen[~df_gen["es_duplicado"]].copy()
    else:
        df_sin = df_gen.copy()
    out = CLEAN_DIR / "clean_playas_genericas_sin_dup.csv"
    df_sin.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"✅ clean_playas_genericas_sin_dup.csv: {len(df_sin)} filas")

print("\n✨ Listo. Ahora ejecuta:")
print("   yatter -i mappings/mapping_v2.yarrrml.yaml -o mappings/mapping.rml.ttl")
print("   python -m morphkgc mappings/config.ini")
