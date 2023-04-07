import requests
import json
import properties as pr
import pandas as pd


params = {
    'api_key' : pr.API_KEY,
}

method = 'flights'
api_base = 'http://airlabs.co/api/v9/'
api_result = requests.get(api_base + method, params)
api_response = api_result.json()

with open(pr.FLIGHTS_FILENAME, 'w+') as file:
    file.write(json.dumps(api_response['response'], indent=3))
print('success')

df = pd.read_json(pr.FLIGHTS_FILENAME)
print(df)