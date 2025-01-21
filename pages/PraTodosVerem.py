import streamlit as st
import streamlit_authenticator as stauth
import google.generativeai as genai
import os
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

# Load authenticator
credentials_path = '.streamlit/credentials.yaml'
with open(credentials_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

authenticator.login()

with open(credentials_path, 'w') as file:
    yaml.dump(config, file, default_flow_style=False)

if st.session_state["authentication_status"]:
    # Get user gemini api key
    st.info("Encontre a Key [AQUI](https://aistudio.google.com/app/apikey)")
    key = st.text_input("Gemini API Key:")

    # Load image from file and display it
    image = st.file_uploader("Carregue uma Imagem", type=["jpg", "jpeg", "png"])
    if image is not None:
        st.image(image, width=300)

    # Send e-mail to Gemini for analysis
    if st.button("Ver", type="primary"):
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
elif st.session_state["authentication_status"] is False:
    st.error('Username/password está incorreto')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, entre Username e Password')
