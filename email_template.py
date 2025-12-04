import datetime


def _get_date_range() -> tuple[str, str, str, str]:
    """
    Calculate current and previous month/year for email templates.

    Called fresh each time to ensure dates are always current,
    even in long-running deployments.

    Returns
    -------
    tuple
        (prev_month, prev_year, now_month, now_year)
    """
    now = datetime.date.today()
    now_month = now.strftime("%B")
    now_year = now.strftime("%Y")
    step_back = now.replace(day=1)
    last_month = step_back - datetime.timedelta(days=1)
    prev_month = last_month.strftime("%B")
    prev_year = last_month.strftime("%Y")
    return prev_month, prev_year, now_month, now_year


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
    prev_month, prev_year, now_month, now_year = _get_date_range()
    return f"{name} {prev_month} {prev_year} - {now_month} {now_year}"


def email_body(name: str, hours: int, org_name: str, rate: str, sig: str, reference: str) -> str:
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
    prev_month, prev_year, now_month, now_year = _get_date_range()
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
