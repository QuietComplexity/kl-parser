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
    
    # --- PARSOWANIE ---
    current_bio_collecting = False
    
    for l in lines:
        l_s = l.strip()
        if not l_s: continue
        l_u = l_s.upper()
        
        # Wykrywanie BIO i zbieranie wszystkiego po nim
        if l_u.startswith("BIO:"):
            meta["AUTOR"] = l_s.replace("BIO:", "").strip()
            current_bio_collecting = True
            continue
        
        # Jeśli jesteśmy w trybie zbierania BIO i linia nie jest innym kluczem SEO
        if current_bio_collecting:
            if ":" in l_s and any(k in l_u for k in ["SEO:", "METAOPIS:", "TAGI:", "URL:", "SŁOWO KLUCZ:", "LEAD:"]):
                current_bio_collecting = False
            else:
                meta["BIO"] += (" " + l_s) if meta["BIO"] else l_s
                continue

        # Inne metadane
        if ":" in l_s and any(k in l_u for k in ["SEO:", "METAOPIS:", "TAGI:", "URL:", "SŁOWO KLUCZ:", "LEAD:"]):
            klucz, wartosc = l_s.split(":", 1)
            val = wartosc.strip()
            key_map = {"SEO": "TYTUL", "TYTUŁ": "TYTUL", "META": "META", "TAGI": "TAGI", "URL": "SLOWO", "SŁOWO": "SLOWO", "LEAD": "LEAD"}
            for k_word, target in key_map.items():
                if k_word in l_u: meta[target] = val
            continue

        # Pomijanie znaczników technicznych
        if l_u == "TEKST:" or l_s.startswith("==="): continue
        
        # Jeśli nie jest metadanymi ani BIO, trafia do treści artykułu
        content_lines.append(l_s)

    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        l_low = l.lower()
        
        # 1. OBRAZKI (Rygorystyczne: musi być tekst w [], nie cyfra, nie http)
        is_image = False
        if "[" in l and "]" in l:
            tag_match = re.search(r'\[(.*?)\]', l)
            if tag_match:
                tag_content = tag_match.group(1).strip()
                if not tag_content.isdigit() and not tag_content.startswith("http"):
                    is_image = True
                    tag_raw = tag_content.lower()
                    width = 550 if any(k in tag_raw for k in ["pion", "v", "sq", "kwadrat"]) else 675
                    tag_clean = usun_polskie_znaki(tag_raw).replace(" ", "_")
                    file_name = f"{author_code}_{tag_clean}{file_ext}"
                    html_body.append(f'<img class="alignnone wp-image-XXXX" src="{base_url + file_name}" alt="" width="{width}" height="auto" style="max-width: 100%; height: auto;" />')

        if not is_image:
            # 2. NAGŁÓWKI SEKCJI
            if l_low.startswith("przypisy") or l_low.startswith("książka"):
                html_body.append(f'<br />\n<b>{l}</b>')
            # 3. WYIMKI
            elif l.startswith(">") or l_low.startswith("wyimek:"):
                txt = l.lstrip("> ").strip() if l.startswith(">") else l.split(":", 1)[1].strip()
                html_body.append(f'<blockquote><span style="font-weight: 400;">"{uczyn_linki_klikalnymi(txt)}"</span></blockquote>')
            # 4. STOPKA
            elif "rubrykę redaguje" in l_low:
                html_body.append(f'\n<i><span style="font-weight: 400;">{l}</span></i>')
            # 5. ZWYKŁY TEKST I PRZYPISY NUMEROWANE
            else:
                html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(l)}</span>')

    full_html = (f'<b>{meta["LEAD"]}</b>\n\n' if meta["LEAD"] else "") + "\n\n".join(html_body) + f'\n\n<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />'

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_input("URL (Slug):", meta['SLOWO'])
        st.text_area("Metaopis:", meta['META'], height=80)
        st.divider()
        st.text_area("Kod HTML artykułu (BIO wycięte):", full_html, height=350)
        
        st.subheader("👤 Dane Autora")
        st.text_input("Imię i Nazwisko:", meta['AUTOR'])
        st.text_area("BIO (do wklejenia w profil):", meta['BIO'], height=100)