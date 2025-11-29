import datetime

# Calculate date ranges for email template
now = datetime.date.today()
now_month = now.strftime("%B")
now_year = now.strftime("%Y")
step_back = now.replace(day=1)
last_month = step_back - datetime.timedelta(days=1)
prev_month = last_month.strftime("%B")
prev_year = last_month.strftime('%Y')


def email_subject(name: str) -> str:
    """
    This function sets the email subject template.

    Parameters
    ----------
    name : str
        The name of the carer

    Returns
    -------
    str
        The email subject in format: "Name PrevMonth PrevYear - CurrentMonth CurrentYear"
    """
    return f"{name} {prev_month} {prev_year} - {now_month} {now_year}"


def email_body(name: str, 
               hours: int, 
               org_name: str, 
               rate: str, 
               sig: str,
               reference: str) -> str:
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
    rate : str
        The hourly rate (e.g., "£11.95")
    sig : str
        The name of the person sending the email
    reference : str
        The reference number for the payment

    Returns
    -------
    str
        The email body template as HTML string.
    """
    return f"""
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
    {sig} - Reference: {reference}
    """
