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
    text_content = []
    
    collecting_bio = False
    
    # 1. PARSOWANIE (Metadane i BIO)
    for l in lines:
        l_u = l.upper()
        
        # Wykrywanie kluczy technicznych
        if ":" in l and any(k in l_u for k in ["SEO", "TYTUŁ SEO", "METAOPIS", "TAGI", "URL", "SŁOWO KLUCZOWE", "LEAD"]):
            collecting_bio = False 
            klucz, wartosc = l.split(":", 1)
            k = klucz.upper()
            v = wartosc.strip()
            
            if "LEAD" in k: meta["LEAD"] = v
            elif "SEO" in k or "TYTUŁ" in k: meta["TYTUL"] = v
            elif "META" in k: meta["META"] = v
            elif "TAGI" in k: meta["TAGI"] = v
            elif "URL" in k or "SŁOWO" in k: meta["SLOWO"] = v
            continue

        if l_u.startswith("BIO:"):
            meta["AUTOR"] = l.replace("BIO:", "").strip()
            collecting_bio = True
            continue

        if collecting_bio:
            meta["BIO"] += ("\n" + l) if meta["BIO"] else l
            continue

        # Treść artykułu - POMIJAMY linie identyczne z zapisanym LEAD
        if l_u not in ["TEKST:", "==="] and not l_u.startswith("AUTOR:"):
            # Radykalne porównanie, aby uniknąć dublowania leada
            if l != meta["LEAD"]:
                text_content.append(l)

    # 2. BUDOWANIE HTML
    html_body = []
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

    for l in text_content:
        l_low = l.lower()
        
        # --- LOGIKA OBRAZKÓW (obsługuje [ilustracja0] jako okładkę) ---
        if "[" in l and "]" in l and not l.startswith("[http"):
            tag_match = re.search(r'\[(.*?)\]', l)
            if tag_match:
                tag_content = tag_match.group(1).strip()
                if any(c.isalpha() for c in tag_content) or "0" in tag_content:
                    tag_clean = usun_polskie_znaki(tag_content.lower()).replace(" ", "_")
                    
                    # Szerokość 550px dla okładki, ilustracji0 i pionów
                    if any(k in tag_clean for k in ["okladka", "ilustracja0", "pion", "v", "sq", "kwadrat"]):
                        w = 550
                    else:
                        w = 675
                    
                    f_name = f"{author_code}_{tag_clean}{file_ext}"
                    html_body.append(f'<img class="alignnone wp-image-XXXX" src="{base_url + f_name}" alt="" width="{w}" height="auto" style="max-width: 100%; height: auto;" />')
                    continue

        # --- TEKST ---
        if l_low.startswith("przypisy") or l_low.startswith("książka"):
            html_body.append(f'<br />\n<b>{l}</b>')
        elif l.startswith(">") or l_low.startswith("wyimek:"):
            txt = l.lstrip("> ").strip() if l.startswith(">") else l.split(":", 1)[1].strip()
            html_body.append(f'<blockquote><span style="font-weight: 400;">"{uczyn_linki_klikalnymi(txt)}"</span></blockquote>')
        elif "rubrykę redaguje" in l_low:
            html_body.append(f'\n<i><span style="font-weight: 400;">{l}</span></i>')
        else:
            # Standardowy tekst bez boldowania
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(l)}</span>')

    # 3. WYNIK FINALNY
    # Lead boldowany tylko raz na samej górze
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
        st.info(f"Imię i Nazwisko: **{meta['AUTOR']}**")
        st.text_area("BIO (zachowane entery):", meta['BIO'], height=150)