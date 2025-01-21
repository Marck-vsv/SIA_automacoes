import streamlit as st
import requests
import google.generativeai as genai
import os
import json
from bs4 import BeautifulSoup
import pandas as pd

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
    "temperature": 0.2,
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


def get_filename_without_extension(file_path):
    # Obtem o nome do arquivo com a extensão
    file_name_with_extension = os.path.basename(file_path)
    # Separa o nome do arquivo e a extensão
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    return file_name_without_extension


# https://api.sead.pi.gov.br/sei/docs
def login(user, password, organ="SEPLAN-PI"):
    url = "https://api.sead.pi.gov.br/sei/v1/orgaos/usuarios/login"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    data = json.dumps({"Usuario": user, "Senha": password, "Orgao": organ})
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()

    if response.status_code == 200:
        resposta_json = response.json()
        token = resposta_json.get("Token")
        id_organ = resposta_json.get("Unidades")[0]["Id"]
        return token, id_organ


def get_documents(process_id, token, id_organ) -> pd.DataFrame:
    page = 1
    df_documents = []
    while True:
        quantity = 10
        url = f"https://api.sead.pi.gov.br/sei/v1/unidades/{id_organ}/procedimentos/documentos?protocolo_procedimento={process_id}&pagina={page}&quantidade={quantity}"
        headers = {"accept": "application/octet-stream", "token": token}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            response_json = response.json()
            info = response_json.get("Info")
            documents = response_json.get("Documentos")
            for document in documents:
                data = {
                    "id": document["DocumentoFormatado"],
                    "data": document["Data"],
                    "nome": document["Serie"]["Nome"],
                    "sigla": document["UnidadeElaboradora"]["Sigla"],
                    "url": document["LinkAcesso"],
                }
                df_documents.append(data)

            if info["Pagina"] == info["TotalPaginas"]:
                break
        page += 1

    return pd.DataFrame(df_documents).sort_values(by="data")


# Função para obter o arquivo html da API
def download_document(document_id, token, id_organ):
    url = f"https://api.sead.pi.gov.br/sei/v1/unidades/{id_organ}/documentos/baixar?protocolo_documento={document_id}"
    headers = {"accept": "application/octet-stream", "token": token}
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    response.encoding = "utf-8"  # Garante que o conteúdo está em UTF-8
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        html_content = soup.get_text(separator="\n", strip=True)
        return html_content
    return ""


def sei_document_summarize(process_id: str, token: str, id_organ: str):
    process_id = process_id.replace(".", "").replace("/", "").replace("-", "")

    prompt = [
        """- Analise os documentos a seguir.
- Escreva um resumo de 2 parágrafos.
- Verifique se o processo chegou ao fim.
    - Se chegou ao fim, escreva um parágrafo explicando porque foi aprovado ou reprovado."""
    ]

    df_documents = get_documents(process_id, token, id_organ)
    for i, row in df_documents.iterrows():
        try:
            # Obtém o html da API
            content = download_document(row["id"], token, id_organ)
            prompt.append(content)

            # Exibe o resultado (opcional)
            st.markdown(
                f'{row["data"]} - [{row["nome"]}]({row["url"]}) ({row["sigla"]})'
            )
            # st.markdown(content.replace("\n", "  \n"))

        except Exception as e:
            st.error(f'Erro ao processar o documento {row["id"]}: {e}')

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        safety_settings=safety_settings,
        generation_config=generation_config,
    )

    raw_response = model.generate_content(prompt, request_options={"timeout": 600})
    return raw_response.text


# Interface do Streamlit
st.title("Análise de documentos do SEI")

# Login
if st.session_state.get("authentication_status", None) is None:
    with st.form("my_form"):
        user = st.text_input("Usuário SEI:")
        password = st.text_input("Senha SEI:")
        organ = st.text_input("Órgão SEI:", placeholder="SEPLAN-PI")
        key = st.text_input("Gemini API Key:")
        st.markdown("Encontre a Key [AQUI](https://aistudio.google.com/app/apikey)")
        submitted = st.form_submit_button("Login")
        if submitted:
            st.session_state["authentication_status"] = True

            token, id_organ = login(user, password, organ)
            genai.configure(api_key=key)
            st.session_state["token"] = token
            st.session_state["id_organ"] = id_organ
            st.rerun()
# Automação
elif st.session_state["authentication_status"]:

    documents_text = st.text_input("Insira o protocolo do processo:", "")
    # Botão para iniciar o upload
    if st.button("Upload"):
        if documents_text:
            st.divider()
            response = sei_document_summarize(
                documents_text, st.session_state["token"], st.session_state["id_organ"]
            )
            st.divider()
            st.markdown(response)

        else:
            st.warning("Insira pelo menos um ID de html.")
