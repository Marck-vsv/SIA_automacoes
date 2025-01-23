import streamlit as st
import google.generativeai as genai
import json
import requests
from io import BytesIO
import PIL.Image
import time

HEIGHT = 500

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=safety_settings,
    generation_config=generation_config,
)

prompt = """Crie um caption para a imagem seguindo essa orientação:
• Identificar os elementos relevantes na imagem
• Descreva apenas o que tiver certeza
• Não usar aspas e parênteses
• Não usar "aproximadamente"
• Usar verbos no presente e evitar gerúndio
• Elimine pleonasmos
• Mencionar as roupas das pessoas com o verbo "usar"
Responda apenas o caption, nada mais."""

st.write("# #PraTodosVerem 😎")

st.write("Esta é uma ferramenta para ajudar pessoas com deficiência visual a apreciarem imagens.")

# Get user gemini api key
st.info("Encontre a Key [AQUI](https://aistudio.google.com/app/apikey)")
key = st.text_input("Gemini API Key:")

# Load image from file and display it
file = st.file_uploader("Carregue uma Imagem ou JSON", type=["jpg", "jpeg", "png", "json"])

if file is not None and file.type != "application/json":
    st.image(file, width=300)

button = st.button("Ver", type="primary")

st.write("## Descrição")

# Send e-mail to Gemini for analysis
if button:
    if key and file is not None:
        genai.configure(api_key=key)

        # Describe images from instagran JSON posts
        if file.type == "application/json":
            json_file = json.load(file)
            if "post" in json_file.keys():
                posts = json_file["post"]
                with st.container(height=HEIGHT, border=True):
                    for i, post in enumerate(posts):
                        if "photos_url" in post.keys():
                            photos_url = post["photos_url"]
                            photos_url = eval(photos_url)
                            photos_url = eval(photos_url)
                            for j, url in enumerate(photos_url):
                                image_bytes = requests.get(url).content
                                image = PIL.Image.open(BytesIO(image_bytes))
                                response = model.generate_content(
                                    [image, prompt]
                                )
                                st.markdown(f"({i+1}/{len(posts)}) ({j+1}) [{url}]({url})")
                                st.write(response.text)
                                post["caption"] = response.text
                                time.sleep(4)
            else:
                st.error("O JSON não contém posts com fotos")

            # Convert the dictionary to a JSON string
            json_string = json.dumps(json_file, indent=4)
            # Create a download button
            st.download_button(
                label="Salvar JSON",  # Button label in Portuguese
                data=json_string,
                file_name="descricao_" + file.name,  # Name of the file to be downloaded
                mime="application/json",  # MIME type for JSON
                type="primary"
            )
        # Describe image from file
        else:
            image = PIL.Image.open(file)
            response = model.generate_content(
                [image, prompt]
            )
            with st.container(height=HEIGHT, border=True):
                st.write(response.text)
    elif not key:
        st.error("Por favor, insira a Key")
    elif file is None:
        st.error("Por favor, insira a Imagem ou JSON")
else:
    with st.container(height=HEIGHT, border=True):
        st.write("(A descrição vai aparecer aqui)")
