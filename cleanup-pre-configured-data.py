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
    pass

# --- Configuration ---
MAUTIC_URL = os.getenv("MAUTIC_URL")
MAUTIC_USER = os.getenv("MAUTIC_USER")
MAUTIC_PASSWORD = os.getenv("MAUTIC_PASSWORD")

if not MAUTIC_URL or not MAUTIC_USER or not MAUTIC_PASSWORD:
    print("ERROR: Required environment variables are not set.")
    sys.exit(1)

def make_api_request(endpoint, method="GET", data=None):
    url = f"{MAUTIC_URL}/api/{endpoint}"
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
        if response.text:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"API Error ({endpoint}): {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

# --- Resource Names ---
CUSTOM_FIELD_ALIAS = "profissao"
EMAIL_NAMES = [
    "Bem-vindo ao Método Superare - D+0",
    "Método Superare - Fundamentos - D+1",
    "Método Superare - Aplicação Prática - D+2"
]
CAMPAIGN_NAME = "LancamentoSemente1"
TAG_NAME = "Semente1"
FORM_NAME = "LeadLandingPageForm"

# --- Delete Custom Field ---
print("\n=== Deleting Custom Field 'profissao' ===")
fields_response = make_api_request("fields/contact")
profissao_field_id = None
if fields_response and 'fields' in fields_response:
    for field in fields_response['fields'].values():
        if field.get('alias') == CUSTOM_FIELD_ALIAS:
            profissao_field_id = field.get('id')
            break
if profissao_field_id:
    del_result = make_api_request(f"fields/contact/{profissao_field_id}/delete", method="DELETE")
    if del_result is not None:
        print(f"✅ Custom field '{CUSTOM_FIELD_ALIAS}' deleted.")
    else:
        print(f"❌ Failed to delete custom field '{CUSTOM_FIELD_ALIAS}'.")
else:
    print(f"Custom field '{CUSTOM_FIELD_ALIAS}' does not exist.")

# --- Delete Emails ---
def get_email_id_by_name(email_name):
    emails_response = make_api_request("emails")
    if emails_response and 'emails' in emails_response:
        for email in emails_response['emails']:
            if email.get('name') == email_name:
                return email.get('id')
    return None

print("\n=== Deleting Emails ===")
for email_name in EMAIL_NAMES:
    email_id = get_email_id_by_name(email_name)
    if email_id:
        del_result = make_api_request(f"emails/{email_id}/delete", method="DELETE")
        if del_result is not None:
            print(f"✅ Email '{email_name}' deleted.")
        else:
            print(f"❌ Failed to delete email '{email_name}'.")
    else:
        print(f"Email '{email_name}' does not exist.")

# --- Delete Campaign ---
def get_campaign_id_by_name(campaign_name):
    campaigns_response = make_api_request("campaigns")
    if campaigns_response and 'campaigns' in campaigns_response:
        for campaign in campaigns_response['campaigns']:
            if campaign.get('name') == campaign_name:
                return campaign.get('id')
    return None

print("\n=== Deleting Campaign ===")
campaign_id = get_campaign_id_by_name(CAMPAIGN_NAME)
if campaign_id:
    del_result = make_api_request(f"campaigns/{campaign_id}/delete", method="DELETE")
    if del_result is not None:
        print(f"✅ Campaign '{CAMPAIGN_NAME}' deleted.")
    else:
        print(f"❌ Failed to delete campaign '{CAMPAIGN_NAME}'.")
else:
    print(f"Campaign '{CAMPAIGN_NAME}' does not exist.")

# --- Delete Tag ---
def get_tag_id_by_name(tag_name):
    tags_response = make_api_request("tags")
    if tags_response and 'tags' in tags_response:
        for tag in tags_response['tags']:
            if tag.get('tag') == tag_name:
                return tag.get('id')
    return None

print("\n=== Deleting Tag ===")
tag_id = get_tag_id_by_name(TAG_NAME)
if tag_id:
    del_result = make_api_request(f"tags/{tag_id}/delete", method="DELETE")
    if del_result is not None:
        print(f"✅ Tag '{TAG_NAME}' deleted.")
    else:
        print(f"❌ Failed to delete tag '{TAG_NAME}'.")
else:
    print(f"Tag '{TAG_NAME}' does not exist.")

# --- Delete Form ---
def get_form_id_by_name(form_name):
    forms_response = make_api_request("forms")
    if forms_response and 'forms' in forms_response:
        for form in forms_response['forms']:
            if form.get('name') == form_name:
                return form.get('id')
    return None

print("\n=== Deleting Form ===")
form_id = get_form_id_by_name(FORM_NAME)
if form_id:
    del_result = make_api_request(f"forms/{form_id}/delete", method="DELETE")
    if del_result is not None:
        print(f"✅ Form '{FORM_NAME}' deleted.")
    else:
        print(f"❌ Failed to delete form '{FORM_NAME}'.")
else:
    print(f"Form '{FORM_NAME}' does not exist.") 