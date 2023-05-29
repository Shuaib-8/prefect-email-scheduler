from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message
from prefect import variables # Retrieve variables defined in Prefect Cloud/UI
from typing import List

from email_template import email_subject, email_body

# Define flow.
# Function parameters inside flows are defined on Prefect Cloud/UI as "Flow Parameters".
@flow
def example_email_send_message_flow(email_addresses: List[str], 
                                    carers: list[str],
                                    hours: list[int]):
    # Docstring the function example_email_send_message_flow
    """
    This function sends an email to a list of email addresses, 
    aided by Prefect dataflows.

    The email body and email subject are templates which are set 
    by the function email_subject and email_body respectively
    (defined in ./email_template.py).
    The email body template is defined in email_body as a literal HTML string
    and saved as a variable called `msg` within `email_send_message` function.
   
    The email server credentials are retrieved from Prefect Cloud/UI tab 
    called 'Blocks'using the function EmailServerCredentials.load 
    with the argument where a block is defined (email server credentials).

    Parameters
    ----------
    email_addresses : List[str]
        A list of email addresses
    carers : list[str]
        A list of carer names
    hours : list[int]
        A list of hours worked

    Returns
    -------
    subject : str
        The email body and email subject, sent to the email address recipients.

    Raises
    ------
    AssertionError
        If the carers and hours lists retrieved from Prefect Cloud/UI 
        aren't identical to the email_carer_dict keys and values respectively.
    """
    email_server_credentials = EmailServerCredentials.load("gmail-access-app")

    # Define carer name and corresponding hours worked
    email_carer_dict = {
        str(variables.get('carer1')): int(variables.get('hours1')),
        str(variables.get('carer2')): int(variables.get('hours2'))
    }

    # Basic checks 
    assert carers == list(email_carer_dict.keys())
    assert hours == list(email_carer_dict.values())

    for email_address in email_addresses:
        for carer, hours in email_carer_dict.items():
            subject = email_send_message.with_options(name=f"email {email_address}").submit(
                email_server_credentials=email_server_credentials,
                subject = email_subject(carer),
                msg = email_body(carer, 
                                 hours, 
                                 variables.get('orgname'), 
                                 variables.get('rate'), 
                                 variables.get('sig')
                                ),
                email_to=email_address,
            )
    return subject


if __name__ == '__main__':
    example_email_send_message_flow()


