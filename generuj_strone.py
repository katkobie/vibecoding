# -*- coding: utf-8 -*-
"""Czyta oferty.db i generuje samodzielny plik oferty.html (dane osadzone w srodku).

Uruchom ponownie po kazdej aktualizacji bazy, zeby odswiezyc strone.
"""
import sqlite3
import json
import os
from datetime import datetime

KAT = os.path.dirname(__file__)
BAZA = os.path.join(KAT, "oferty.db")
WYJSCIE = os.path.join(KAT, "oferty.html")

conn = sqlite3.connect(BAZA)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
oferty = [dict(r) for r in cur.execute("""
    SELECT id, miasto, tytul, cena, waluta, cena_za_m2, powierzchnia_m2,
           powierzchnia_dzialki_m2, liczba_pokoi, lokalizacja, prywatny,
           agencja, data_dodania, url
    FROM oferty ORDER BY miasto, cena DESC
""")]
conn.close()

dane = {
    "wygenerowano": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "oferty": oferty,
}
dane_json = json.dumps(dane, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Domy na sprzedaz - przeglad ofert (Otodom)</title>
  <style>
    :root{
      --bg:#f6f8fa; --panel:#fff; --tekst:#1f2328; --cien:#59636e;
      --ramka:#d0d7de; --akcent:#0969da; --akcent-tlo:#ddf4ff;
      --sans:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    }
    *{box-sizing:border-box;}
    body{margin:0; background:var(--bg); color:var(--tekst); font-family:var(--sans); font-size:16px; line-height:1.5;}
    .wrap{max-width:1100px; margin:0 auto; padding:24px 18px 60px;}
    h1{font-size:clamp(24px,4vw,34px); margin:0 0 6px;}
    .pod{color:var(--cien); margin:0 0 22px; font-size:14px;}
    .statki{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; margin-bottom:22px;}
    .stat{background:var(--panel); border:1px solid var(--ramka); border-radius:10px; padding:14px 16px;}
    .stat .label{font-size:12px; text-transform:uppercase; letter-spacing:.5px; color:var(--cien);}
    .stat .val{font-size:22px; font-weight:700; margin-top:4px;}
    .filtry{display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px;}
    .filtr{font:inherit; cursor:pointer; background:var(--panel); color:var(--tekst); border:1px solid var(--ramka); border-radius:20px; padding:7px 16px;}
    .filtr:hover{border-color:var(--akcent);}
    .filtr.akt{background:var(--akcent); color:#fff; border-color:var(--akcent);}
    .tabela-wrap{background:var(--panel); border:1px solid var(--ramka); border-radius:10px; overflow-x:auto;}
    table{border-collapse:collapse; width:100%; min-width:760px;}
    th,td{padding:10px 12px; text-align:left; border-bottom:1px solid var(--ramka); font-size:14px; white-space:nowrap;}
    th{background:#f6f8fa; color:var(--tekst); cursor:pointer; user-select:none; position:sticky; top:0;}
    th:hover{color:var(--akcent);}
    th .strz{color:var(--akcent); font-size:11px;}
    td.lok{white-space:normal; min-width:180px; color:var(--cien);}
    tr:last-child td{border-bottom:0;}
    tr:hover td{background:#f6f8fa;}
    .miasto-tag{display:inline-block; font-size:12px; font-weight:600; padding:2px 9px; border-radius:12px; background:var(--akcent-tlo); color:var(--akcent);}
    .cena{font-weight:700;}
    a.link{color:var(--akcent); text-decoration:none;}
    a.link:hover{text-decoration:underline;}
    .puste{padding:30px; text-align:center; color:var(--cien);}
    @media (max-width:640px){ body{font-size:15px;} }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Domy na sprzedaz - przeglad ofert</h1>
    <p class="pod">Zrodlo: Otodom.pl - Wroclaw, Gdansk, Krakow (po 10 ofert). Dane wygenerowano: <span id="dataGen"></span>.</p>

    <div class="statki" id="statki"></div>

    <div class="filtry" id="filtry"></div>

    <div class="tabela-wrap">
      <table>
        <thead><tr id="naglowki"></tr></thead>
        <tbody id="body"></tbody>
      </table>
    </div>
  </div>

  <script id="dane" type="application/json">__DANE__</script>
  <script>
  "use strict";
  const DANE = JSON.parse(document.getElementById('dane').textContent);
  const OFERTY = DANE.oferty;
  document.getElementById('dataGen').textContent = DANE.wygenerowano;

  const ETYKIETY = { Wroclaw:'Wroclaw', Gdansk:'Gdansk', Krakow:'Krakow' };
  // ladne nazwy z polskimi znakami
  const NAZWY = { Wroclaw:'Wrocław', Gdansk:'Gdańsk', Krakow:'Kraków' };

  const KOLUMNY = [
    { klucz:'miasto',        etykieta:'Miasto',     typ:'tekst' },
    { klucz:'cena',          etykieta:'Cena',       typ:'liczba' },
    { klucz:'cena_za_m2',    etykieta:'Cena/m²', typ:'liczba' },
    { klucz:'powierzchnia_m2', etykieta:'Pow. [m²]', typ:'liczba' },
    { klucz:'powierzchnia_dzialki_m2', etykieta:'Działka [m²]', typ:'liczba' },
    { klucz:'liczba_pokoi',  etykieta:'Pokoje',     typ:'liczba' },
    { klucz:'lokalizacja',   etykieta:'Lokalizacja', typ:'tekst' },
    { klucz:'url',           etykieta:'Link',       typ:'link' },
  ];

  let stan = { miasto:'wszystkie', sortKol:'cena', sortKier:-1 };

  function fmtLiczba(n){ return n==null ? '—' : Math.round(n).toLocaleString('pl-PL'); }
  function fmtCena(n){ return n==null ? '—' : Math.round(n).toLocaleString('pl-PL') + ' zł'; }

  function widoczne(){
    let w = OFERTY.slice();
    if(stan.miasto !== 'wszystkie') w = w.filter(o => o.miasto === stan.miasto);
    w.sort((a,b) => {
      let x = a[stan.sortKol], y = b[stan.sortKol];
      if(x==null) return 1; if(y==null) return -1;   // puste na koniec
      if(typeof x === 'string') return x.localeCompare(y,'pl') * stan.sortKier;
      return (x - y) * stan.sortKier;
    });
    return w;
  }

  function rysujStatki(w){
    const zCena = w.filter(o => o.cena != null);
    const sr = zCena.length ? zCena.reduce((s,o)=>s+o.cena,0)/zCena.length : null;
    const zM2 = w.filter(o => o.cena_za_m2 != null);
    const srM2 = zM2.length ? zM2.reduce((s,o)=>s+o.cena_za_m2,0)/zM2.length : null;
    document.getElementById('statki').innerHTML = [
      ['Liczba ofert', w.length],
      ['Średnia cena', fmtCena(sr)],
      ['Średnia cena/m²', srM2==null?'—':fmtLiczba(srM2)+' zł'],
    ].map(([l,v]) => '<div class="stat"><div class="label">'+l+'</div><div class="val">'+v+'</div></div>').join('');
  }

  function rysujFiltry(){
    const miasta = ['wszystkie','Wroclaw','Gdansk','Krakow'];
    document.getElementById('filtry').innerHTML = miasta.map(m =>
      '<button class="filtr'+(stan.miasto===m?' akt':'')+'" data-m="'+m+'">'
      + (m==='wszystkie' ? 'Wszystkie' : NAZWY[m]) + '</button>'
    ).join('');
    document.querySelectorAll('.filtr').forEach(b => b.onclick = () => { stan.miasto = b.dataset.m; rysuj(); });
  }

  function rysujNaglowki(){
    document.getElementById('naglowki').innerHTML = KOLUMNY.map(k => {
      const strz = stan.sortKol===k.klucz ? ' <span class="strz">'+(stan.sortKier===1?'▲':'▼')+'</span>' : '';
      return '<th data-k="'+k.klucz+'">'+k.etykieta+strz+'</th>';
    }).join('');
    document.querySelectorAll('th[data-k]').forEach(th => th.onclick = () => {
      const k = th.dataset.k;
      if(stan.sortKol===k) stan.sortKier *= -1; else { stan.sortKol = k; stan.sortKier = 1; }
      rysuj();
    });
  }

  function komorka(o, k){
    if(k.klucz==='miasto') return '<td><span class="miasto-tag">'+NAZWY[o.miasto]+'</span></td>';
    if(k.klucz==='cena') return '<td class="cena">'+fmtCena(o.cena)+'</td>';
    if(k.klucz==='cena_za_m2') return '<td>'+(o.cena_za_m2==null?'—':fmtLiczba(o.cena_za_m2)+' zł')+'</td>';
    if(k.klucz==='liczba_pokoi') return '<td>'+(o.liczba_pokoi==null?'—':o.liczba_pokoi)+'</td>';
    if(k.typ==='liczba') return '<td>'+fmtLiczba(o[k.klucz])+'</td>';
    if(k.klucz==='lokalizacja') return '<td class="lok">'+(o.lokalizacja||'—')+'</td>';
    if(k.klucz==='url') return '<td>'+(o.url?'<a class="link" href="'+o.url+'" target="_blank" rel="noopener">otwórz ↗</a>':'—')+'</td>';
    return '<td>'+(o[k.klucz]||'—')+'</td>';
  }

  function rysujTabele(w){
    const body = document.getElementById('body');
    if(!w.length){ body.innerHTML = '<tr><td colspan="'+KOLUMNY.length+'" class="puste">Brak ofert.</td></tr>'; return; }
    body.innerHTML = w.map(o => '<tr>' + KOLUMNY.map(k => komorka(o,k)).join('') + '</tr>').join('');
  }

  function rysuj(){
    const w = widoczne();
    rysujFiltry(); rysujNaglowki(); rysujStatki(w); rysujTabele(w);
  }
  rysuj();
  </script>
</body>
</html>
"""

with open(WYJSCIE, "w", encoding="utf-8") as f:
    f.write(HTML.replace("__DANE__", dane_json))

print(f"Wygenerowano {WYJSCIE} ({len(oferty)} ofert)")
