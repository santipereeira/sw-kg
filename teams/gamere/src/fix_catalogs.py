"""
fix_catalogs.py — Repara catalog_concellos.csv y catalog_provincias.csv
=======================================================================
Ejecutar UNA VEZ desde la raíz del proyecto:
    python scripts/fix_catalogs.py

Problema que resuelve:
  El CSV de bandera azul tiene "A Coruña Province" / "Pontevedra Province"
  como nombre de provincia (viene del campo wikidata_provincia en inglés).
  El script de build las dejó como provincias distintas de "A Coruña".
  Resultado: Arteixo aparece dos veces con URIs distintas.

Solución:
  1. Ampliar PROVINCIA_CANON para cubrir "X Province" y "X province"
  2. Recomputar id_concello para todos los afectados
  3. Fusionar duplicados (el que tiene código INE prevalece)
  4. Limpiar catalog_provincias.csv (eliminar las filas "X Province")
  5. Añadir id_provincia a catalog_concellos.csv para que el mapping funcione
"""

import pandas as pd
import unicodedata
import re
from pathlib import Path

CLEAN_DIR = Path("data/clean")

# ── Tabla maestra de provincias ───────────────────────────────────────────────
# Cualquier variante → nombre canónico
PROV_CANON = {
    # Gallego/castellano
    "a coruña":                "A Coruña",
    "la coruña":               "A Coruña",
    "coruña":                  "A Coruña",
    # Wikidata en inglés
    "a coruña province":       "A Coruña",
    "a coruna province":       "A Coruña",
    "province of a coruña":    "A Coruña",
    "lugo":                    "Lugo",
    "lugo province":           "Lugo",
    "province of lugo":        "Lugo",
    "ourense":                 "Ourense",
    "orense":                  "Ourense",
    "ourense province":        "Ourense",
    "province of ourense":     "Ourense",
    "pontevedra":              "Pontevedra",
    "pontevedra province":     "Pontevedra",
    "province of pontevedra":  "Pontevedra",
    # Portugal
    "viana do castelo":        "Viana Do Castelo",
    "viana de castelo":        "Viana Do Castelo",
    "braga":                   "Braga",
    "bragança":                "Bragança",
    "braganca":                "Bragança",
    "vila real":               "Vila Real",
}

PROV_CODIGO = {
    "A Coruña":        15,
    "Lugo":            27,
    "Ourense":         32,
    "Pontevedra":      36,
    "Viana Do Castelo": 0,
    "Braga":           0,
    "Bragança":        0,
    "Vila Real":       0,
}

PROV_PAIS = {
    "A Coruña": "España", "Lugo": "España",
    "Ourense": "España",  "Pontevedra": "España",
    "Viana Do Castelo": "Portugal", "Braga": "Portugal",
    "Bragança": "Portugal", "Vila Real": "Portugal",
}


def slugify(text):
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower().strip())
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def canon_prov(raw: str) -> str:
    if not isinstance(raw, str):
        return "Descoñecida"
    key = raw.strip().lower()
    return PROV_CANON.get(key, raw.strip().title())


def concello_id(concello, provincia, pais):
    return f"{slugify(concello)}-{slugify(provincia)}-{slugify(pais)}"


# ── Leer catálogo actual ──────────────────────────────────────────────────────
df = pd.read_csv(CLEAN_DIR / "catalog_concellos.csv", encoding="utf-8-sig")
print(f"Filas originales: {len(df)}")
print(f"Provincias únicas antes: {sorted(df['provincia'].unique())}\n")

# ── Corregir provincia en cada fila ──────────────────────────────────────────
df["provincia"] = df["provincia"].apply(canon_prov)

# Recomputar id_concello con la provincia canónica
df["id_concello"] = df.apply(
    lambda r: concello_id(r["concello"], r["provincia"], r["pais"]), axis=1
)

# Actualizar codigo_provincia y pais
df["codigo_provincia"] = df["provincia"].map(PROV_CODIGO).fillna(0).astype(int)

# ── Fusionar duplicados: el que tiene codigo_concello > 0 prevalece ───────────
df = df.sort_values("codigo_concello", ascending=False)
df = df.drop_duplicates("id_concello", keep="first")
df = df.sort_values(["pais", "provincia", "concello"]).reset_index(drop=True)

print(f"Filas tras deduplicar: {len(df)}")
print(f"Provincias únicas después: {sorted(df['provincia'].unique())}\n")

# ── Añadir id_provincia (necesario para el mapping) ───────────────────────────
df["id_provincia"] = df["provincia"].apply(slugify)

# ── Guardar catalog_concellos.csv corregido ───────────────────────────────────
df.to_csv(CLEAN_DIR / "catalog_concellos.csv", index=False, encoding="utf-8-sig")
print(f"✅ catalog_concellos.csv guardado: {len(df)} concellos únicos")
print(f"   ├─ España:   {(df.pais=='España').sum()}")
print(f"   └─ Portugal: {(df.pais=='Portugal').sum()}")

# ── Reconstruir catalog_provincias.csv limpio ─────────────────────────────────
prov_rows = []
for prov, codigo in PROV_CODIGO.items():
    prov_rows.append({
        "provincia":        prov,
        "codigo_provincia": codigo,
        "pais":             PROV_PAIS[prov],
        "id_provincia":     slugify(prov),
        "id_pais":          slugify(PROV_PAIS[prov]),
    })

df_prov = pd.DataFrame(prov_rows)
df_prov.to_csv(CLEAN_DIR / "catalog_provincias.csv", index=False, encoding="utf-8-sig")
print(f"\n✅ catalog_provincias.csv reconstruido: {len(df_prov)} provincias")
for _, r in df_prov.iterrows():
    print(f"   {r['id_provincia']} | {r['provincia']} | {r['pais']} | código {r['codigo_provincia']}")

# ── Verificación rápida: concellos con provincia descoñecida ──────────────────
unknown = df[~df["provincia"].isin(PROV_CODIGO.keys())]
if len(unknown):
    print(f"\n⚠️  {len(unknown)} concellos con provincia no reconocida:")
    print(unknown[["concello", "provincia", "pais"]].to_string())
else:
    print("\n✅ Todos los concellos tienen provincia reconocida.")

print("\n✨ Catalogs reparados. Continúa con el resto del script.")
