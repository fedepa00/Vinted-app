import streamlit as st
import pandas as pd
import zipfile
import io
import os
import base64
import json
from openai import OpenAI

# Configurazione Pagina Mobile
st.set_page_config(page_title="Vinted AI Suite", page_icon="🛍️", layout="wide")

# CSS Personalizzato stile App moderna
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        background-color: #00a6a6;
        color: white;
        border: none;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛍️ Vinted AI Suite")
st.caption("Analizza lotti di articoli, crea schede perfette ed esporta in Excel.")

# Sidebar per la API Key
st.sidebar.header("🔑 Configurazione")
api_key = st.sidebar.text_input("Inserisci OpenAI API Key", type="password")

def analyze_article(folder_name, images_bytes_list, client):
    content_payload = [
        {
            "type": "text",
            "text": (
                "Sei un esperto di vendite su Vinted Italia.\n"
                "Analizza queste foto (fino a 20) dello stesso articolo.\n"
                "Rispondi SOLO ed ESCLUSIVAMENTE con un oggetto JSON valido con queste chiavi esatte:\n"
                "{\n"
                '  "titolo": "Titolo ottimizzato Vinted (max 60 car)",\n'
                '  "brand": "Marca o Sconosciuta",\n'
                '  "taglia": "Taglia o visibile",\n'
                '  "condizione": "Nuovo con cartellino / Ottime / Buone",\n'
                '  "descrizione": "Descrizione dettagliata con dettagli, vestibilità ed eventuali difetti",\n'
                '  "hashtag": "#vinted #marca #categoria"\n'
                "}"
            )
        }
    ]
    
    for img_bytes in images_bytes_list[:20]:
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        content_payload.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                "detail": "low"
            }
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content_payload}],
        response_format={"type": "json_object"},
        max_tokens=600
    )
    return json.loads(response.choices[0].message.content)

# File Uploader per file ZIP
uploaded_zip = st.file_uploader("📂 Carica archivio .ZIP con le cartelle articoli", type=["zip"])

if "results" not in st.session_state:
    st.session_state.results = []

if uploaded_zip and api_key:
    if st.button("🚀 Avvia Analisi Batch All-in-One"):
        client = OpenAI(api_key=api_key)
        st.session_state.results = []
        
        with zipfile.ZipFile(uploaded_zip, 'r') as z:
            folder_files = {}
            for filename in z.namelist():
                if not filename.endswith('/') and not filename.startswith('__MACOSX'):
                    parts = filename.split('/')
                    if len(parts) > 1:
                        folder_name = parts[0]
                        if folder_name not in folder_files:
                            folder_files[folder_name] = []
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                            folder_files[folder_name].append(filename)

            progress_bar = st.progress(0)
            status_text = st.empty()
            total = len(folder_files)
            
            for idx, (folder_name, file_list) in enumerate(folder_files.items()):
                status_text.text(f"⏳ Analizzando {idx+1}/{total}: {folder_name}")
                images_bytes = [z.read(fname) for fname in file_list]
                
                try:
                    res = analyze_article(folder_name, images_bytes, client)
                    res["folder"] = folder_name
                    res["num_foto"] = len(images_bytes)
                    st.session_state.results.append(res)
                except Exception as e:
                    st.error(f"Errore su {folder_name}: {e}")
                
                progress_bar.progress((idx + 1) / total)
                
            status_text.success("🎉 Analisi Completata!")

# Visualizzazione Schede Stile App
if st.session_state.results:
    st.write("---")
    st.subheader(f"📦 Articoli Elaborati ({len(st.session_state.results)})")
    
    # Download Excel
    df = pd.DataFrame(st.session_state.results)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Vinted')
        
    st.download_button(
        label="📥 Scarica Report Completo Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="articoli_vinted.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Rendering Card per ciascun articolo
    for item in st.session_state.results:
        with st.container():
            st.markdown(f"### 🏷️ {item['titolo']}")
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Brand:** {item['brand']}")
            col2.write(f"**Taglia:** {item['taglia']}")
            col3.write(f"**Condizioni:** {item['condizione']}")
            
            st.text_area("Descrizione + Hashtag", f"{item['descrizione']}\n\n{item['hashtag']}", height=120, key=item['folder'])
            st.write("---")
