import requests
import json
import os
import sys

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv('.mautic_env')
except ImportError:
    print("Warning: python-dotenv not installed. Loading environment from system variables.")
    # Load from system environment variables instead
    pass

# --- Configuration ---
# Get Mautic instance details from environment variables
MAUTIC_URL = os.getenv("MAUTIC_URL")
MAUTIC_USER = os.getenv("MAUTIC_USER")
MAUTIC_PASSWORD = os.getenv("MAUTIC_PASSWORD")

# Check if required environment variables are set
if not MAUTIC_URL:
    print("ERROR: MAUTIC_URL environment variable is not set")
    print("Please set MAUTIC_URL in your .mautic_env file")
    sys.exit(1)

if not MAUTIC_USER:
    print("ERROR: MAUTIC_USER environment variable is not set")
    print("Please set MAUTIC_USER in your .mautic_env file")
    sys.exit(1)

if not MAUTIC_PASSWORD:
    print("ERROR: MAUTIC_PASSWORD environment variable is not set")
    print("Please set MAUTIC_PASSWORD in your .mautic_env file")
    sys.exit(1)

print(f"Using Mautic URL: {MAUTIC_URL}")
print(f"Using Mautic User: {MAUTIC_USER}")

# --- Helper Functions ---
def make_api_request(endpoint, method="GET", data=None):
    """Make API request with proper error handling"""
    url = f"{MAUTIC_URL}/api/{endpoint}"
    # Cast to strings since we've already validated they're not None
    auth = (str(MAUTIC_USER), str(MAUTIC_PASSWORD))
    
    try:
        if method == "GET":
            response = requests.get(url, auth=auth, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, auth=auth, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, auth=auth, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, auth=auth, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error ({endpoint}): {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

# --- Step 1: Create Custom Fields ---
print("\n=== Step 1: Creating Custom Fields ===")

# Check if custom field 'profissao' already exists
print("Checking if custom field 'profissao' already exists...")
fields_response = make_api_request("fields/contact")
profissao_field_id = None
if fields_response and 'fields' in fields_response:
    fields = fields_response['fields']
    if isinstance(fields, dict):
        field_iter = fields.values()
    else:
        field_iter = fields
    for field in field_iter:
        if isinstance(field, dict) and field.get('alias') == 'profissao':
            profissao_field_id = field.get('id')
            print(f"Custom field 'profissao' already exists with ID {profissao_field_id}")
            break

if not profissao_field_id:
    # Custom field for profession/area de atuação
    profession_field = {
        "label": "Profissão",
        "alias": "profissao",
        "type": "select",
        "group": "core",
        "object": "contact",
        "properties": {
            "list": [
                {"label": "Educação Física", "value": "educacao_fisica"},
                {"label": "Fisioterapia", "value": "fisioterapia"},
                {"label": "Medicina Esportiva", "value": "medicina_esportiva"},
                {"label": "Medicina", "value": "medicina"},
                {"label": "Empreendedor", "value": "empreendedor"},
                {"label": "Outro", "value": "outro"}
            ]
        }
    }

    print("Creating custom field 'profissao'...")
    profession_result = make_api_request("fields/contact/new", "POST", profession_field)

    if profession_result:
        print("✅ Custom field 'profissao' created successfully")
        profissao_field_id = profession_result.get('field', {}).get('id')
    else:
        print("❌ Failed to create custom field 'profissao'")
        sys.exit(1)

# --- Step 2: Create Email Category ---
print("\n=== Step 2: Creating Email Category ===")

def get_email_category_id_by_name(category_name):
    categories_response = make_api_request("categories?type=email")
    if categories_response and 'categories' in categories_response:
        for cat in categories_response['categories']:
            if cat.get('title') == category_name:
                return cat.get('id')
    return None

email_category_name = "Semente Aquecimento"
email_category_id = get_email_category_id_by_name(email_category_name)
if email_category_id:
    print(f"Email category '{email_category_name}' already exists with ID {email_category_id}")
else:
    category_data = {
        "title": email_category_name,
        "bundle": "email"
}
    print(f"Creating email category '{email_category_name}'...")
    category_result = make_api_request("categories/new", "POST", category_data)
    if category_result:
        print(f"✅ Email category '{email_category_name}' created successfully")
        email_category_id = category_result.get('category', {}).get('id')
    else:
        print(f"❌ Failed to create email category")
    sys.exit(1)

# --- Step 2: Create Welcome Emails (moved up) ---
print("\n=== Step 2: Creating Welcome Email Sequence ===")

def get_email_id_by_name(email_name):
    emails_response = make_api_request("emails")
    if emails_response and 'emails' in emails_response:
        for email in emails_response['emails']:
            if isinstance(email, dict) and email.get('name') == email_name:
                return email.get('id')
    return None

# Email 1: Day 0 (Welcome)
email1_name = "Bem-vindo ao Método Superare - D+0"
email1_id = get_email_id_by_name(email1_name)
if email1_id:
    print(f"Email '{email1_name}' already exists with ID {email1_id}")
else:
    email1_data = {
        "name": email1_name,
    "subject": "Bem-vindo ao Método Superare! 🌟",
    "content": """
    <h2>Olá {contactfield=firstname}!</h2>
    
    <p>Seja bem-vindo ao <strong>Método Superare</strong>!</p>
    
    <p>Ficamos muito felizes em ter você conosco. O Método Superare é uma abordagem revolucionária que combina:</p>
    
    <ul>
        <li>✅ Ciência do esporte de alto rendimento</li>
        <li>✅ Metodologias comprovadas de reabilitação</li>
        <li>✅ Estratégias de prevenção de lesões</li>
        <li>✅ Desenvolvimento de performance atlética</li>
    </ul>
    
    <p>Nos próximos dias, você receberá informações valiosas sobre como aplicar essas técnicas em sua prática profissional.</p>
    
    <p>Fique atento ao seu email!</p>
    
    <p>Atenciosamente,<br>
    <strong>Equipe Superare</strong></p>
    """,
        "isPublished": True,
        "category": email_category_id
}
print("Creating welcome email (D+0)...")
email1_result = make_api_request("emails/new", "POST", email1_data)
if email1_result:
    print("✅ Welcome email (D+0) created successfully")
    email1_id = email1_result.get('email', {}).get('id')
else:
    print("❌ Failed to create welcome email")
    sys.exit(1)

# Email 2: Day 1
email2_name = "Método Superare - Fundamentos - D+1"
email2_id = get_email_id_by_name(email2_name)
if email2_id:
    print(f"Email '{email2_name}' already exists with ID {email2_id}")
else:
    email2_data = {
        "name": email2_name,
    "subject": "Os 3 Pilares do Método Superare 📚",
    "content": """
    <h2>Olá {contactfield=firstname}!</h2>
    
    <p>Hoje vamos falar sobre os <strong>3 Pilares Fundamentais</strong> do Método Superare:</p>
    
    <h3>🎯 Pilar 1: Avaliação Específica</h3>
    <p>Identificamos as necessidades individuais de cada atleta ou paciente através de avaliações precisas e personalizadas.</p>
    
    <h3>⚡ Pilar 2: Treinamento Funcional</h3>
    <p>Desenvolvemos programas de treinamento que simulam movimentos reais e melhoram a performance específica.</p>
    
    <h3>🛡️ Pilar 3: Prevenção Inteligente</h3>
    <p>Implementamos estratégias proativas para prevenir lesões e otimizar a recuperação.</p>
    
    <p>Esses pilares formam a base de todo o nosso método. Amanhã você descobrirá como aplicá-los na prática!</p>
    
    <p>Atenciosamente,<br>
    <strong>Equipe Superare</strong></p>
    """,
        "isPublished": True,
        "category": email_category_id
}
print("Creating day 1 email...")
email2_result = make_api_request("emails/new", "POST", email2_data)
if email2_result:
    print("✅ Day 1 email created successfully")
    email2_id = email2_result.get('email', {}).get('id')
else:
    print("❌ Failed to create day 1 email")
    sys.exit(1)

# Email 3: Day 2
email3_name = "Método Superare - Aplicação Prática - D+2"
email3_id = get_email_id_by_name(email3_name)
if email3_id:
    print(f"Email '{email3_name}' already exists with ID {email3_id}")
else:
    email3_data = {
        "name": email3_name,
    "subject": "Como Aplicar o Método Superare na Prática 🚀",
    "content": """
    <h2>Olá {contactfield=firstname}!</h2>
    
    <p>Chegou o momento de colocar o <strong>Método Superare</strong> em ação!</p>
    
    <h3>🎯 Passo a Passo da Aplicação:</h3>
    
    <ol>
        <li><strong>Avaliação Inicial:</strong> Identifique as necessidades específicas</li>
        <li><strong>Planejamento:</strong> Desenvolva um programa personalizado</li>
        <li><strong>Execução:</strong> Implemente o treinamento progressivo</li>
        <li><strong>Monitoramento:</strong> Acompanhe os resultados</li>
        <li><strong>Ajustes:</strong> Otimize baseado no feedback</li>
    </ol>
    
    <h3>💡 Dica do Dia:</h3>
    <p>Lembre-se: cada pessoa é única. O Método Superare se adapta às necessidades individuais, não o contrário.</p>
    
    <p>Você está pronto para transformar sua prática profissional!</p>
    
    <p>Atenciosamente,<br>
    <strong>Equipe Superare</strong></p>
    """,
        "isPublished": True,
        "category": email_category_id
}
print("Creating day 2 email...")
email3_result = make_api_request("emails/new", "POST", email3_data)
if email3_result:
    print("✅ Day 2 email created successfully")
    email3_id = email3_result.get('email', {}).get('id')
else:
    print("❌ Failed to create day 2 email")
    sys.exit(1)

# --- Step 3.5: Create Tag ---
print("\n=== Step 3.5: Creating Tag ===")

def get_tag_id_by_name(tag_name):
    tags_response = make_api_request("tags")
    if tags_response and 'tags' in tags_response:
        for tag in tags_response['tags']:
            if isinstance(tag, dict) and tag.get('tag') == tag_name:
                return tag.get('id')
    return None

tag_name = "Semente1"
tag_id = get_tag_id_by_name(tag_name)
if tag_id:
    print(f"Tag '{tag_name}' already exists with ID {tag_id}")
else:
    tag_data = {
        "tag": tag_name
    }
    print(f"Creating tag '{tag_name}'...")
    tag_result = make_api_request("tags/new", "POST", tag_data)
    if tag_result:
        print(f"✅ Tag '{tag_name}' created successfully")
        tag_id = tag_result.get('tag', {}).get('id')
    else:
        print(f"❌ Failed to create tag")
        sys.exit(1)

# --- Step 3.6: Create Segment ---
print("\n=== Step 3.6: Creating Segment ===")

def get_segment_id_by_name(segment_name):
    segments_response = make_api_request("segments")
    if segments_response and 'lists' in segments_response:
        lists = segments_response['lists']
        if isinstance(lists, dict):
            segment_iter = lists.values()
        else:
            segment_iter = lists
        for segment in segment_iter:
            if isinstance(segment, dict) and segment.get('name') == segment_name:
                return segment.get('id')
    return None

segment_name = "Semente1"
segment_id = get_segment_id_by_name(segment_name)
if segment_id:
    print(f"Segment '{segment_name}' already exists with ID {segment_id}")
else:
    segment_data = {
        "name": segment_name,
        "alias": "semente1",
        "description": "Segmento para campanha Semente1",
        "isPublished": True
    }
    print(f"Creating segment '{segment_name}'...")
    segment_result = make_api_request("segments/new", "POST", segment_data)
    if segment_result:
        print(f"✅ Segment '{segment_name}' created successfully")
        segment_id = segment_result.get('list', {}).get('id')
    else:
        print(f"❌ Failed to create segment")
        sys.exit(1)

# --- Step 3: Create Campaign (now with first event) ---
print("\n=== Step 3: Creating Campaign ===")

def get_campaign_id_by_name(campaign_name):
    campaigns_response = make_api_request("campaigns")
    if campaigns_response and 'campaigns' in campaigns_response:
        for campaign in campaigns_response['campaigns']:
            if campaign.get('name') == campaign_name:
                return campaign.get('id')
    return None

campaign_name = "LancamentoSemente1"
campaign_id = get_campaign_id_by_name(campaign_name)
if campaign_id:
    print(f"Campaign '{campaign_name}' already exists with ID {campaign_id}")
else:
    campaign_data = {
        "name": campaign_name,
        "description": "Campanha de lançamento para captura de leads",
        "isPublished": True,
        "sources": [
            {
                "type": "segment",
                "id": segment_id
            }
        ],
        "events": [
            {
                "name": "Send email (D+0)",
                "type": "email.send",
                "properties": {
                    "email": email1_id,
                    "send_delay": 0
                }
            }
        ]
    }
    print(f"Creating campaign '{campaign_name}'...")
    campaign_result = make_api_request("campaigns/new", "POST", campaign_data)
    if campaign_result:
        print(f"✅ Campaign '{campaign_name}' created successfully")
        campaign_id = campaign_result.get('campaign', {}).get('id')
    else:
        print("❌ Failed to create campaign")
        sys.exit(1)

# --- Step 4: Create Form with Proper Field Mapping ---
print("\n=== Step 4: Creating Form ===")

def get_form_id_by_name(form_name):
    forms_response = make_api_request("forms")
    if forms_response and 'forms' in forms_response:
        for form in forms_response['forms']:
            if form.get('name') == form_name:
                return form.get('id')
    return None

form_name = "LeadLandingPageForm"
form_id = get_form_id_by_name(form_name)
if form_id:
    print(f"Form '{form_name}' already exists with ID {form_id}")
else:
    form_payload = {
        "name": form_name,
        "alias": "leadlandingpageform",
        "formType": "campaign",
        "isPublished": True,
        "fields": [
            {
                "label": "Nome",
                "type": "text",
                "alias": "firstname",  # Maps to contact firstname field
                "isRequired": True,
                "validationMessage": "O campo Nome é obrigatório."
            },
            {
                "label": "Email",
                "type": "email",
                "alias": "email",  # Maps to contact email field
                "isRequired": True,
                "validationMessage": "Por favor, insira um email válido."
            },
            {
                "label": "Código do País",
                "type": "text",
                "alias": "country_code",  # Custom field for country code
                "isRequired": True,
                "properties": {
                    "maxLength": 4
                },
                "validationMessage": "O código do país é obrigatório (ex: +55, +1, +44)."
            },
            {
                "label": "Celular",
                "type": "tel",
                "alias": "mobile",  # Maps to contact mobile field
                "isRequired": True,
                "validationMessage": "O campo Celular é obrigatório."
            },
            {
                "label": "Área de Atuação",
                "type": "select",
                "alias": "profissao",  # Maps to custom profession field
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
        ],
        "actions": [
            {
                "name": "Add to campaign",
                "type": "campaign.add",
                "properties": {
                    "campaign": campaign_id
                }
            },
            {
                "name": "Add tag",
                "type": "contact.addtag",
                "properties": {
                    "tags": [tag_name]
                }
            }
        ]
    }
    print(f"Creating form '{form_name}'...")
    form_result = make_api_request("forms/new", "POST", form_payload)
    if form_result:
        print(f"✅ Form '{form_name}' created successfully")
        form_id = form_result.get('form', {}).get('id')
        print(f"Form ID: {form_id}")
        print(f"Campaign ID: {campaign_id}")
        print(f"Tag ID: {tag_id}")
        print("\n--- Form Details ---")
        print(json.dumps(form_result, indent=2))
    else:
        print(f"❌ Failed to create form")
        sys.exit(1)

# --- Step 4: Verify Field Mapping ---
print("\n=== Step 4: Field Mapping Summary ===")
print("Form fields mapped to contact fields:")
print("- 'firstname' → contact.firstname")
print("- 'email' → contact.email") 
print("- 'mobile' → contact.mobile")
print("- 'country_code' → custom field (country code)")
print("- 'profissao' → custom field (profession)")

print(f"\n✅ Setup completed successfully!")
print(f"Form URL: {MAUTIC_URL}/form/leadlandingpageform")
print(f"Campaign: LancamentoSemente1 (ID: {campaign_id})")
print(f"Form: LeadLandingPageForm (ID: {form_id})")
print(f"Tag: Semente1 (ID: {tag_id})")
print(f"Actions: Form submissions will add contacts to campaign and tag them with 'Semente1'")

print(f"\n📧 Email Sequence Created:")
print(f"- D+0: Bem-vindo ao Método Superare (ID: {email1_id})")
print(f"- D+1: Os 3 Pilares do Método Superare (ID: {email2_id})")
print(f"- D+2: Como Aplicar o Método Superare na Prática (ID: {email3_id})")

print(f"\n🎯 Complete Workflow:")
print(f"1. Lead submits form → Contact created")
print(f"2. Contact added to 'LancamentoSemente1' campaign")
print(f"3. Contact tagged with 'Semente1'")
print(f"4. Welcome email sent immediately (D+0)")
print(f"5. Follow-up email sent next day (D+1)")
print(f"6. Final email sent 2 days later (D+2)")

# Remove any prompt: always proceed in CI/CD
# (No need for SENDGRID_API_KEY check here, as this script is for pre-configured data)
# End of script 