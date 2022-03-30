# Guess365DataAPI

提供[Guess365](https://guess365.cc/ "Guess365")進行賽事盤口查詢、預測盤口服務。


# 預測盤口範例
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://192.168.0.223:5000/PredictMatchEntry/'
data = {'account':'ccc',
        'password':'123123',
        'GroupOptionCode':'10',
        'OptionCode':'X',
        'EventCode':'113172483'}

response = requests.post(url, data = data, auth=HTTPBasicAuth('guess365', 'er3p5eak97')).text
```
## JSON參數

參數  | 用途
------------- | -------------
account  | 帳戶
password  | 密碼
GroupOptionCode  | 盤口編號
OptionCode  | 選擇方
EventCode  | 賽事編號

## 其他參數
參數  | 用途
------------- | -------------
HTTPBasicAuth  | user='guess365', password='er3p5eak97'
URL  | http://192.168.0.223:5000/PredictMatchEntry/

<div style="page-break-after: always;"></div>

# 查詢盤口範例
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://192.168.0.223:5000/MatchEntryInfo/DateBetween/NBA/2022-4-1~2022-4-29'

response = requests.get(url, auth=HTTPBasicAuth('guess365', 'er3p5eak97')).text
```

## URL參數
參數  | 用途
------------- | -------------
HTTPBasicAuth  | user='guess365', password='er3p5eak97'
URL 1 | http://192.168.0.223:5000/MatchEntryInfo/DateBetween/All/**[Input:DateBetween]**
URL 2 | http://192.168.0.223:5000/MatchEntryInfo/DateBetween/**[Input:TournamentText]**/**[Input:DateBetween]**
URL 3 | http://192.168.0.223:5000/MatchEntryInfo/**[EventCode]**
[Input:TournamentText] | 聯盟名稱，例如：NBA、EPL、NFL、MLB等等。
[Input:DateBetween] | 提供兩種輸入方式，'2022-3-29~2022-3-29' 或 'any'。