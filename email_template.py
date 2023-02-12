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

def email_subject(name=os.getenv('CARER1')):
    email_sbj = f"{name} {prev_month} {prev_year} - {now_month} {now_year}"
    return email_sbj

def email_body(name=os.getenv('CARER1'), hours=40):
    email_body_template = \
    f"""
    Dear {os.getenv('ORGNAME')},

    Please pay {name} for the period: 
    
    {prev_month} {prev_year} - {now_month} {now_year}: {hours} hours @ {os.getenv('RATE')}
    
    Kind regards,
    {os.getenv('SIG')}    
    """
    return email_body_template

if __name__ == '__main__':
    ex = email_subject(name=os.getenv('CARER1'))
    print(ex)

    ex2 = email_body(name=os.getenv('CARER1'), hours=24)
    print(ex2)