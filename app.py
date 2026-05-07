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
    lines = input_text.splitlines()
    meta = {"LEAD": "", "TYTUL": "", "SLOWO": "", "META": "", "TAGI": "", "AUTOR": "", "BIO": ""}
    content_lines = []
    skip_next = False
    
    raw_lines = [l.strip() for l in lines if l.strip()]
    
    for i, l in enumerate(raw_lines):
        if skip_next:
            skip_next = False
            continue
        l_u = l.upper()
        # Wyłapywanie metadanych
        if ":" in l and any(k in l_u for k in ["SEO:", "TYTUŁ SEO:", "METAOPIS:", "TAGI:", "URL:", "SŁOWO KLUCZ:", "LEAD:", "AUTOR:"]):
            klucz, wartosc = l.split(":", 1)
            val = wartosc.strip()
            if "AUTOR" in l_u:
                meta["AUTOR"] = val
                # Jeśli następna linia nie ma dwukropka, uznajemy ją za BIO
                if i+1 < len(raw_lines) and ":" not in raw_lines[i+1]:
                    meta["BIO"] = raw_lines[i+1]
                    skip_next = True
            else:
                key_map = {"SEO": "TYTUL", "TYTUŁ": "TYTUL", "META": "META", "TAGI": "TAGI", "URL": "SLOWO", "SŁOWO": "SLOWO", "LEAD": "LEAD"}
                for k_word, target in key_map.items():
                    if k_word in l_u: meta[target] = val
            continue
        
        # Jeśli linia zaczyna się od BIO: (dosłownie), też ją wycinamy
        if l_u.startswith("BIO:"):
            meta["BIO"] = l.split(":", 1)[1].strip()
            continue
            
        if l_u == "TEKST:" or l.startswith("==="): continue
        content_lines.append(l)

    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        l_strip = l.strip()
        l_low = l_strip.lower()
        
        # --- LOGIKA OBRAZKÓW (Bardziej precyzyjna) ---
        is_image = False
        tag_content = ""
        if "[" in l_strip and "]" in l_strip:
            match = re.search(r'\[(.*?)\]', l_strip)
            if match:
                tag_content = match.group(1).strip()
                # OBRAZEK: jeśli nie jest samym numerem i nie zaczyna się od http
                if not tag_content.isdigit() and not tag_content.startswith("http"):
                    is_image = True

        if is_image:
            width = 550 if any(k in tag_content.lower() for k in ["pion", "v", "sq", "kwadrat"]) else 675
            tag_clean = usun_polskie_znaki(tag_content.lower()).replace(" ", "_")
            file_name = f"{author_code}_{tag_clean}{file_ext}"
            html_body.append(f'<img class="alignnone wp-image-XXXX" src="{base_url + file_name}" alt="" width="{width}" height="auto" style="max-width: 100%; height: auto;" />')
        
        # --- RESZTA TEKSTU ---
        elif l_low.startswith("przypisy") or l_low.startswith("książka"):
            html_body.append(f'<br />\n<b>{l_strip}</b>')
        elif l_strip.startswith(">") or l_low.startswith("wyimek:"):
            txt = l_strip.lstrip("> ").strip() if l_strip.startswith(">") else l_strip.split(":", 1)[1].strip()
            html_body.append(f'<blockquote><span style="font-weight: 400;">"{uczyn_linki_klikalnymi(txt)}"</span></blockquote>')
        elif "rubrykę redaguje" in l_low:
            html_body.append(f'\n<i><span style="font-weight: 400;">{l_strip}</span></i>')
        else:
            # Tutaj lądują przypisy [1], [2] i zwykły tekst - z klikalnymi linkami
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(l_strip)}</span>')

    # Składanie finalnego kodu (bez BIO i Autora)
    full_html = (f'<b>{meta["LEAD"]}</b>\n\n' if meta["LEAD"] else "") + "\n\n".join(html_body) + f'\n\n<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />'

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_input("URL (Slug):", meta['SLOWO'])
        st.text_area("Metaopis:", meta['META'], height=80)
        st.divider()
        st.text_area("Kod HTML artykułu:", full_html, height=350)
        
        # --- NOWA SEKCJA NA BIO I AUTORA ---
        st.subheader("👤 Dane Autora (do stopki WP)")
        st.text_input("Imię i Nazwisko:", meta['AUTOR'])
        st.text_area("BIO autora:", meta['BIO'], height=100)