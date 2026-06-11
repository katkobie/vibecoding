# -*- coding: utf-8 -*-
"""Czyta oferty.db i generuje samodzielny plik oferty.html (dane osadzone w srodku).

Funkcje strony: filtr po miescie, sortowanie, wyszukiwarka tekstowa,
suwaki zakresu (cena, powierzchnia), wykres cen, ulubione (localStorage).

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
      --ramka:#d0d7de; --akcent:#0969da; --akcent-tlo:#ddf4ff; --zloto:#d4a017;
      --sans:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    }
    *{box-sizing:border-box;}
    body{margin:0; background:var(--bg); color:var(--tekst); font-family:var(--sans); font-size:16px; line-height:1.5;}
    .wrap{max-width:1100px; margin:0 auto; padding:24px 18px 60px;}
    h1{font-size:clamp(24px,4vw,34px); margin:0 0 6px;}
    .pod{color:var(--cien); margin:0 0 22px; font-size:14px;}
    .statki{display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:18px;}
    .stat{background:var(--panel); border:1px solid var(--ramka); border-radius:10px; padding:14px 16px;}
    .stat .label{font-size:12px; text-transform:uppercase; letter-spacing:.5px; color:var(--cien);}
    .stat .val{font-size:22px; font-weight:700; margin-top:4px;}

    .panel-box{background:var(--panel); border:1px solid var(--ramka); border-radius:10px; padding:16px; margin-bottom:18px;}
    .panel-box h2{font-size:14px; text-transform:uppercase; letter-spacing:.5px; color:var(--cien); margin:0 0 12px;}

    /* Wykres */
    .wykres{display:flex; align-items:flex-end; gap:20px; height:180px; padding-top:10px;}
    .slupek{flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%;}
    .slupek .bar{width:70%; max-width:90px; background:var(--akcent); border-radius:6px 6px 0 0; transition:height .3s; min-height:2px;}
    .slupek .kwota{font-size:13px; font-weight:700; margin-bottom:6px;}
    .slupek .miasto{font-size:13px; color:var(--cien); margin-top:8px;}

    /* Wyszukiwarka + przyciski */
    .szukaj{width:100%; font:inherit; padding:10px 14px; border:1px solid var(--ramka); border-radius:8px; margin-bottom:14px;}
    .szukaj:focus{outline:2px solid var(--akcent); border-color:var(--akcent);}
    .filtry{display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; align-items:center;}
    .filtr{font:inherit; cursor:pointer; background:var(--panel); color:var(--tekst); border:1px solid var(--ramka); border-radius:20px; padding:7px 16px;}
    .filtr:hover{border-color:var(--akcent);}
    .filtr.akt{background:var(--akcent); color:#fff; border-color:var(--akcent);}
    .filtr.ulub.akt{background:var(--zloto); border-color:var(--zloto);}
    .rozdziel{flex:1;}
    .wyczysc{font:inherit; cursor:pointer; background:none; border:0; color:var(--akcent); text-decoration:underline; padding:6px;}

    /* Suwaki */
    .suwaki{display:grid; grid-template-columns:1fr 1fr; gap:24px;}
    @media (max-width:640px){ .suwaki{grid-template-columns:1fr;} }
    .suwak-grupa .label{font-size:13px; font-weight:600; margin-bottom:6px;}
    .suwak-grupa .zakres{font-size:13px; color:var(--cien); margin-bottom:8px;}
    .suwak-grupa input[type=range]{width:100%; accent-color:var(--akcent);}

    .tabela-wrap{background:var(--panel); border:1px solid var(--ramka); border-radius:10px; overflow-x:auto;}
    table{border-collapse:collapse; width:100%; min-width:820px;}
    th,td{padding:10px 12px; text-align:left; border-bottom:1px solid var(--ramka); font-size:14px; white-space:nowrap;}
    th{background:#f6f8fa; color:var(--tekst); cursor:pointer; user-select:none; position:sticky; top:0;}
    th:hover{color:var(--akcent);}
    th.nosort{cursor:default; color:var(--tekst);}
    th .strz{color:var(--akcent); font-size:11px;}
    td.lok{white-space:normal; min-width:170px; color:var(--cien);}
    tr:last-child td{border-bottom:0;}
    tr:hover td{background:#f6f8fa;}
    .miasto-tag{display:inline-block; font-size:12px; font-weight:600; padding:2px 9px; border-radius:12px; background:var(--akcent-tlo); color:var(--akcent);}
    .cena{font-weight:700;}
    a.link{color:var(--akcent); text-decoration:none;}
    a.link:hover{text-decoration:underline;}
    .gwiazda{cursor:pointer; background:none; border:0; font-size:20px; line-height:1; color:#ccc; padding:0;}
    .gwiazda.akt{color:var(--zloto);}
    .puste{padding:30px; text-align:center; color:var(--cien);}
    @media (max-width:640px){ body{font-size:15px;} }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Domy na sprzedaz - przeglad ofert</h1>
    <p class="pod">Zrodlo: Otodom.pl - Wroclaw, Gdansk, Krakow (po 10 ofert). Dane wygenerowano: <span id="dataGen"></span>.</p>

    <div class="statki" id="statki"></div>

    <div class="panel-box">
      <h2>Srednia cena wg miasta (wg aktualnego filtra)</h2>
      <div class="wykres" id="wykres"></div>
    </div>

    <div class="panel-box">
      <h2>Filtry i wyszukiwanie</h2>
      <input type="text" class="szukaj" id="szukaj" placeholder="Szukaj po lokalizacji lub tytule (np. Krzyki, Wrzeszcz, dom z ogrodem)...">
      <div class="filtry" id="filtry"></div>
      <div class="suwaki">
        <div class="suwak-grupa">
          <div class="label">Cena</div>
          <div class="zakres"><span id="cenaOdTxt"></span> &ndash; <span id="cenaDoTxt"></span></div>
          <input type="range" id="cenaOd"><input type="range" id="cenaDo">
        </div>
        <div class="suwak-grupa">
          <div class="label">Powierzchnia [m&sup2;]</div>
          <div class="zakres"><span id="powOdTxt"></span> &ndash; <span id="powDoTxt"></span></div>
          <input type="range" id="powOd"><input type="range" id="powDo">
        </div>
      </div>
    </div>

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

  const NAZWY = { Wroclaw:'Wrocław', Gdansk:'Gdańsk', Krakow:'Kraków' };
  const KOLEJNOSC_MIAST = ['Wroclaw','Gdansk','Krakow'];

  // ----- granice suwakow z danych -----
  const ceny = OFERTY.map(o => o.cena).filter(c => c != null);
  const powy = OFERTY.map(o => o.powierzchnia_m2).filter(p => p != null);
  const C_MIN = Math.floor(Math.min.apply(null, ceny));
  const C_MAX = Math.ceil(Math.max.apply(null, ceny));
  const P_MIN = Math.floor(Math.min.apply(null, powy));
  const P_MAX = Math.ceil(Math.max.apply(null, powy));

  // ----- ulubione (localStorage) -----
  function wczytajUlub(){
    try { return new Set(JSON.parse(localStorage.getItem('ulubione_oferty') || '[]')); }
    catch(e){ return new Set(); }
  }
  function zapiszUlub(){ localStorage.setItem('ulubione_oferty', JSON.stringify([...stan.ulubione])); }

  const stan = {
    miasto:'wszystkie', sortKol:'cena', sortKier:-1,
    szukaj:'', cenaOd:C_MIN, cenaDo:C_MAX, powOd:P_MIN, powDo:P_MAX,
    tylkoUlub:false, ulubione: wczytajUlub()
  };

  const KOLUMNY = [
    { klucz:'ulubione',      etykieta:'⭐',          typ:'gwiazda', sort:false },
    { klucz:'miasto',        etykieta:'Miasto',     typ:'tekst' },
    { klucz:'cena',          etykieta:'Cena',       typ:'liczba' },
    { klucz:'cena_za_m2',    etykieta:'Cena/m²',  typ:'liczba' },
    { klucz:'powierzchnia_m2', etykieta:'Pow. [m²]', typ:'liczba' },
    { klucz:'powierzchnia_dzialki_m2', etykieta:'Działka [m²]', typ:'liczba' },
    { klucz:'liczba_pokoi',  etykieta:'Pokoje',     typ:'liczba' },
    { klucz:'lokalizacja',   etykieta:'Lokalizacja', typ:'tekst' },
    { klucz:'url',           etykieta:'Link',       typ:'link' },
  ];

  function fmtLiczba(n){ return n==null ? '—' : Math.round(n).toLocaleString('pl-PL'); }
  function fmtCena(n){ return n==null ? '—' : Math.round(n).toLocaleString('pl-PL') + ' zł'; }

  function widoczne(){
    let w = OFERTY.slice();
    if(stan.miasto !== 'wszystkie') w = w.filter(o => o.miasto === stan.miasto);
    if(stan.tylkoUlub) w = w.filter(o => stan.ulubione.has(o.id));
    if(stan.szukaj.trim()){
      const q = stan.szukaj.trim().toLowerCase();
      w = w.filter(o => ((o.lokalizacja||'') + ' ' + (o.tytul||'')).toLowerCase().includes(q));
    }
    // cena: oferty bez ceny pokazujemy tylko gdy suwak ceny nieruszony
    const cenaPelna = (stan.cenaOd===C_MIN && stan.cenaDo===C_MAX);
    w = w.filter(o => o.cena==null ? cenaPelna : (o.cena>=stan.cenaOd && o.cena<=stan.cenaDo));
    w = w.filter(o => o.powierzchnia_m2==null ? true : (o.powierzchnia_m2>=stan.powOd && o.powierzchnia_m2<=stan.powDo));
    w.sort((a,b) => {
      let x = a[stan.sortKol], y = b[stan.sortKol];
      if(x==null) return 1; if(y==null) return -1;
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
      ['Widoczne oferty', w.length],
      ['Średnia cena', fmtCena(sr)],
      ['Średnia cena/m²', srM2==null?'—':fmtLiczba(srM2)+' zł'],
      ['Ulubione', stan.ulubione.size],
    ].map(([l,v]) => '<div class="stat"><div class="label">'+l+'</div><div class="val">'+v+'</div></div>').join('');
  }

  function rysujWykres(w){
    // srednia cena per miasto wsrod widocznych ofert
    const grupy = {};
    KOLEJNOSC_MIAST.forEach(m => grupy[m] = []);
    w.forEach(o => { if(o.cena!=null && grupy[o.miasto]) grupy[o.miasto].push(o.cena); });
    const srednie = KOLEJNOSC_MIAST.map(m => {
      const arr = grupy[m];
      return { miasto:m, sr: arr.length ? arr.reduce((s,c)=>s+c,0)/arr.length : 0 };
    });
    const max = Math.max.apply(null, srednie.map(s=>s.sr).concat([1]));
    document.getElementById('wykres').innerHTML = srednie.map(s => {
      const h = s.sr>0 ? Math.round((s.sr/max)*100) : 0;
      const kwota = s.sr>0 ? (Math.round(s.sr/1000).toLocaleString('pl-PL')+' tys.') : '—';
      return '<div class="slupek"><div class="kwota">'+kwota+'</div>'
        + '<div class="bar" style="height:'+h+'%"></div>'
        + '<div class="miasto">'+NAZWY[s.miasto]+'</div></div>';
    }).join('');
  }

  function rysujFiltry(){
    const miasta = ['wszystkie','Wroclaw','Gdansk','Krakow'];
    let html = miasta.map(m =>
      '<button class="filtr'+(stan.miasto===m?' akt':'')+'" data-m="'+m+'">'
      + (m==='wszystkie' ? 'Wszystkie' : NAZWY[m]) + '</button>'
    ).join('');
    html += '<button class="filtr ulub'+(stan.tylkoUlub?' akt':'')+'" id="btnUlub">⭐ Tylko ulubione</button>';
    html += '<span class="rozdziel"></span><button class="wyczysc" id="btnWyczysc">Wyczyść filtry</button>';
    const cont = document.getElementById('filtry');
    cont.innerHTML = html;
    cont.querySelectorAll('button[data-m]').forEach(b => b.onclick = () => { stan.miasto = b.dataset.m; rysuj(); });
    document.getElementById('btnUlub').onclick = () => { stan.tylkoUlub = !stan.tylkoUlub; rysuj(); };
    document.getElementById('btnWyczysc').onclick = wyczysc;
  }

  function rysujNaglowki(){
    document.getElementById('naglowki').innerHTML = KOLUMNY.map(k => {
      if(k.sort===false) return '<th class="nosort">'+k.etykieta+'</th>';
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
    if(k.klucz==='ulubione'){
      const akt = stan.ulubione.has(o.id);
      return '<td><button class="gwiazda'+(akt?' akt':'')+'" data-fav="'+o.id+'" title="Dodaj/usun z ulubionych">'+(akt?'★':'☆')+'</button></td>';
    }
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
    if(!w.length){ body.innerHTML = '<tr><td colspan="'+KOLUMNY.length+'" class="puste">Brak ofert spelniajacych kryteria.</td></tr>'; return; }
    body.innerHTML = w.map(o => '<tr>' + KOLUMNY.map(k => komorka(o,k)).join('') + '</tr>').join('');
    body.querySelectorAll('button[data-fav]').forEach(b => b.onclick = () => {
      const id = Number(b.dataset.fav);
      if(stan.ulubione.has(id)) stan.ulubione.delete(id); else stan.ulubione.add(id);
      zapiszUlub(); rysuj();
    });
  }

  function rysuj(){
    const w = widoczne();
    rysujFiltry(); rysujNaglowki(); rysujStatki(w); rysujWykres(w); rysujTabele(w);
  }

  // ----- suwaki -----
  function ustawSuwaki(){
    const cOd=document.getElementById('cenaOd'), cDo=document.getElementById('cenaDo');
    const pOd=document.getElementById('powOd'), pDo=document.getElementById('powDo');
    [cOd,cDo].forEach(s=>{ s.min=C_MIN; s.max=C_MAX; s.step=10000; });
    [pOd,pDo].forEach(s=>{ s.min=P_MIN; s.max=P_MAX; s.step=5; });
    cOd.value=stan.cenaOd; cDo.value=stan.cenaDo; pOd.value=stan.powOd; pDo.value=stan.powDo;
    function aktCena(){
      let a=Number(cOd.value), b=Number(cDo.value);
      if(a>b){ if(this===cOd) b=a; else a=b; cOd.value=a; cDo.value=b; }
      stan.cenaOd=a; stan.cenaDo=b; aktTeksty(); rysuj();
    }
    function aktPow(){
      let a=Number(pOd.value), b=Number(pDo.value);
      if(a>b){ if(this===pOd) b=a; else a=b; pOd.value=a; pDo.value=b; }
      stan.powOd=a; stan.powDo=b; aktTeksty(); rysuj();
    }
    cOd.oninput=aktCena; cDo.oninput=aktCena; pOd.oninput=aktPow; pDo.oninput=aktPow;
  }
  function aktTeksty(){
    document.getElementById('cenaOdTxt').textContent = fmtCena(stan.cenaOd);
    document.getElementById('cenaDoTxt').textContent = fmtCena(stan.cenaDo);
    document.getElementById('powOdTxt').textContent = stan.powOd + ' m²';
    document.getElementById('powDoTxt').textContent = stan.powDo + ' m²';
  }

  function wyczysc(){
    stan.miasto='wszystkie'; stan.szukaj=''; stan.tylkoUlub=false;
    stan.cenaOd=C_MIN; stan.cenaDo=C_MAX; stan.powOd=P_MIN; stan.powDo=P_MAX;
    document.getElementById('szukaj').value='';
    document.getElementById('cenaOd').value=C_MIN; document.getElementById('cenaDo').value=C_MAX;
    document.getElementById('powOd').value=P_MIN; document.getElementById('powDo').value=P_MAX;
    aktTeksty(); rysuj();
  }

  document.getElementById('szukaj').oninput = (e) => { stan.szukaj = e.target.value; rysuj(); };
  ustawSuwaki(); aktTeksty(); rysuj();
  </script>
</body>
</html>
"""

with open(WYJSCIE, "w", encoding="utf-8") as f:
    f.write(HTML.replace("__DANE__", dane_json))

print(f"Wygenerowano {WYJSCIE} ({len(oferty)} ofert)")
