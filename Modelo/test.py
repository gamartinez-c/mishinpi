from dotenv import load_dotenv
import requests
import pandas as pd

load_dotenv()

url = "https://graph.facebook.com/v13.0/act_343691773566320/insights?date_present=this_year&time_increment=1&limit=5000&access_token=EAAHtZATnPDuUBACcxFR2L4ZAkHh8rpc3d99ZCjidsxt5rndZAhhMqrZATqeTsXlJZAw0oaL9sRjrTnlSPuzreAm2SWYv6LdxWdnkdlrZAyBcBAqBeAouuA0KLl47CVYB9oKm7ZBEZCkH6TKcegms3DZCCvfnPvzka8rVMsRmCxvMIeP6zhdUqInkYBjnYlzzyCZAkbNci482YQgeak0bx6CjGID"

response = requests.get(url).json()
df_facebook_ads = pd.DataFrame(response['data'])

print(1)