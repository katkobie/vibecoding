# -*- coding: utf-8 -*-
"""Eksportuje tabele 'oferty' z bazy SQLite do pliku oferty.json (dla strony www)."""
import sqlite3
import json
import os

KAT = os.path.dirname(__file__)
BAZA = os.path.join(KAT, "oferty.db")
WYJSCIE = os.path.join(KAT, "oferty.json")

conn = sqlite3.connect(BAZA)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

rekordy = [dict(r) for r in cur.execute("""
    SELECT id, miasto, tytul, cena, waluta, cena_za_m2, powierzchnia_m2,
           powierzchnia_dzialki_m2, liczba_pokoi, lokalizacja, prywatny,
           agencja, data_dodania, url
    FROM oferty
    ORDER BY miasto, cena DESC
""")]

dane = {
    "zrodlo": "Otodom.pl - domy na sprzedaz",
    "miasta": ["Wroclaw", "Gdansk", "Krakow"],
    "liczba_ofert": len(rekordy),
    "oferty": rekordy,
}

with open(WYJSCIE, "w", encoding="utf-8") as f:
    json.dump(dane, f, ensure_ascii=False, indent=2)

conn.close()
print(f"Zapisano {len(rekordy)} ofert do {WYJSCIE}")
