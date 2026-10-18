import streamlit as st
import pandas as pd
import io
import json
import google.generativeai as genai
from PIL import Image

# Configurazione Pagina Mobile
st.set_page_config(page_title="Vinted AI Assistant (Free)", page_icon="🛍️", layout="wide")

# CSS Personalizzato stile App Mobile
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
        padding: 12px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛍️ Vinted AI Assistant (100% Gratuito)")
st.caption("Seleziona fino a 20 foto dalla galleria. Powered by Google Gemini.")

# Sidebar per la API Key di Google
st.sidebar.header("🔑 Configurazione")
api_key = st.sidebar.text_input("Inserisci Google Gemini API Key", type="password")

if "articoli" not in st.session_state:
    st.session_state.articoli = []

def analyze_with_gemini(images_list, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = (
        "Sei un esperto di vendite su Vinted Italia.\n"
        "Analizza queste foto (fino a 20) dello stesso articolo di abbigliamento/accessorio.\n"
        "Rispondi ESCLUSIVAMENTE con un oggetto JSON valido con queste chiavi esatte:\n"
        "{\n"
        '  "titolo": "Titolo d\'impatto e chiaro per Vinted (max 60 caratteri)",\n'
        '  "brand": "Marca visibile o Presunta/Sconosciuta",\n'
        '  "taglia": "Taglia o visibile sull\'etichetta",\n'
        '  "condizione": "Nuovo con cartellino / Nuovo senza cartellino / Ottime condizioni / Buone condizioni",\n'
        '  "descrizione": "Descrizione dettagliata e curata con dettagli, vestibilità, difetti visibili e consigli outfit",\n'
        '  "hashtag": "#vinted #marca #categoria #stile"\n'
        "}"
    )
    
    content = [prompt]
    for img_file in images_list[:20]:
        img = Image.open(img_file)
        content.append(img)
        
    response = model.generate_content(content)
    text_resp = response.text.strip()
    
    if text_resp.startswith("```json"):
        text_resp = text_resp[7:]
    if text_resp.endswith("```"):
        text_resp = text_resp[:-3]
        
    return json.loads(text_resp.strip())

# Selezione Foto direttamente dalla galleria del telefono
uploaded_photos = st.file_uploader(
    "📷 Seleziona foto dalla Galleria (Max 20 foto per articolo)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_photos:
    if len(uploaded_photos) > 20:
        st.warning("Hai selezionato più di 20 foto. Verranno analizzate solo le prime 20.")
        uploaded_photos = uploaded_photos[:20]

    st.write(f"📸 **{len(uploaded_photos)} foto selezionate**")
    
    cols = st.columns(4)
    for idx, img in enumerate(uploaded_photos[:4]):
        with cols[idx]:
            st.image(img, use_column_width=True)

    if st.button("🚀 Analizza Articolo con Gemini"):
        if not api_key:
            st.error("Inserisci prima la tua Google Gemini API Key nella barra laterale!")
        else:
            with st.spinner("Gemini sta analizzando le foto gratis..."):
                try:
                    data = analyze_with_gemini(uploaded_photos, api_key)
                    data["num_foto"] = len(uploaded_photos)
                    st.session_state.articoli.append(data)
                    st.success("✅ Articolo analizzato con successo!")
                except Exception as e:
                    st.error(f"Errore durante l'analisi: {e}")

# Visualizzazione Risultati ed Esportazione Excel
if st.session_state.articoli:
    st.write("---")
    st.subheader(f"📦 Articoli Analizzati in Questa Sessione ({len(st.session_state.articoli)})")

    df = pd.DataFrame(st.session_state.articoli)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Articoli Vinted')
        
    st.download_button(
        label="📥 Scarica Report Excel con Tutti gli Articoli",
        data=buffer.getvalue(),
        file_name="articoli_vinted_batch.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    for idx, item in enumerate(reversed(st.session_state.articoli)):
        st.markdown(f"### 🏷️ Articolo #{len(st.session_state.articoli) - idx}: {item['titolo']}")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Brand:** {item['brand']}")
        c2.write(f"**Taglia:** {item['taglia']}")
        c3.write(f"**Condizioni:** {item['condizione']}")

        st.text_input("Titolo (da copiare)", value=item['titolo'], key=f"title_{idx}")
        st.text_area("Descrizione + Hashtag (da copiare)", value=f"{item['descrizione']}\n\n{item['hashtag']}", height=140, key=f"desc_{idx}")
        st.write("---")
