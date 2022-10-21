import requests
import pandas as pd

basic = requests.get('https://elysia.zeev.it/api/2/assignments', headers={'Authorization': 'Bearer HihrPwM6iplpMc20YafyI0X20hYBwMJjn9O5b3uRXLc%3D'})
df = pd.DataFrame(basic.json())
print(df)

