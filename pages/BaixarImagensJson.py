import os
import streamlit as st
import json
import requests
from io import BytesIO
from PIL import Image
import time

# Configuração do Streamlit
st.title("Download de Imagens do Instagram a partir de JSON")
st.write("Esta pagina baixa imagens de URLs do Instagram e organiza em pastas separadas para cada post.")

# Upload do arquivo JSON
file = st.file_uploader("Carregue um arquivo JSON", type=["json"])

log_container = st.container()

if file is not None:
    json_data = json.load(file)
    posts = json_data.get("photos", {})

    if not os.path.exists("downloads/images"):
        os.makedirs("downloads/images")

    with log_container:
        st.write("### Logs de Download")
        log_area = st.empty()
        logs = ""

    for post_id, urls in posts.items():
        post_folder = os.path.join("downloads/images", f"post_{post_id}")
        os.makedirs(post_folder, exist_ok=True)
        
        for i, url in enumerate(urls):
            try:
                response = requests.get(url, stream=True)
                content_type = response.headers.get("Content-Type", "")
                
                if response.status_code == 200 and "image" in content_type:
                    img = Image.open(BytesIO(response.content))
                    img_path = os.path.join(post_folder, f"image_{i+1}.jpg")
                    img.save(img_path)
                    log_entry = f"Imagem {i+1} do post {post_id} baixada com sucesso!\n"
                else:
                    log_entry = f"URL do post {post_id} não contém uma imagem válida.\n"
            except Exception as e:
                log_entry = f"Erro ao processar imagem {i+1} do post {post_id}: {e}\n"
            
            logs += log_entry
            log_area.text_area("Logs", logs, height=300)
            time.sleep(2)  # Evita sobrecarga de requisições
    
    st.write("Download concluído! As imagens foram salvas na pasta 'downloads/images'.")
