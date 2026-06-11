# -*- coding: utf-8 -*-
"""Czyta oferty.db i generuje samodzielny plik oferty.html (dane osadzone w srodku).

Uklad: karty ofert (jak portal). Funkcje: filtr po miescie, wyszukiwarka,
suwaki zakresu (cena, powierzchnia), sortowanie (lista), wykres cen,
ulubione (localStorage).

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
      --bg:#f3f5f8; --panel:#fff; --tekst:#1f2328; --cien:#5b6470;
      --ramka:#e4e8ee; --akcent:#0969da; --zloto:#e6a700;
      --wroclaw:#0969da; --gdansk:#0a8a6f; --krakow:#8250df;
      --sans:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      --cien-karta:0 1px 3px rgba(20,30,50,.08), 0 8px 24px rgba(20,30,50,.05);
      --cien-hover:0 6px 16px rgba(20,30,50,.12), 0 18px 40px rgba(20,30,50,.10);
    }
    *{box-sizing:border-box;}
    html{scroll-behavior:smooth;}
    body{margin:0; background:var(--bg); color:var(--tekst); font-family:var(--sans); font-size:16px; line-height:1.5;}
    .wrap{max-width:1180px; margin:0 auto; padding:0 18px 70px;}

    /* Naglowek z gradientem */
    .hero{background:linear-gradient(135deg,#0969da 0%,#0a8a6f 55%,#8250df 120%); color:#fff; margin-bottom:26px;
          border-radius:0 0 22px 22px; box-shadow:0 10px 30px rgba(9,105,218,.18);}
    .hero .inner{max-width:1180px; margin:0 auto; padding:38px 18px 34px;}
    .hero h1{font-size:clamp(26px,4.5vw,40px); margin:0 0 8px; letter-spacing:-.5px;}
    .hero p{margin:0; opacity:.92; font-size:15px; max-width:60ch;}

    .statki{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; margin:-30px 0 22px;}
    .stat{background:var(--panel); border:1px solid var(--ramka); border-radius:14px; padding:16px 18px; box-shadow:var(--cien-karta);}
    .stat .label{font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:var(--cien);}
    .stat .val{font-size:24px; font-weight:800; margin-top:4px; letter-spacing:-.5px;}

    .panel-box{background:var(--panel); border:1px solid var(--ramka); border-radius:16px; padding:20px; margin-bottom:20px; box-shadow:var(--cien-karta);}
    .panel-box h2{font-size:12px; text-transform:uppercase; letter-spacing:.6px; color:var(--cien); margin:0 0 14px;}

    /* Wykres */
    .wykres{display:flex; align-items:flex-end; gap:24px; height:180px; padding-top:10px;}
    .slupek{flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%;}
    .slupek .bar{width:72%; max-width:96px; border-radius:8px 8px 0 0; transition:height .35s ease; min-height:3px;}
    .slupek.Wroclaw .bar{background:linear-gradient(180deg,#3b8eea,var(--wroclaw));}
    .slupek.Gdansk .bar{background:linear-gradient(180deg,#16a98a,var(--gdansk));}
    .slupek.Krakow .bar{background:linear-gradient(180deg,#9b6ef0,var(--krakow));}
    .slupek .kwota{font-size:13px; font-weight:800; margin-bottom:7px;}
    .slupek .miasto{font-size:13px; color:var(--cien); margin-top:9px; font-weight:600;}

    /* Filtry */
    .szukaj{width:100%; font:inherit; padding:12px 16px; border:1px solid var(--ramka); border-radius:10px; margin-bottom:14px; background:#fbfcfe;}
    .szukaj:focus{outline:2px solid var(--akcent); border-color:var(--akcent); background:#fff;}
    .filtry{display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; align-items:center;}
    .filtr{font:inherit; cursor:pointer; background:var(--panel); color:var(--tekst); border:1px solid var(--ramka); border-radius:22px; padding:8px 17px; transition:all .15s;}
    .filtr:hover{border-color:var(--akcent); transform:translateY(-1px);}
    .filtr.akt{background:var(--akcent); color:#fff; border-color:var(--akcent);}
    .filtr.ulub.akt{background:var(--zloto); border-color:var(--zloto);}
    .rozdziel{flex:1;}
    .wyczysc{font:inherit; cursor:pointer; background:none; border:0; color:var(--akcent); text-decoration:underline; padding:6px;}
    .sortuj{font:inherit; padding:8px 12px; border:1px solid var(--ramka); border-radius:10px; background:#fbfcfe; cursor:pointer;}

    .suwaki{display:grid; grid-template-columns:1fr 1fr; gap:26px;}
    @media (max-width:640px){ .suwaki{grid-template-columns:1fr;} }
    .suwak-grupa .label{font-size:13px; font-weight:700; margin-bottom:6px;}
    .suwak-grupa .zakres{font-size:13px; color:var(--cien); margin-bottom:9px;}
    .suwak-grupa input[type=range]{width:100%; accent-color:var(--akcent);}

    .pasek-wynikow{display:flex; align-items:center; gap:14px; margin:4px 2px 16px;}
    .pasek-wynikow .licznik{font-weight:700;}
    .pasek-wynikow .rozdziel{flex:1;}

    /* Siatka kart */
    .siatka{display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:18px;}
    .karta{background:var(--panel); border:1px solid var(--ramka); border-radius:16px; overflow:hidden;
           box-shadow:var(--cien-karta); transition:transform .18s ease, box-shadow .18s ease; display:flex; flex-direction:column;}
    .karta:hover{transform:translateY(-4px); box-shadow:var(--cien-hover);}
    .karta .pasek{height:6px; background:var(--kolor);}
    .karta-tresc{padding:16px 18px 18px; display:flex; flex-direction:column; gap:10px; flex:1;}
    .karta-gora{display:flex; justify-content:space-between; align-items:center;}
    .miasto-tag{display:inline-block; font-size:12px; font-weight:700; padding:3px 11px; border-radius:20px; color:#fff; background:var(--kolor);}
    .gwiazda{cursor:pointer; background:none; border:0; font-size:24px; line-height:1; color:#d2d7de; padding:0; transition:transform .15s;}
    .gwiazda:hover{transform:scale(1.15);}
    .gwiazda.akt{color:var(--zloto);}
    .cena{font-size:24px; font-weight:800; letter-spacing:-.5px; line-height:1.1;}
    .cena-m2{font-size:13px; color:var(--cien); margin-top:-6px;}
    .lokal{font-size:14px; color:var(--tekst); display:flex; gap:6px; align-items:flex-start;}
    .lokal .pin{color:var(--cien);}
    .chipy{display:flex; gap:7px; flex-wrap:wrap; margin-top:auto;}
    .chip{font-size:12px; background:#f1f4f8; color:#39414c; border-radius:8px; padding:5px 10px; font-weight:600;}
    .otworz{margin-top:6px; display:inline-block; text-align:center; text-decoration:none; font-weight:600; font-size:14px;
            color:#fff; background:var(--kolor); border-radius:10px; padding:10px; transition:opacity .15s;}
    .otworz:hover{opacity:.9;}
    .otworz.brak{background:#e4e8ee; color:var(--cien); pointer-events:none;}
    .puste{grid-column:1/-1; padding:50px; text-align:center; color:var(--cien); background:var(--panel); border-radius:16px; border:1px dashed var(--ramka);}
    @media (max-width:640px){ body{font-size:15px;} }
  </style>
</head>
<body>
  <header class="hero">
    <div class="inner">
      <h1>🏡 Domy na sprzedaż</h1>
      <p>Oferty z Otodom.pl — Wrocław, Gdańsk, Kraków (po 10 ofert). Dane wygenerowano: <span id="dataGen"></span>.</p>
    </div>
  </header>

  <div class="wrap">
    <div class="statki" id="statki"></div>

    <div class="panel-box">
      <h2>Średnia cena wg miasta (wg aktualnego filtra)</h2>
      <div class="wykres" id="wykres"></div>
    </div>

    <div class="panel-box">
      <h2>Filtry i wyszukiwanie</h2>
      <input type="text" class="szukaj" id="szukaj" placeholder="🔍 Szukaj po lokalizacji lub tytule (np. Krzyki, Wrzeszcz, dom z ogrodem)...">
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

    <div class="pasek-wynikow">
      <span class="licznik" id="licznik"></span>
      <span class="rozdziel"></span>
      <label for="sortuj" style="font-size:14px;color:var(--cien);">Sortuj:</label>
      <select class="sortuj" id="sortuj">
        <option value="cena|-1">Cena: od najwyższej</option>
        <option value="cena|1">Cena: od najniższej</option>
        <option value="powierzchnia_m2|-1">Powierzchnia: od największej</option>
        <option value="powierzchnia_m2|1">Powierzchnia: od najmniejszej</option>
        <option value="cena_za_m2|1">Cena za m²: od najniższej</option>
        <option value="cena_za_m2|-1">Cena za m²: od najwyższej</option>
      </select>
    </div>

    <div class="siatka" id="siatka"></div>
  </div>

  <script id="dane" type="application/json">__DANE__</script>
  <script>
  "use strict";
  const DANE = JSON.parse(document.getElementById('dane').textContent);
  const OFERTY = DANE.oferty;
  document.getElementById('dataGen').textContent = DANE.wygenerowano;

  const NAZWY = { Wroclaw:'Wrocław', Gdansk:'Gdańsk', Krakow:'Kraków' };
  const KOLORY = { Wroclaw:'var(--wroclaw)', Gdansk:'var(--gdansk)', Krakow:'var(--krakow)' };
  const KOLEJNOSC_MIAST = ['Wroclaw','Gdansk','Krakow'];

  const ceny = OFERTY.map(o => o.cena).filter(c => c != null);
  const powy = OFERTY.map(o => o.powierzchnia_m2).filter(p => p != null);
  const C_MIN = Math.floor(Math.min.apply(null, ceny));
  const C_MAX = Math.ceil(Math.max.apply(null, ceny));
  const P_MIN = Math.floor(Math.min.apply(null, powy));
  const P_MAX = Math.ceil(Math.max.apply(null, powy));

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
      return '<div class="slupek '+s.miasto+'"><div class="kwota">'+kwota+'</div>'
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

  function karta(o){
    const akt = stan.ulubione.has(o.id);
    const chipy = [];
    if(o.powierzchnia_m2!=null) chipy.push('<span class="chip">'+fmtLiczba(o.powierzchnia_m2)+' m²</span>');
    if(o.powierzchnia_dzialki_m2!=null) chipy.push('<span class="chip">działka '+fmtLiczba(o.powierzchnia_dzialki_m2)+' m²</span>');
    if(o.liczba_pokoi!=null) chipy.push('<span class="chip">'+o.liczba_pokoi+' pok.</span>');
    const m2 = o.cena_za_m2!=null ? (fmtLiczba(o.cena_za_m2)+' zł/m²') : '';
    const link = o.url
      ? '<a class="otworz" href="'+o.url+'" target="_blank" rel="noopener">Zobacz na Otodom ↗</a>'
      : '<span class="otworz brak">Brak linku</span>';
    return '<article class="karta" style="--kolor:'+KOLORY[o.miasto]+'">'
      + '<div class="pasek"></div>'
      + '<div class="karta-tresc">'
      +   '<div class="karta-gora"><span class="miasto-tag">'+NAZWY[o.miasto]+'</span>'
      +     '<button class="gwiazda'+(akt?' akt':'')+'" data-fav="'+o.id+'" title="Dodaj/usun z ulubionych">'+(akt?'★':'☆')+'</button></div>'
      +   '<div class="cena">'+fmtCena(o.cena)+'</div>'
      +   (m2 ? '<div class="cena-m2">'+m2+'</div>' : '')
      +   '<div class="lokal"><span class="pin">📍</span><span>'+(o.lokalizacja||'—')+'</span></div>'
      +   '<div class="chipy">'+chipy.join('')+'</div>'
      +   link
      + '</div></article>';
  }

  function rysujSiatke(w){
    const el = document.getElementById('siatka');
    document.getElementById('licznik').textContent = w.length + (w.length===1?' oferta':(w.length>=2&&w.length<=4?' oferty':' ofert'));
    if(!w.length){ el.innerHTML = '<div class="puste">Brak ofert spełniających kryteria. Zmień filtry albo kliknij „Wyczyść filtry".</div>'; return; }
    el.innerHTML = w.map(karta).join('');
    el.querySelectorAll('button[data-fav]').forEach(b => b.onclick = () => {
      const id = Number(b.dataset.fav);
      if(stan.ulubione.has(id)) stan.ulubione.delete(id); else stan.ulubione.add(id);
      zapiszUlub(); rysuj();
    });
  }

  function rysuj(){
    const w = widoczne();
    rysujFiltry(); rysujStatki(w); rysujWykres(w); rysujSiatke(w);
  }

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
  document.getElementById('sortuj').onchange = (e) => {
    const [kol,kier] = e.target.value.split('|');
    stan.sortKol = kol; stan.sortKier = Number(kier); rysuj();
  };
  ustawSuwaki(); aktTeksty(); rysuj();
  </script>
</body>
</html>
"""

with open(WYJSCIE, "w", encoding="utf-8") as f:
    f.write(HTML.replace("__DANE__", dane_json))

print(f"Wygenerowano {WYJSCIE} ({len(oferty)} ofert)")
