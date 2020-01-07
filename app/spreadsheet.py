import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd

def saveUserInfo(userId):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("user_info")
    with open(f'./output/{userId}.json') as json_file:
        data = json.load(json_file)
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False, encoding='utf-8')
    client.import_csv(sheet.id, csv.encode('utf-8'))