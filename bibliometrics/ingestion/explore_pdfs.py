"""
explore_pdfs.py — Exploración del piloto de extracción (Componente B).

OBJETIVO (piloto, NO parsing final):
  Entender cómo están estructurados los boletines SAO en PDF antes de construir
  el pipeline de extracción. Responde:
    1. ¿Cuántas páginas tiene cada boletín?
    2. ¿1 PDF = 1 artículo, o varios?
    3. ¿Qué "pistas" estructurales existen (título, resumen, keywords,
       secciones, referencias)?

Uso:
    python bibliometrics/ingestion/explore_pdfs.py  (con el .venv activado)

No modifica los PDFs originales. Solo lee e imprime un resumen por consola.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber

# Carpeta de muestras del piloto (data/samples/boletines_sao no existe aún;
# los PDFs están directamente en data/samples/).
SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"

# Marcadores que, segun las Instrucciones para Autores del Boletin SAO,
# ayudan a delimitar un articulo dentro del PDF.
STRUCTURE_HINTS = [
    "resumen",
    "abstract",
    "palabras clave",
    "key words",
    "keywords",
    "introduccion",
    "introducción",
    "metodos",
    "métodos",
    "resultados",
    "discusion",
    "discusión",
    "literatura citada",
    "referencias",
    "agradecimientos",
]


def explore_pdf(pdf_path: Path) -> None:
    print("=" * 78)
    print(f"ARCHIVO: {pdf_path.name}")
    print("=" * 78)

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        print(f"Paginas: {num_pages}")

        full_text_lower = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text_lower.append(text.lower())
        joined = "\n".join(full_text_lower)

        # Conteo de pistas estructurales en todo el documento.
        print("\nPistas estructurales (nº de apariciones en todo el PDF):")
        for hint in STRUCTURE_HINTS:
            count = joined.count(hint)
            if count:
                print(f"  - {hint:<18} {count}")

        # Vista previa de la primera pagina (donde suele estar el encabezado).
        first_page_text = pdf.pages[0].extract_text() or ""
        preview = first_page_text.strip()[:900]
        print("\n--- Vista previa PRIMERA pagina (900 chars) ---")
        print(preview)
        print("--- fin vista previa ---\n")


def main() -> None:
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron PDFs en {SAMPLES_DIR}")
        return
    print(f"Encontrados {len(pdfs)} PDFs en {SAMPLES_DIR}\n")
    for pdf_path in pdfs:
        explore_pdf(pdf_path)


if __name__ == "__main__":
    main()
