import streamlit as st
import re
from datetime import datetime

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(tekst):
    polskie_znaki = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return tekst.translate(polskie_znaki)

def uczyn_linki_klikalnymi(tekst):
    wzor_url = r'(https?://[^\s\]]+)'
    return re.sub(wzor_url, r'<a href="\1" target="_blank">\1</a>', tekst)

# --- KONFIGURACJA ---
URL_BANER = "https://kulturaliberalna.pl/wp-content/uploads/2025/06/Baner-strona-WWW-top-1080-x-50-1080-x-100-px.png"

st.set_page_config(page_title="KL Generator", page_icon="🔗", layout="wide")

if st.sidebar.button("🗑️ Wyczyść wszystko"):
    st.rerun()

st.title("🔗 Panel Edytorski KL Dzieciom")

with st.sidebar:
    st.header("📂 Parametry WordPress")
    now = datetime.now()
    year = st.text_input("Rok (YYYY):", value=str(now.year))
    month = st.text_input("Miesiąc (MM):", value=now.strftime("%m"))
    st.header("🖼️ Ustawienia Zdjęć")
    file_ext = st.selectbox("Format plików:", [".jpg", ".jpeg", ".png"], index=0)
    author_code = st.text_input("Kod autora (np. rybak):", value="").lower().strip()

# --- GŁÓWNE OKNO ---
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("1. Wklej tekst")
    input_text = st.text_area("Wklej treść:", height=550, key="main_input")

if input_text:
    # 1. Wstępne czyszczenie i podział na linie
    raw_lines = [l.strip() for l in input_text.splitlines() if l.strip()]
    
    meta = {"LEAD": "", "TYTUL": "", "SLOWO": "", "META": "", "TAGI": "", "AUTOR": "", "BIO": ""}
    content_lines = []
    
    # 2. PARSOWANIE - Wyciągamy metadane i BIO, reszta to treść
    collecting_bio = False
    
    for l in raw_lines:
        l_u = l.upper()
        
        # Wykrywanie kluczy (SEO, Lead itp.)
        if ":" in l:
            klucz = l.split(":", 1)[0].upper()
            wartosc = l.split(":", 1)[1].strip()
            
            if "LEAD" in klucz: meta["LEAD"] = wartosc; continue
            if "SEO" in klucz or "TYTUŁ" in klucz: meta["TYTUL"] = wartosc; continue
            if "META" in klucz: meta["META"] = wartosc; continue
            if "TAGI" in klucz: meta["TAGI"] = wartosc; continue
            if "URL" in klucz or "SŁOWO" in klucz: meta["SLOWO"] = wartosc; continue
            if "AUTOR" in klucz and not collecting_bio: meta["AUTOR"] = wartosc; continue
            
        # Specyficzna obsługa BIO
        if l_u.startswith("BIO:"):
            meta["AUTOR"] = l.replace("BIO:", "").strip()
            collecting_bio = True
            continue
            
        if collecting_bio:
            # BIO zbieramy do momentu napotkania innego pola technicznego
            if ":" in l and any(k in l_u for k in ["SEO", "URL", "TAGI", "META"]):
                collecting_bio = False
            else:
                meta["BIO"] += (" " + l) if meta["BIO"] else l
                continue

        # Jeśli to nie metadane ani BIO -> to jest treść artykułu
        if l_u not in ["TEKST:", "==="]:
            # DODATKOWY FILTR: Nie dodawaj linii, jeśli jest identyczna z Lead'em (unikamy 2x Lead)
            if l != meta["LEAD"]:
                content_lines.append(l)

    # 3. GENEROWANIE HTML
    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        l_low = l.lower()
        
        # --- LOGIKA OBRAZKÓW ---
        if "[" in l and "]" in l and not l.startswith("[http"):
            tag_match = re.search(r'\[(.*?)\]', l)
            if tag_match:
                tag_content = tag_match.group(1).strip()
                # Jeśli to nie jest sam numer przypisu
                if not tag_content.isdigit():
                    tag_clean = usun_polskie_znaki(tag_content.lower()).replace(" ", "_")
                    # Szerokość: okladka 550, reszta 675
                    w = 550 if "okladka" in tag_clean or any(k in tag_clean for k in ["pion", "v", "sq", "kwadrat"]) else 675
                    f_name = f"{author_code}_{tag_clean}{file_ext}"
                    html_body.append(f'<img class="alignnone wp-image-XXXX" src="{base_url + f_name}" alt="" width="{w}" height="auto" style="max-width: 100%; height: auto;" />')
                    continue # Przejdź do następnej linii, nie dodawaj tego jako tekst

        # --- LOGIKA TEKSTU ---
        if l_low.startswith("przypisy") or l_low.startswith("książka"):
            html_body.append(f'<br />\n<b>{l}</b>')
        elif l.startswith(">") or l_low.startswith("wyimek:"):
            txt = l.lstrip("> ").strip() if l.startswith(">") else l.split(":", 1)[1].strip()
            html_body.append(f'<blockquote><span style="font-weight: 400;">"{uczyn_linki_klikalnymi(txt)}"</span></blockquote>')
        elif "rubrykę redaguje" in l_low:
            html_body.append(f'\n<i><span style="font-weight: 400;">{l}</span></i>')
        else:
            # Zwykły akapit (w tym przypisy [1]) - BEZ boldowania
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(l)}</span>')

    # Składanie całości
    final_lead = f'<b>{meta["LEAD"]}</b>\n\n' if meta["LEAD"] else ""
    full_html = final_lead + "\n\n".join(html_body) + f'\n\n<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />'

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_input("URL (Slug):", meta['SLOWO'])
        st.text_area("Metaopis:", meta['META'], height=80)
        st.divider()
        st.text_area("Kod HTML artykułu:", full_html, height=450)
        
        st.subheader("👤 Dane Autora")
        st.info(f"Autor: **{meta['AUTOR']}**")
        st.text_area("BIO do profilu:", meta['BIO'], height=100)