import requests

url = 'http://localhost:6800/schedule.json'
project = 'handler'
spider = 'nrcadamsall'

response = requests.post(url, data={'project': project, 'spider': spider})
print(response.json())