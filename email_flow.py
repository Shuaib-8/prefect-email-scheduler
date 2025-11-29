from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message
from prefect.variables import Variable
from typing import List

from email_template import email_subject, email_body


def validate_config(config: dict) -> tuple[str, dict]:
    """
    Validate the email_config structure and return extracted values.
    
    Raises ValueError with helpful message if config is invalid.
    """
    if config is None:
        raise ValueError(
            "email_config variable not found in Prefect Cloud. "
            "Please create it with the required JSON structure."
        )
    
    if not isinstance(config, dict):
        raise ValueError(
            f"email_config must be a JSON object, got {type(config).__name__}"
        )
    
    # Validate required top-level keys
    if 'orgname' not in config:
        raise ValueError(
            "email_config missing required key 'orgname'. "
            "Expected: {\"orgname\": \"<name>\", \"carers\": {...}}"
        )
    
    if 'carers' not in config:
        raise ValueError(
            "email_config missing required key 'carers'. "
            "Expected: {\"orgname\": \"<name>\", \"carers\": {...}}"
        )
    
    carers = config['carers']
    if not isinstance(carers, dict) or len(carers) == 0:
        raise ValueError(
            "email_config 'carers' must be a non-empty object. "
            "Expected: {\"<carer_name>\": {\"hours\": ..., \"rate\": ..., \"sig\": ..., \"reference\": ...}}"
        )
    
    # Validate each carer's config
    required_carer_keys = ['hours', 'rate', 'sig', 'reference']
    for carer_name, carer_config in carers.items():
        if not isinstance(carer_config, dict):
            raise ValueError(
                f"Carer '{carer_name}' config must be an object, got {type(carer_config).__name__}"
            )
        
        missing_keys = [key for key in required_carer_keys if key not in carer_config]
        if missing_keys:
            raise ValueError(
                f"Carer '{carer_name}' missing required keys: {missing_keys}. "
                f"Expected: {{\"hours\": <int>, \"rate\": \"<rate>\", \"sig\": \"<name>\", \"reference\": \"<ref>\"}}"
            )
    
    return config['orgname'], carers


@flow
def example_email_send_message_flow(email_addresses: List[str]):
    """
    Sends payment emails to carers via Prefect Cloud.

    Email configuration is loaded from a single JSON variable 'email_config' in Prefect Cloud.
    
    Expected JSON format:
    {
        "orgname": "<organization_name>",
        "carers": {
            "<carer_name>": {
                "hours": <int>,
                "rate": "<hourly_rate>",
                "sig": "<signature_name>",
                "reference": "<reference_number>"
            }
        }
    }

    Parameters
    ----------
    email_addresses : List[str]
        A list of email addresses to send to

    Returns
    -------
    subject
        The last email task submitted.
    
    Raises
    ------
    ValueError
        If email_config is missing or has invalid structure.
    """
    email_server_credentials = EmailServerCredentials.load("gmail-access-app")

    # Load and validate configuration
    config = Variable.get('email_config')  # type: ignore
    org_name, carers = validate_config(config)  # type: ignore

    subject = None
    for email_address in email_addresses:
        for carer_name, carer_config in carers.items():
            subject = email_send_message.with_options(name=f"email {email_address} - {carer_name}").submit(
                email_server_credentials=email_server_credentials,  # type: ignore
                subject=email_subject(carer_name),
                msg=email_body(
                    name=carer_name, 
                    hours=int(carer_config['hours']), 
                    org_name=org_name, 
                    rate=carer_config['rate'], 
                    sig=carer_config['sig'],
                    reference=carer_config['reference']
                ),
                email_to=email_address,
            )
    return subject
