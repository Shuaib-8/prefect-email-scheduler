from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message
from prefect import variables
from typing import List
import os 

from email_template import email_subject, email_body

# Function parameters inside flows are defined on Prefect Cloud/UI as "Flow Parameters"
@flow
def example_email_send_message_flow(email_addresses: List[str]):
    email_server_credentials = EmailServerCredentials.load("gmail-access-app")
    for email_address in email_addresses:
        subject = email_send_message.with_options(name=f"email {email_address}").submit(
            email_server_credentials=email_server_credentials,
            subject="Example Flow Notification using Gmail",
            msg=f"This proves email_send_message works!",
            email_to=email_address,
        )
    return subject


if __name__ == '__main__':
    example_email_send_message_flow()


