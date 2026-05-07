import streamlit as st
import re
from datetime import datetime

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(tekst):
    polskie_znaki = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return tekst.translate(polskie_znaki)

def uczyn_linki_klikalnymi(tekst):
    """Zamienia adresy URL na linki HTML, ignorując nawiasy kwadratowe wokół nich."""
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
        if skip_next: skip_next = False; continue
        l_u = l.upper()
        if ":" in l and any(k in l_u for k in ["SEO:", "TYTUŁ SEO:", "METAOPIS:", "TAGI:", "URL:", "SŁOWO KLUCZ:", "LEAD:", "AUTOR:"]):
            klucz, wartosc = l.split(":", 1)
            val = wartosc.strip()
            if "AUTOR" in l_u:
                meta["AUTOR"] = val
                if i+1 < len(raw_lines) and ":" not in raw_lines[i+1]:
                    meta["BIO"] = raw_lines[i+1]; skip_next = True
            else:
                key_map = {"SEO": "TYTUL", "TYTUŁ": "TYTUL", "META": "META", "TAGI": "TAGI", "URL": "SLOWO", "SŁOWO": "SLOWO", "LEAD": "LEAD"}
                for k_word, target in key_map.items():
                    if k_word in l_u: meta[target] = val
            continue
        if l_u == "TEKST:" or l.startswith("==="): continue
        content_lines.append(l)

    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        l_strip = l.strip()
        l_low = l_strip.lower()
        
        # 1. SPRAWDZANIE CZY TO OBRAZEK (Tylko jeśli to nie jest przypis [1] ani link [http])
        is_image_tag = False
        if "[" in l_strip and "]" in l_strip:
            # Wyciągamy zawartość nawiasu
            potential_tag = re.search(r'\[(.*?)\]', l_strip).group(1)
            # Jeśli to NIE jest cyfra i NIE zaczyna się od http, to uznajemy, że to obrazek
            if not potential_tag.isdigit() and not potential_tag.startswith("http"):
                is_image_tag = True

        if is_image_tag:
            tag_raw = re.search(r'\[(.*?)\]', l_strip).group(1).lower()
            width = 550 if any(k in tag_raw for k in ["pion", "v", "sq", "kwadrat"]) else 675
            tag_clean = usun_polskie_znaki(tag_raw).replace(" ", "_")
            file_name = f"{author_code}_{tag_clean}{file_ext}"
            html_body.append(f'<img class="alignnone wp-image-XXXX" src="{base_url + file_name}" alt="" width="{width}" height="auto" style="max-width: 100%; height: auto;" />')
        
        # 2. NAGŁÓWKI (Przypisy / Książka)
        elif l_low.startswith("przypisy") or l_low.startswith("książka"):
            html_body.append(f'<br />\n<b>{l_strip}</b>')
        
        # 3. WYIMKI
        elif l_strip.startswith(">") or l_low.startswith("wyimek:"):
            txt = l_strip.lstrip("> ").strip() if l_strip.startswith(">") else l_strip.split(":", 1)[1].strip()
            txt = uczyn_linki_klikalnymi(txt)
            html_body.append(f'<blockquote><span style="font-weight: 400;">"{txt}"</span></blockquote>')
            
        # 4. ZWYKŁY TEKST (W tym przypisy [1] i [2] z linkami)
        else:
            tekst_finalny = uczyn_linki_klikalnymi(l_strip)
            html_body.append(f'<span style="font-weight: 400;">{tekst_finalny}</span>')

    full_html = (f'<b>{meta["LEAD"]}</b>\n\n' if meta["LEAD"] else "") + "\n\n".join(html_body) + f'\n\n<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />'

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_input("URL (Slug):", meta['SLOWO'])
        st.text_area("Metaopis:", meta['META'], height=80)
        st.divider()
        st.text_area("Kod HTML:", full_html, height=450)
        st.info(f"Autor: **{meta['AUTOR']}**")