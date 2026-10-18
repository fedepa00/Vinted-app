import streamlit as st
import pandas as pd
import io
import base64
import json
from openai import OpenAI

# Configurazione Pagina Mobile
st.set_page_config(page_title="Vinted AI Assistant", page_icon="🛍️", layout="wide")

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

st.title("🛍️ Vinted AI Assistant")
st.caption("Seleziona fino a 20 foto dalla galleria per generare subito i dati del tuo articolo.")

# Sidebar per la API Key
st.sidebar.header("🔑 Configurazione")
api_key = st.sidebar.text_input("Inserisci OpenAI API Key", type="password")

# Session State per salvare gli articoli elaborati
if "articoli" not in st.session_state:
    st.session_state.articoli = []

def analyze_article_photos(images_list, client):
    content_payload = [
        {
            "type": "text",
            "text": (
                "Sei un esperto di vendite su Vinted Italia.\n"
                "Analizza queste foto (fino a 20) appartenenti allo STESSO articolo di abbigliamento/accessorio.\n"
                "Rispondi SOLO ed ESCLUSIVAMENTE con un oggetto JSON valido con queste chiavi esatte:\n"
                "{\n"
                '  "titolo": "Titolo d\'impatto e chiaro per Vinted (max 60 caratteri)",\n'
                '  "brand": "Marca visibile o Presunta/Sconosciuta",\n'
                '  "taglia": "Taglia o visibile sull\'etichetta",\n'
                '  "condizione": "Nuovo con cartellino / Nuovo senza cartellino / Ottime condizioni / Buone condizioni",\n'
                '  "descrizione": "Descrizione dettagliata e curata con dettagli, vestibilità, difetti visibili e consigli outfit",\n'
                '  "hashtag": "#vinted #marca #categoria #stile"\n'
                "}"
            )
        }
    ]
    
    for img_file in images_list[:20]:
        base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
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
        max_tokens=700
    )
    return json.loads(response.choices[0].message.content)

# File Uploader impostato su IMMAGINI (Apre direttamente la galleria su iPhone e Android)
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
    
    # Anteprima veloce delle prime foto
    cols = st.columns(4)
    for idx, img in enumerate(uploaded_photos[:4]):
        with cols[idx]:
            st.image(img, use_column_width=True)

    if st.button("🚀 Analizza Articolo"):
        if not api_key:
            st.error("Inserisci prima la tua OpenAI API Key nella barra laterale/menu!")
        else:
            with st.spinner("L'AI sta analizzando le foto..."):
                try:
                    client = OpenAI(api_key=api_key)
                    data = analyze_article_photos(uploaded_photos, client)
                    data["num_foto"] = len(uploaded_photos)
                    
                    # Salva l'articolo nella sessione
                    st.session_state.articoli.append(data)
                    st.success("✅ Articolo analizzato con successo!")
                except Exception as e:
                    st.error(f"Errore durante l'analisi: {e}")

# Se ci sono articoli analizzati, li mostra sotto
if st.session_state.articoli:
    st.write("---")
    st.subheader(f"📦 Articoli Analizzati in Questa Sessione ({len(st.session_state.articoli)})")

    # Pulsante Download Excel
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

    # Mostra ciascun articolo con caselle facili da copiare su mobile
    for idx, item in enumerate(reversed(st.session_state.articoli)):
        st.markdown(f"### 🏷️ Articolo #{len(st.session_state.articoli) - idx}: {item['titolo']}")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Brand:** {item['brand']}")
        c2.write(f"**Taglia:** {item['taglia']}")
        c3.write(f"**Condizioni:** {item['condizione']}")

        st.text_input("Titolo (da copiare)", value=item['titolo'], key=f"title_{idx}")
        st.text_area("Descrizione + Hashtag (da copiare)", value=f"{item['descrizione']}\n\n{item['hashtag']}", height=140, key=f"desc_{idx}")
        st.write("---")
