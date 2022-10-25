import requests
from prefect import flow, task 

@task(name='response-request')
def call_api(url):
    response = requests.get(url)
    print(response.status_code)
    return response.json()

@task(name='parse-text')
def parse_fact_text(response, field:str= 'text'):
    fact = response[field]
    print(fact)
    return fact 

@flow(name='random-fact-parser')
def api_flow(url):
    fact_json = call_api(url)
    fact_text = parse_fact_text(fact_json)
    return fact_text


api_flow("https://uselessfacts.jsph.pl/random.json?language=en")
