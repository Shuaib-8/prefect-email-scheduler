from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message
from prefect.variables import Variable
from typing import List

from email_template import email_subject, email_body


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
    """
    email_server_credentials = EmailServerCredentials.load("gmail-access-app")

    # Load all email configuration from JSON variable (Prefect auto-parses JSON)
    config = Variable.get('email_config')  # type: ignore
    org_name = config['orgname']
    carers = config['carers']

    subject = None
    for email_address in email_addresses:
        for carer_name, carer_config in carers.items():
            subject = email_send_message.with_options(name=f"email {email_address} - {carer_name}").submit(
                email_server_credentials=email_server_credentials, # type: ignore
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
