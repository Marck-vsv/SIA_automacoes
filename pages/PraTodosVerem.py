import streamlit as st
import google.generativeai as genai
import yaml
from yaml.loader import SafeLoader
import PIL.Image

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
• Mencionar as roupas com o verbo "usar"
• Não usar aspas e parênteses
• Não usar "aproximadamente"
• Identificar os elementos relevantes na imagem
• Usar verbos no presente e evitar gerúndio
• Elimine pleonasmos
• Descreva apenas o que tiver certeza"""

st.write("# #PraTodosVerem 😎")

st.write("Esta é uma ferramenta para ajudar pessoas com deficiência visual a apreciarem imagens.")

# Get user gemini api key
st.info("Encontre a Key [AQUI](https://aistudio.google.com/app/apikey)")
key = st.text_input("Gemini API Key:")

# Load image from file and display it
image = st.file_uploader("Carregue uma Imagem", type=["jpg", "jpeg", "png"])
if image is not None:
    st.image(image, width=300)

button = st.button("Ver", type="primary")

st.write("## Descrição")

# Send e-mail to Gemini for analysis
if button:
    if key and image is not None:
        genai.configure(api_key=key)
        image = PIL.Image.open(image)
        response = model.generate_content(
            [image, prompt]
        )
        st.write(response.text)
    elif not key:
        st.error("Por favor, insira a Key")
    elif image is None:
        st.error("Por favor, insira a Imagem")
else:
    st.write("(A descrição vai aparecer aqui)")