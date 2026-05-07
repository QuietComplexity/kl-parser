import streamlit as st
import re
from datetime import datetime

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(tekst):
    """Zamienia polskie litery na ich łacińskie odpowiedniki."""
    polskie_znaki = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return tekst.translate(polskie_znaki)

# --- KONFIGURACJA ---
URL_BANER = "https://kulturaliberalna.pl/wp-content/uploads/2025/06/Baner-strona-WWW-top-1080-x-50-1080-x-100-px.png"

st.set_page_config(page_title="KL Generator Linków", page_icon="🔗", layout="wide")

st.title("🔗 Panel Edytorski KL Dzieciom")
st.markdown("Skrypt automatycznie dobiera szerokość: **675px** dla poziomych i **550px**, jeśli w nawiasie wpiszesz 'pion' lub 'v'.")

# --- SIDEBAR: KONFIGURACJA SCHEMATU ---
with st.sidebar:
    st.header("📂 Ustawienia WordPress")
    now = datetime.now()
    year = st.text_input("Rok (YYYY):", value=str(now.year))
    month = st.text_input("Miesiąc (MM):", value=now.strftime("%m"))
    
    st.header("🖼️ Parametry Zdjęć")
    file_ext = st.selectbox("Format plików:", [".png", ".jpg", ".jpeg"], index=0)
    author_code = st.text_input("Kod autora (np. rybak):", value="").lower().strip()
    
    st.divider()
    st.subheader("Szerokości (px)")
    w_horizontal = st.number_input("Poziome:", value=675)
    w_vertical = st.number_input("Pion/Kwadrat:", value=550)
    
    st.info("Zasada: Jeśli tag zawiera słowo 'pion', 'v' lub 'sq', system użyje mniejszej szerokości.")

# --- GŁÓWNE OKNO ---
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("1. Wklej tekst artykułu")
    input_text = st.text_area("Wklej treść razem z metadanymi:", height=550)

if input_text:
    lines = input_text.splitlines()
    meta = {"LEAD": "", "TYTUL": "", "SLOWO": "", "META": "", "TAGI": "", "AUTOR": "", "BIO": ""}
    content_lines = []
    skip_next = False
    
    raw_lines = [l.strip() for l in lines if l.strip()]
    
    # --- PARSOWANIE METADANYCH ---
    for i, l in enumerate(raw_lines):
        if skip_next:
            skip_next = False
            continue
        l_u = l.upper()
        if ":" in l and any(k in l_u for k in ["SEO:", "TYTUŁ SEO:", "METAOPIS:", "TAGI:", "URL:", "SŁOWO KLUCZ:", "LEAD:", "AUTOR:"]):
            klucz, wartosc = l.split(":", 1)
            val = wartosc.strip()
            if "AUTOR" in l_u:
                meta["AUTOR"] = val
                if i+1 < len(raw_lines) and ":" not in raw_lines[i+1]:
                    meta["BIO"] = raw_lines[i+1]
                    skip_next = True
            else:
                key_map = {"SEO": "TYTUL", "TYTUŁ": "TYTUL", "META": "META", "TAGI": "TAGI", "URL": "SLOWO", "SŁOWO": "SLOWO", "LEAD": "LEAD"}
                for k_word, target in key_map.items():
                    if k_word in l_u: meta[target] = val
            continue
        if l_u == "TEKST:" or l.startswith("==="): continue
        content_lines.append(l)

    # --- GENEROWANIE HTML ---
    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        # Obsługa Obrazków
        if "[" in l and "]" in l:
            tag_raw = re.search(r'\[(.*?)\]', l).group(1).lower()
            
            # Wybór szerokości na podstawie słów kluczowych
            if any(k in tag_raw for k in ["pion", "v", "sq", "kwadrat"]):
                width = w_vertical
            else:
                width = w_horizontal
            
            # Czyszczenie nazwy pliku (brak polskich znaków, spacje -> _)
            tag_clean = usun_polskie_znaki(tag_raw).replace(" ", "_")
            file_name = f"{author_code}_{tag_clean}{file_ext}"
            
            full_img_url = base_url + file_name
            
            html_body.append(
                f'<img class="alignnone wp-image-XXXX" src="{full_img_url}" '
                f'alt="" width="{width}" height="auto" '
                f'style="max-width: 100%; height: auto;" />'
            )
        
        # Wyimki / Cytaty
        elif l.startswith(">") or l.lower().startswith("wyimek:"):
            txt = l.lstrip("> ").strip() if l.startswith(">") else l.split(":", 1)[1].strip()
            html_body.append(f'<blockquote><span style="font-weight: 400;">"{txt}"</span></blockquote>')
        
        # Przypisy i Książka
        elif l.lower().startswith(("przypisy:", "książka:")):
            html_body.append(f'\n<b>{l}</b>\n')
            
        # Stopka redakcyjna
        elif "Rubrykę redaguje" in l:
            html_body.append(f'\n<i><span style="font-weight: 400;">{l}</span></i>\n')
            
        # Zwykły akapit
        else:
            html_body.append(f'<span style="font-weight: 400;">{l}</span>')

    # Montaż końcowy
    final_html = [f'<b>{meta["LEAD"]}</b>'] + html_body + [f'<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />']

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_input("URL (Slug):", meta['SLOWO'])
        st.text_area("Metaopis:", meta['META'], height=80)
        
        st.divider()
        st.text_area("Kod HTML (Kopiuj do WP):", "\n\n".join(final_html), height=400)
        
        st.subheader("Autor & Bio")
        st.info(f"**{meta['AUTOR']}**\n\n{meta['BIO']}")

else:
    with col_out:
        st.info("Wklej tekst po lewej stronie, aby wygenerować kod.")