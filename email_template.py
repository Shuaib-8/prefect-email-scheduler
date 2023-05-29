from dotenv import load_dotenv
import os
import datetime

load_dotenv()

now = datetime.date.today()
now_month = now.strftime("%B")
now_year = now.strftime("%Y")
step_back = now.replace(day=1)
last_month = step_back - datetime.timedelta(days=1)
prev_month = last_month.strftime("%B")
prev_year = last_month.strftime('%Y')

def email_subject(name: str):
    """
    This function sets the email subject template.

    Parameters
    ----------
    name : str
        The name of the carer

    Returns
    -------
    email_sbj : str
        The email subject
    """
    email_sbj = f"{name} {prev_month} {prev_year} - {now_month} {now_year}"
    return email_sbj

def email_body(name:str, 
               hours: int, 
               org_name:str, 
               rate: int, 
               sig: str):
    """
    This function sets the email body template.

    Parameters
    ----------
    name : str
        The name of the carer
    hours : int
        The number of hours worked
    org_name : str
        The name of the organisation
    rate : int
        The hourly rate
    sig : str
        The name of the person sending the email

    Returns
    -------
    email_body_template : str
        The email body template. 
        Line breaks and text bolding are included for readability, 
        having to use literal HTML for the email body.
    """
    email_body_template = \
    f"""
    Dear {org_name},
    <br>
    <br>
    Please pay {name} for the period: 
    <br>
    <br>
    <b>{prev_month} {prev_year} - {now_month} {now_year}: {hours} hours @ {rate}</b>
    <br>
    <br>
    Kind regards,
    <br>
    {sig}    
    """
    return email_body_template

if __name__ == '__main__':
    ex = email_subject(name=os.getenv('CARER1'))
    print(ex)

    ex2 = email_body(name=os.getenv('CARER1'), 
                     hours=os.getenv('HOURS1'), 
                     org_name=os.getenv('ORGNAME'), 
                     rate=os.getenv('RATE'), 
                     sig=os.getenv('SIG')
    )
    print(ex2)