# Guess365DataAPI

提供[Guess365](https://guess365.cc/ "Guess365")進行賽事盤口查詢、預測盤口服務。


# 預測盤口-單筆 範例
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://192.168.0.223:5000/PredictMatchEntry/'
data = {'account':'ccc',
        'password':'123123',
        'GroupOptionCode':'10',
        'OptionCode':'X',
        'EventCode':'113172483',
        'PredictType':'Forecast'}

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
PredictType  | 預測類型('Forecast' or 'Selling')

## 其他參數
參數  | 用途
------------- | -------------
HTTPBasicAuth  | user='guess365', password='er3p5eak97'
URL  | http://192.168.0.223:5000/PredictMatchEntry/

<div style="page-break-after: always;"></div>

# 預測盤口-多筆 範例
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://ecocoapidev1.southeastasia.cloudapp.azure.com/UserMemberSellingPushMessage'
data = {"predlist":[
                    {"account":"koer3743",
                    "password":"er3p5eak97",
                    "GroupOptionCode":20,
                    "OptionCode":2,
                    "EventCode":"119890397",
                    "predict_type":"Selling",
                    "HomeOdds":4.5,
                    "AwayOdds":1.1,
                    "HomeConfidence":"30%",
                    "AwayConfidence":"70%"}]}

response = requests.post(url, data = data, auth=HTTPBasicAuth('guess365', 'er3p5eak97'), verify=False).text
```
## JSON參數

參數  | 用途
------------- | -------------
predlist | 每一筆預測
predlist-account  | 帳戶
predlist-password  | 密碼
predlist-GroupOptionCode  | 盤口編號
predlist-OptionCode  | 選擇方
predlist-EventCode  | 賽事編號
predlist-PredictType  | 預測類型('Forecast' or 'Selling')
predlist-HomeOdds  | 自訂主場賠率
predlist-AwayOdds  | 自訂客場賠率
predlist-HomeConfidence  | 自訂主場預測信心度
predlist-AwayConfidence  | 自訂客場預測信心度

<div style="page-break-after: always;"></div>

# 查詢盤口範例
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://192.168.0.223:5000/MatchEntryInfo/DateBetween/NBA/now~2022-4-29'

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
[Input:DateBetween] | 提供兩種輸入方式，'now~2022-3-29' 或 'any'。

<div style="page-break-after: always;"></div>

# 查詢預測結果範例
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://192.168.0.223:5000/PredictResults/adsads2323'

response = requests.get(url, auth=HTTPBasicAuth('guess365', 'er3p5eak97')).text
```
## URL參數
參數  | 用途
------------- | -------------
HTTPBasicAuth  | user='guess365', password='er3p5eak97'
URL 1 | http://192.168.0.223:5000/PredictResults/**[Input:accounts]**
URL 2 | http://192.168.0.223:5000/PredictResults/**[Input:accounts]**/**[Input:DateBetween]**
[Input:accounts] | 帳號，"MA890101,winwin666,adsads2323"。
[Input:DateBetween] | 提供兩種輸入方式，'now~2022-3-29' 或 'any'。
