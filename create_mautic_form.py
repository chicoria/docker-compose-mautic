import requests
import json
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
# Load variables from .mautic_env file
load_dotenv('.mautic_env')

# --- Configuration ---
# Get Mautic instance details from environment variables
MAUTIC_URL = os.getenv("MAUTIC_URL", "https://your-mautic-instance.com")
MAUTIC_USER = os.getenv("MAUTIC_USER", "your_mautic_username")
MAUTIC_PASSWORD = os.getenv("MAUTIC_PASSWORD", "your_mautic_password")

# If MAUTIC_URL is not set, construct it from other variables
if MAUTIC_URL == "https://your-mautic-instance.com":
    # Try to construct URL from available variables
    mautic_host = os.getenv("MAUTIC_HOST", "localhost")
    mautic_port = os.getenv("MAUTIC_PORT", "8001")
    mautic_protocol = os.getenv("MAUTIC_PROTOCOL", "http")
    
    if mautic_host != "localhost":
        MAUTIC_URL = f"{mautic_protocol}://{mautic_host}"
        if mautic_port and mautic_port != "80" and mautic_port != "443":
            MAUTIC_URL += f":{mautic_port}"

print(f"Using Mautic URL: {MAUTIC_URL}")
print(f"Using Mautic User: {MAUTIC_USER}")

# --- Form and Field Definitions ---
# This payload defines the form and its fields according to the Mautic API structure.
form_payload = {
    "name": "FormInteresse1",
    "alias": "forminteresse1", # Optional: Mautic will generate this if left blank
    "formType": "campaign",  # Specify that this is a Campaign Form
    "fields": [
        {
            "label": "Email",
            "type": "email",
            "alias": "email",
            "isRequired": True,
            "validationMessage": "Por favor, insira um email válido."
        },
        {
            "label": "Nome",
            "type": "text",
            "alias": "nome",
            "isRequired": True,
            "validationMessage": "O campo Nome é obrigatório."
        },
        {
            "label": "DDD",
            "type": "text",
            "alias": "ddd",
            "isRequired": True,
            "properties": {
                "maxLength": 3
            },
            "validationMessage": "O campo DDD é obrigatório."
        },
        {
            "label": "Celular",
            "type": "tel",
            "alias": "celular",
            "isRequired": True,
            "validationMessage": "O campo Celular é obrigatório."
        },
        {
            "label": "Área de Atuação",
            "type": "select",
            "alias": "area_de_atuacao",
            "isRequired": True,
            "properties": {
                "list": [
                    {"label": "Educação Física", "value": "educacao_fisica"},
                    {"label": "Fisioterapia", "value": "fisioterapia"},
                    {"label": "Medicina Esportiva", "value": "medicina_esportiva"},
                    {"label": "Medicina", "value": "medicina"},
                    {"label": "Empreendedor", "value": "empreendedor"},
                    {"label": "Outro", "value": "outro"}
                ]
            },
            "validationMessage": "Por favor, selecione sua área de atuação."
        }
    ]
}

# --- API Request ---
api_endpoint = f"{MAUTIC_URL}/api/forms/new"

print(f"Enviando requisição para: {api_endpoint}")

try:
    response = requests.post(
        api_endpoint,
        json=form_payload,
        auth=(MAUTIC_USER, MAUTIC_PASSWORD)
    )
    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()

    # --- Process Response ---
    if response.status_code == 201:
        print("\nFormulário 'FormInteresse1' criado com sucesso!")
        print("--- Detalhes do Formulário ---")
        # Pretty print the JSON response
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\nErro ao criar o formulário. Status: {response.status_code}")
        print("Resposta:", response.text)

except requests.exceptions.HTTPError as errh:
    print(f"\nErro HTTP: {errh}")
    print("Verifique se a URL, usuário e senha estão corretos e se o usuário tem as permissões necessárias.")
    print("Detalhes da resposta do servidor:", response.text)
except requests.exceptions.ConnectionError as errc:
    print(f"\nErro de Conexão: {errc}")
    print("Não foi possível conectar ao Mautic. Verifique a URL e sua conexão com a internet.")
except requests.exceptions.Timeout as errt:
    print(f"\nErro de Timeout: {errt}")
except requests.exceptions.RequestException as err:
    print(f"\nAlgo deu errado: {err}") 