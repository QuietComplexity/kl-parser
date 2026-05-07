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
    lines = [l.strip() for l in input_text.splitlines() if l.strip()]
    meta = {"LEAD": "", "TYTUL": "", "SLOWO": "", "META": "", "TAGI": "", "AUTOR": "", "BIO": ""}
    content_lines = []
    
    # --- PARSOWANIE METADANYCH I BIO ---
    current_bio_collecting = False
    
    for l in lines:
        l_u = l.upper()
        
        # BIO
        if l_u.startswith("BIO:"):
            meta["AUTOR"] = l.replace("BIO:", "").strip()
            current_bio_collecting = True
            continue
        
        if current_bio_collecting:
            if ":" in l and any(k in l_u for k in ["SEO:", "METAOPIS:", "TAGI:", "URL:", "SŁOWO:", "LEAD:"]):
                current_bio_collecting = False
            else:
                meta["BIO"] += (" " + l) if meta["BIO"] else l
                continue

        # Inne klucze (w tym SŁOWO KLUCZOWE)
        if ":" in l and any(k in l_u for k in ["SEO", "META", "TAGI", "URL", "SŁOWO", "LEAD", "AUTOR"]):
            klucz, wartosc = l.split(":", 1)
            val = wartosc.strip()
            k_upper = klucz.upper()
            if "SEO" in k_upper or "TYTUŁ" in k_upper: meta["TYTUL"] = val
            elif "META" in k_upper: meta["META"] = val
            elif "TAGI" in k_upper: meta["TAGI"] = val
            elif "URL" in k_upper or "SŁOWO" in k_upper: meta["SLOWO"] = val
            elif "LEAD" in k_upper: meta["LEAD"] = val
            elif "AUTOR" in k_upper: meta["AUTOR"] = val
            continue

        if l_u == "TEKST:" or l.startswith("==="): continue
        
        # Dodajemy do treści tylko to, co nie jest Lead'em ani Słowem Kluczowym
        if l != meta["LEAD"] and l != meta["SLOWO"]:
            content_lines.append(l)

    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in content_lines:
        l_low = l.lower()
        
        # --- LOGIKA OBRAZKÓW ---
        is_image = False
        if "[" in l and "]" in l:
            tag_match = re.search(r'\[(.*?)\]', l)
            if tag_match:
                tag_content = tag_match.group(1).strip()
                # Jeśli tag zawiera litery i nie jest linkiem
                if any(c.isalpha() for c in tag_content) and not tag_content.startswith("http"):
                    is_image = True
                    tag_clean = usun_polskie_znaki(tag_content.lower()).replace(" ", "_")
                    # Rozmiar: okladka zawsze 550, reszta wg słów kluczowych
                    if "okladka" in tag_clean or any(k in tag_clean for k in ["pion", "v", "sq", "kwadrat"]):
                        width = 550
                    else:
                        width = 675
                    
                    file_name = f"{author_code}_{tag_clean}{file_ext}"
                    html_body.append(f'<img class="alignnone wp-image-XXXX" src="{base_url + file_name}" alt="" width="{width}" height="auto" style="max-width: 100%; height: auto;" />')

        if not is_image:
            if l_low.startswith("przypisy") or l_low.startswith("książka"):
                html_body.append(f'<br />\n<b>{l}</b>')
            elif l.startswith(">") or l_low.startswith("wyimek:"):
                txt = l.lstrip("> ").strip() if l.startswith(">") else l.split(":", 1)[1].strip()
                html_body.append(f'<blockquote><span style="font-weight: 400;">"{uczyn_linki_klikalnymi(txt)}"</span></blockquote>')
            elif "rubrykę redaguje" in l_low:
                html_body.append(f'\n<i><span style="font-weight: 400;">{l}</span></i>')
            else:
                html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(l)}</span>')

    # Składanie finalnego kodu
    final_lead = f'<b>{meta["LEAD"]}</b>\n\n' if meta["LEAD"] else ""
    full_html = final_lead + "\n\n".join(html_body) + f'\n\n<img class="alignnone wp-image-105887 size-full" src="{URL_BANER}" alt="" width="1080" height="100" />'

    with col_out:
        st.subheader("2. Gotowy kod i SEO")
        st.text_input("Tytuł SEO:", meta['TYTUL'])
        st.text_input("URL (Slug):", meta['SLOWO'])
        st.text_area("Metaopis:", meta['META'], height=80)
        st.divider()
        st.text_area("Kod HTML artykułu:", full_html, height=400)
        
        st.subheader("👤 Dane Autora")
        st.text_input("Imię i Nazwisko:", meta['AUTOR'])
        st.text_area("BIO (do profilu):", meta['BIO'], height=100)