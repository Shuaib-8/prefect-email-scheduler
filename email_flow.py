from datetime import datetime
from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message

@flow
def example_email_send_message_flow(email_addresses):
    email_server_credentials = EmailServerCredentials.load("email-server-credentials")
    for email_address in email_addresses:
        subject = email_send_message.with_options(name=f"email {email_address}").submit(
            email_server_credentials=email_server_credentials,
            subject="Example Flow Notification using Gmail",
            msg="This proves email_send_message works!",
            email_to=email_address,
        )

if __name__ == '__main__':
    example_email_send_message_flow(["shuaib.ahmed45@gmail.com"])


