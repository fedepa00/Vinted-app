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
