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

st.title("🔗 Generator HTML (Obsługa PNG i JPG)")

# --- SIDEBAR: USTALANIE SCHEMATU LINKÓW ---
with st.sidebar:
    st.header("📂 Schemat Uploadu WP")
    now = datetime.now()
    year = st.text_input("Rok (YYYY):", value=str(now.year))
    month = st.text_input("Miesiąc (MM):", value=now.strftime("%m"))
    
    st.header("🖼️ Ustawienia Obrazków")
    # NOWOŚĆ: Wybór rozszerzenia pliku
    file_ext = st.selectbox("Rozszerzenie plików:", [".png", ".jpg", ".jpeg"], index=0)
    
    author_code = st.text_input("Kod autora:", value="rybak").lower().strip()
    img_w = st.number_input("Szerokość (px):", value=675)
    img_h = st.number_input("Wysokość (px):", value=380)
    
    st.divider()
    st.write("**Podgląd nazwy pliku:**")
    # System pokaże np. rybak_okladka.jpg
    st.code(f"{author_code}_okladka{file_ext}")

# --- GŁÓWNE OKNO ---
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("1. Wklej tekst")
    input_text = st.text_area("Wklej treść artykułu:", height=500)

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

    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        # Obsługa obrazków z czyszczeniem znaków i wybranym rozszerzeniem
        if "[" in l and "]" in l:
            tag_raw = re.search(r'\[(.*?)\]', l).group(1).lower()
            # Usuwamy polskie litery i spacje z tagu
            tag = usun_polskie_znaki(tag_raw).replace(" ", "_")
            
            file_name = f"{author_code}_{tag}{file_ext}"
            full_img_url = base_url + file_name
            html_body.append(f'<img class="alignnone wp-image-XXXX" src="{full_img_url}" alt="" width="{img_w}" height="{img_h}" />')
        
        elif l.startswith(">") or l.lower().startswith("wyimek:"):
            txt = l.lstrip("> ").strip() if l.startswith(">") else l.split(":", 1)[1].strip()
            html_body.append(f'<blockquote><span style="font-weight: 400;">"{txt}"</span></blockquote>')
        
        elif l.lower().startswith(("przypisy:", "książka:")):
            html_body.append(f'\n<b>{l}</b>\n')
            
        elif "Rubrykę redaguje" in l:
            html_body.append(f'\n<i><span style="font-weight: 400;">{l}</span></i>\n')
            
        else:
            html_body.append(f'<span style="font-weight: 400;">{l}</span>')

    final_html = [f'<b>{meta["LEAD"]}</b>'] + html_body + [f'<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />']

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_area("Metaopis:", meta['META'], height=80)
        
        st.divider()
        st.text_area("Kod HTML (Wklej do WP):", "\n\n".join(final_html), height=350)