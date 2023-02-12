from datetime import datetime
from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message
import os

@flow
def example_email_send_message_flow():
    email_server_credentials = EmailServerCredentials(
        username="shuaib.ahmed45@gmail.com",
        password=os.getenv('EMAIL_AUTOMATION_PASS'),
    )
    subject = email_send_message(
        email_server_credentials=email_server_credentials,
        subject="Example Flow Notification using Gmail",
        msg="This proves email_send_message works!",
        email_to="shuaib.ahmed45@gmail.com",
    )
    return subject

if __name__ == "main":
    example_email_send_message_flow()


