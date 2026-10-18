import streamlit as st
import pandas as pd
import io
import json
import google.generativeai as genai
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="Vinted AI Studio", page_icon="🛍️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #fcfaf7; }
    .stButton>button {
        width: 100%;
        border-radius: 14px;
        font-weight: 600;
        background-color: #d99b82;
        color: white;
        border: none;
        padding: 12px;
        font-size: 16px;
    }
    .stDownloadButton>button {
        width: 100%;
        border-radius: 14px;
        font-weight: 600;
        background-color: #2c2c2c;
        color: white;
        border: none;
        padding: 12px;
    }
    </style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "nuova"
if "archivio" not in st.session_state:
    st.session_state.archivio = []
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None

col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("➕ Nuova"):
        st.session_state.page = "nuova"
        st.rerun()
with col_nav2:
    if st.button(f"📦 Archivio ({len(st.session_state.archivio)})"):
        st.session_state.page = "archivio"
        st.rerun()
with col_nav3:
    if st.session_state.archivio:
        df_exp = pd.DataFrame(st.session_state.archivio)
        b_exp = io.BytesIO()
        df_exp.to_excel(b_exp, index=False)
        st.download_button("📥 Esporta", data=b_exp.getvalue(), file_name="vinted_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.sidebar.header("🔑 Configurazione API")
api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

def analyze_item_fast(images_list, api_key):
    genai.configure(api_key=api_key)
    
    # Lista di modelli da provare in sequenza se uno fallisce o esaurisce la quota
    modelli_da_provare = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision']
    
    prompt = (
        "Sei un esperto venditore su Vinted Italia.\n"
        "Analizza queste foto dell'articolo e restituisci SOLO un oggetto JSON con queste esatte chiavi:\n"
        "{\n"
        '  "titolo": "Titolo commerciale chiaro (max 60 car)",\n'
        '  "brand": "Marca visibile o Sconosciuta",\n'
        '  "taglia": "Taglia rilevata",\n'
        '  "condizione": "Ottime condizioni / Nuovo / ecc",\n'
        '  "descrizione": "Descrizione dettagliata con vestibilità e dettagli",\n'
        '  "misure": "Lunghezza e larghezza torace stimate o visibili",\n'
        '  "hashtag": "#vinted #marca #categoria #stile"\n'
        "}"
    )
    
    content = [prompt]
    for img in images_list[:20]:
        content.append(Image.open(img))
        
    last_error = None
    for nome_modello in modelli_da_provare:
        try:
            model = genai.GenerativeModel(nome_modello)
            response = model.generate_content(content)
            txt = response.text.strip()
            if txt.startswith("```json"): txt = txt[7:]
            if txt.endswith("```"): txt = txt[:-3]
            return json.loads(txt.strip())
        except Exception as e:
            last_error = e
            continue
            
    raise Exception(f"Tutti i modelli hanno riscontrato un errore (ultimo: {last_error})")

if st.session_state.page == "nuova":
    st.markdown("# Nuova *analisi*")
    st.caption(f"Analizzati oggi: {len(st.session_state.archivio)}")
    
    st.markdown("### ARTICOLO 1")
    uploaded_files = st.file_uploader("Carica dalla galleria o trascina qui", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="uploader_main")
    
    if uploaded_files:
        st.success(f"📸 {len(uploaded_files)} foto caricate correttamente.")
        
        cols_prev = st.columns(min(len(uploaded_files), 4))
        for i, img_file in enumerate(uploaded_files[:4]):
            with cols_prev[i]:
                st.image(img_file, use_column_width=True)

        if st.button("✨ Avvia analisi"):
            if not api_key:
                st.error("Inserisci la chiave API di Google Gemini nella barra laterale!")
            else:
                with st.spinner("Analisi rapida in corso..."):
                    try:
                        res = analyze_item_fast(uploaded_files, api_key)
                        res["data"] = datetime.now().strftime("%d ott %Y")
                        res["foto_files"] = uploaded_files
                        st.session_state.archivio.insert(0, res)
                        st.session_state.selected_item = res
                        st.session_state.page = "dettaglio"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore durante l'analisi: {e}")

elif st.session_state.page == "archivio":
    st.markdown("# Archivio")
    st.caption(f"Totale articoli salvati: {len(st.session_state.archivio)}")
    
    search_query = st.text_input("🔍 Cerca titolo, descrizione, hashtag...")
    
    filtered_items = [
        item for item in st.session_state.archivio 
        if search_query.lower() in item['titolo'].lower() or search_query.lower() in item['descrizione'].lower()
    ] if search_query else st.session_state.archivio

    if not filtered_items:
        st.info("Nessun articolo trovato nell'archivio.")
    
    for idx, item in enumerate(filtered_items):
        with st.container():
            st.markdown(f"""
                <div style="padding: 15px; border-radius: 12px; border: 1px solid #e5dfd5; margin-bottom: 10px; background: white;">
                    <h4>{item['titolo']}</h4>
                    <p style="color: gray; font-size: 13px; margin: 0;">📅 {item['data']} &nbsp;|&nbsp; Brand: {item['brand']} &nbsp;|&nbsp; Taglia: {item['taglia']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Apri scheda #{len(filtered_items)-idx}", key=f"open_{idx}"):
                st.session_state.selected_item = item
                st.session_state.page = "dettaglio"
                st.rerun()

elif st.session_state.page == "dettaglio" and st.session_state.selected_item:
    item = st.session_state.selected_item
    
    if st.button("← Torna indietro"):
        st.session_state.page = "archivio"
        st.rerun()
        
    st.markdown(f"## {item['titolo']}")
    
    if "foto_files" in item and item["foto_files"]:
        cols_d = st.columns(min(len(item["foto_files"]), 3))
        for i, img_f in enumerate(item["foto_files"][:3]):
            with cols_d[i]:
                st.image(img_f, use_column_width=True)

    st.markdown("### TITOLO")
    st.info(item['titolo'])
    
    st.markdown("### DESCRIZIONE")
    st.success(item['descrizione'])
    
    st.markdown("### MISURE")
    st.warning(item['misure'])
    
    st.markdown("### HASHTAG")
    st.code(item['hashtag'])
    
    if st.button("🗑️ Elimina articolo"):
        st.session_state.archivio.remove(item)
        st.session_state.page = "archivio"
        st.rerun()
