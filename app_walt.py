from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import create_engine
from flask import Flask, request, jsonify, make_response
import json
import traceback
from datetime import datetime, timedelta, timezone
from flask_httpauth import HTTPBasicAuth
import pandas as pd
from flask_cors import CORS
import web_config
import requests, time
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote, quote_plus
import pyodbc

db = SQLAlchemy()
app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

server   = web_config.production().server
username = web_config.production().username
password = web_config.production().password
database = web_config.production().database
driver   = '/home/linuxbrew/.linuxbrew/lib/libtdsodbc.so'
port     = '1433'

odbc_str = 'DRIVER='+driver+';SERVER='+server+';PORT='+port+';DATABASE='+database+';UID='+username+';PWD='+password
connect_str = 'mssql+pyodbc:///?odbc_connect='+quote_plus(odbc_str)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_str
db.init_app(app)


users = [
    {'username': 'jake', 'password': generate_password_hash('000jk')} 
]
@auth.verify_password
def verify_password(username, password):
    for user in users:
        if user['username'] == username:
            if check_password_hash(user['password'], password):
                return True
    return False

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@app.route('/MatchEntryInfo/DateBetween/All/<DateBetween>', methods=['GET'])
@app.route('/MatchEntryInfo/DateBetween/<TournamentText>/<DateBetween>', methods=['GET'])
@app.route('/MatchEntryInfo/<EventCode>', methods=['GET'])
@auth.login_required
def getMatchEntryInfo(DateBetween=None,TournamentText = None, SourceCode = None ,EventCode = None):
    try:
        if request.method == 'GET' and not EventCode is None:
            sql = f"select MatchEntry.SportCode,MatchEntry.EventCode,MatchEntry.TournamentText,MatchEntry.MatchTime,MatchEntry.SourceCode,MatchEntry.HomeTeam,MatchEntry.AwayTeam,MatchEntry.CollectedTime,GroupOptionCode,OptionCode,OptionRate,SpecialBetValue  from MatchEntry " \
                  f"left join Odds on MatchEntry.EventCode = Odds.EventCode " \
                  f"where MatchEntry.EventCode = '{EventCode}' and MatchEntry.MatchTime >= '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}' "
            MatchEntry = db.engine.execute(sql).mappings().all()
            for idx in range(len(MatchEntry)):
                MatchEntry[idx] = dict(MatchEntry[idx])
            MatchEntry_df = pd.DataFrame(MatchEntry)
            # 整理賽事
            MatchEntrysOutput = []
            records = []
            for MatchEntry in MatchEntry:
                if MatchEntry['EventCode'] not in records:
                    MatchEntrysOutput.append(dict(EventCode=MatchEntry['EventCode'],
                                                    TournamentText=MatchEntry['TournamentText'],
                                                    MatchTime=MatchEntry['MatchTime'].strftime('%Y-%m-%d %H:%M:%S.000'),
                                                    SportCode=MatchEntry['SportCode'],
                                                    SourceCode=MatchEntry['SourceCode'],
                                                    HomeTeam=[MatchEntry['HomeTeam'],TeamNameCorrection(MatchEntry['HomeTeam'])],
                                                    AwayTeam=[MatchEntry['AwayTeam'],TeamNameCorrection(MatchEntry['AwayTeam'])],
                                                    odds= [] if MatchEntry_df[MatchEntry_df.EventCode == MatchEntry['EventCode']].loc[:,['GroupOptionCode','OptionCode','OptionRate','SpecialBetValue']].to_dict('records')[0]['GroupOptionCode']==None else MatchEntry_df[MatchEntry_df.EventCode == MatchEntry['EventCode']].loc[:,['GroupOptionCode','OptionCode','OptionRate','SpecialBetValue']].to_dict('records'),
                                                    CollectedTime=MatchEntry['CollectedTime'].strftime('%Y-%m-%d %H:%M:%S.000')))
                    records.append(MatchEntry['EventCode'])
            return jsonify({'response': MatchEntrysOutput})
        elif request.method == 'GET' and not DateBetween is None and TournamentText is None:
            if DateBetween == 'any':
                DatetimeTop, DatetimeBottom = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'),(datetime.now().astimezone(timezone(timedelta(hours=8)))+timedelta(days=7)).replace(hour=23,minute=59,second=59).strftime('%Y-%m-%d %H:%M:%S.000')
            else:
                DatetimeTop, DatetimeBottom = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'),DateBetween.split('~')[1].strip()+' 23:59:59.000'
            # 查詢賽事
            sql = f"Select MatchEntry.SportCode,MatchEntry.EventCode,MatchEntry.TournamentText,MatchEntry.MatchTime,MatchEntry.SourceCode,MatchEntry.HomeTeam,MatchEntry.AwayTeam,MatchEntry.CollectedTime,GroupOptionCode,OptionCode,OptionRate,SpecialBetValue  from MatchEntry " \
                  f"left join Odds on MatchEntry.EventCode = Odds.EventCode where Matchtime >= '{DatetimeTop}' and  Matchtime <= '{DatetimeBottom}' " \
                  f"order by Matchtime,HomeTeam,AwayTeam,MatchEntry.SourceCode desc"
            MatchEntrys = db.engine.execute(sql).mappings().all()
            for idx in range(len(MatchEntrys)):
                MatchEntrys[idx] = dict(MatchEntrys[idx]) # 將 Mapping 轉型為 dict
            MatchEntry_df = pd.DataFrame(MatchEntrys)
            # 整理賽事
            MatchEntrysOutput = []
            records = []
            for MatchEntry in MatchEntrys:
                if MatchEntry['EventCode'] not in records:
                    MatchEntrysOutput.append(dict(EventCode=MatchEntry['EventCode'],
                                                    TournamentText=MatchEntry['TournamentText'],
                                                    MatchTime=MatchEntry['MatchTime'].strftime('%Y-%m-%d %H:%M:%S.000'),
                                                    SportCode=MatchEntry['SportCode'],
                                                    SourceCode=MatchEntry['SourceCode'],
                                                    HomeTeam=[MatchEntry['HomeTeam'],TeamNameCorrection(MatchEntry['HomeTeam'])],
                                                    AwayTeam=[MatchEntry['AwayTeam'],TeamNameCorrection(MatchEntry['AwayTeam'])],
                                                    odds= [] if MatchEntry_df[MatchEntry_df.EventCode == MatchEntry['EventCode']].loc[:,['GroupOptionCode','OptionCode','OptionRate','SpecialBetValue']].to_dict('records')[0]['GroupOptionCode']==None else MatchEntry_df[MatchEntry_df.EventCode == MatchEntry['EventCode']].loc[:,['GroupOptionCode','OptionCode','OptionRate','SpecialBetValue']].to_dict('records'),
                                                    CollectedTime=MatchEntry['CollectedTime'].strftime('%Y-%m-%d %H:%M:%S.000')))
                    records.append(MatchEntry['EventCode'])
            return jsonify({'response': MatchEntrysOutput})
        elif request.method == 'GET' and not TournamentText is None:
            if DateBetween == 'any':
                DatetimeTop, DatetimeBottom = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), (datetime.now().astimezone(timezone(timedelta(hours=8))) + timedelta(days=7)).replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S.000')
            else:
                DatetimeTop, DatetimeBottom = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'),DateBetween.split('~')[1].strip()+' 23:59:59.000'
            # 查詢賽事
            sql = f"Select MatchEntry.SportCode,MatchEntry.EventCode,MatchEntry.TournamentText,MatchEntry.MatchTime,MatchEntry.SourceCode,MatchEntry.HomeTeam,MatchEntry.AwayTeam,MatchEntry.CollectedTime,GroupOptionCode,OptionCode,OptionRate,SpecialBetValue  from MatchEntry " \
                  f"left join Odds on MatchEntry.EventCode = Odds.EventCode where Matchtime >= '{DatetimeTop}' and  Matchtime <= '{DatetimeBottom}' and TournamentText = '{TournamentText}' " \
                  f"order by Matchtime,HomeTeam,AwayTeam,MatchEntry.SourceCode desc"
            MatchEntrys = db.engine.execute(sql).mappings().all()
            for idx in range(len(MatchEntrys)):
                MatchEntrys[idx] = dict(MatchEntrys[idx]) # 將 Mapping 轉型為 dict
            MatchEntry_df = pd.DataFrame(MatchEntrys)
            # 整理賽事
            MatchEntrysOutput = []
            records = []

            for MatchEntry in MatchEntrys:
                if MatchEntry['EventCode'] not in records:
                    MatchEntrysOutput.append(dict(EventCode=MatchEntry['EventCode'],
                                                    TournamentText=MatchEntry['TournamentText'],
                                                    MatchTime=MatchEntry['MatchTime'].strftime('%Y-%m-%d %H:%M:%S.000'),
                                                    SportCode=MatchEntry['SportCode'],
                                                    SourceCode=MatchEntry['SourceCode'],
                                                    HomeTeam=[MatchEntry['HomeTeam'],TeamNameCorrection(MatchEntry['HomeTeam'])],
                                                    AwayTeam=[MatchEntry['AwayTeam'],TeamNameCorrection(MatchEntry['AwayTeam'])],
                                                    odds= [] if MatchEntry_df[MatchEntry_df.EventCode == MatchEntry['EventCode']].loc[:,['GroupOptionCode','OptionCode','OptionRate','SpecialBetValue']].to_dict('records')[0]['GroupOptionCode']==None else MatchEntry_df[MatchEntry_df.EventCode == MatchEntry['EventCode']].loc[:,['GroupOptionCode','OptionCode','OptionRate','SpecialBetValue']].to_dict('records'),
                                                    CollectedTime=MatchEntry['CollectedTime'].strftime('%Y-%m-%d %H:%M:%S.000')))
                    records.append(MatchEntry['EventCode'])
            return jsonify({'response': MatchEntrysOutput})
    except:
        return jsonify({'response': [{'Error Info': traceback.format_exc()}]})

@app.route('/PredictResults/<accounts>/<DateBetween>', methods=['GET'])
@app.route('/PredictResults/<accounts>', methods=['GET'])
@auth.login_required
def get_PredictResults(accounts=None,DateBetween=None):
    try:
        if DateBetween==None:
            DatetimeTop, DatetimeBottom = (datetime.now().astimezone(timezone(timedelta(hours=8))) - timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S.000'), (datetime.now().astimezone(timezone(timedelta(hours=8))) - timedelta(
            days=1)).replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S.000')
        else:
            DatetimeTop, DatetimeBottom = DateBetween.split('~')[0].strip() + ' 00:00:00.000', DateBetween.split('~')[1].strip() + ' 23:59:59.000'



        accounts = accounts.split(',')
        sql = f'''SELECT c.SportCode, d.member, a.EventCode, c.HomeTeam, c.AwayTeam, a.TournamentText, a.GroupOptionCode, a.PredictTeam, a.OptionCode, c.MatchTime, b.Results FROM [dbo].[PredictMatch] as a
                        inner join PredictResults as b on a.id=b.Predict_id
                        inner join MatchEntry as c on c.EventCode=a.EventCode
                        inner join UserMember  as d on d.UserId=a.UserId
                        where c.MatchTime>='{DatetimeTop}' and c.MatchTime<'{DatetimeBottom}'
                        and d.member in ({str(accounts).replace('[','').replace(']','')}) and gameType='Selling'
                        order by a.TournamentText,  d.member '''
        PredictResults = db.engine.execute(sql).mappings().all()
        for idx in range(len(PredictResults)):
            PredictResults[idx] = dict(PredictResults[idx])

        message = ''
        if len(PredictResults)>0:
            TournamentTexts = list(set(pd.DataFrame(PredictResults)['TournamentText']))

            for TournamentText in TournamentTexts:
                    message+='👏'+TournamentText+'\n\n'
                    message+='賽事日期|主隊 客隊|盤口|預測|結果\n\n'
                    for PredictResult in PredictResults:
                        if PredictResult['TournamentText'] == TournamentText:
                            HomeTeam, AwayTeam = TeamNameCorrection(PredictResult['HomeTeam']), TeamNameCorrection(PredictResult['AwayTeam'])
                            message+=f"{PredictResult['MatchTime'].strftime('%m%d ')}" \
                                     f"{HomeTeam}🆚{AwayTeam}" \
                                     f"|{get_TypeCname(PredictResult['SportCode'],PredictResult['GroupOptionCode'])}" \
                                     f"|{Mapping_OptionCode(PredictResult['OptionCode'],PredictResult['SportCode'],PredictResult['GroupOptionCode'],HomeTeam,AwayTeam)}" \
                                     f"{'✅' if PredictResult['Results']=='Y' else '❎'}\n\n"

        print(message)
        return jsonify({'responese': message })
    except:
        return jsonify({'response':traceback.format_exc()})

@app.route('/PredictMatchEntrys/', methods=['POST'])
@auth.login_required
def PredictMatchEntrys():
    try:
        err_msg = ""
        messages = ""
        message = f"{datetime.now().astimezone(timezone(timedelta(hours=8)))}[%s]\n" \
                  "{'MatchTime':'%s'," \
                  " 'Odds':['%s','%s']," \
                  " 'Confidence':['%s','%s']," \
                  " 'TournamentText':'%s'," \
                  " 'HomeTeam':'%s'," \
                  " 'AwayTeam':'%s'," \
                  " 'GroupOptionName':'%s'," \
                  " 'OptionCode':'%s'}\n"

        # 取得驗證資料
        auth_username = auth.username()
        client_ip = request.remote_addr
        GameType = ['Forecast', 'Selling']
        data = request.get_json()
        # 取得預測列表
        for idx, pred in enumerate(data['predlist']):
            try:
                # 取得每一項預測
                account = pred['account']
                password = pred['password']
                GroupOptionCode = pred['GroupOptionCode']
                OptionCode = pred['OptionCode']
                EventCode = pred['EventCode']
                predict_type = pred['predict_type']
                input_HomeOdds = pred['HomeOdds']
                input_AwayOdds = pred['AwayOdds']
                HomeConfidence = pred['HomeConfidence']
                AwayConfidence = pred['AwayConfidence']
                #檢查盤口是否存在
                MatchEntry = dict(db.engine.execute(f"select * from MatchEntry where EventCode = '{EventCode}'  ").mappings().one()) #and MatchTime >= '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'
                Odds = dict(db.engine.execute(f"select * from Odds where EventCode = '{EventCode}' and GroupOptionCode='{GroupOptionCode}' and OptionCode='{OptionCode}' ").mappings().one())
                UserId = get_UserId(account,password)
                level = get_UserMemberLevel(UserId)
                # 檢查 帳號密碼是否存在
                if UserId is None:
                    err_msg += f'data[{idx}] Account {account} does not exist. data=({pred})\n'
                    continue
                # 檢查 predict_type是否為指定值
                if predict_type is None or  predict_type not in GameType:
                    err_msg += f"data[{idx}] Predict type please enter 'Forecast' or 'Selling' option. data=({pred})\n"
                    continue
                # 預測
                if predict_type == 'Selling':
                    if int(level) not in (1, 2, 3, 6):
                        err_msg += f'data[{idx}] Account {account} non-selling member. data=({pred})\n'
                        continue

                    isForcast, Forecast_result = isPredictMacthExists(UserId, EventCode, GroupOptionCode, 'Forecast')
                    isSelling, Selling_result = isPredictMacthExists(UserId, EventCode, GroupOptionCode, 'Selling')
                    if not isForcast:
                        for gametype in GameType:
                            predict_sql = f'''INSERT INTO [dbo].[PredictMatch] ([UserId],[SportCode],[EventType],[EventCode],[TournamentCode],[TournamentText],[GroupOptionCode],[GroupOptionName],[PredictTeam],[OptionCode],[SpecialBetValue],[OptionRate],[status],[gameType],[MarketType],[PredictDatetime],[CreatedTime]) VALUES('{UserId}','{MatchEntry['SportCode']}', '{'0'}','{MatchEntry['EventCode']}', '{MatchEntry['SportTournamentCode']}','{MatchEntry['TournamentText']}','{Odds['GroupOptionCode']}','{get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])}','{Mapping_PredictTeamName(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'], MatchEntry['HomeTeam'], MatchEntry['AwayTeam'])}','{Odds['OptionCode']}','{Odds['SpecialBetValue']}','{Odds['OptionRate']}','{'2'}','{gametype}','{"international" if MatchEntry['SourceCode'] == "Bet365" else "sportslottery"}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}') '''
                            db.engine.execute(predict_sql)
                        add_userbouns(UserId)
                        HomeTeam, AwayTeam = TeamNameCorrection(MatchEntry['HomeTeam']), TeamNameCorrection(MatchEntry['AwayTeam'])

                        m = message%(idx,
                                     MatchEntry['MatchTime'].strftime('%m-%d %H:%M'),
                                     input_HomeOdds,input_AwayOdds,
                                     HomeConfidence,AwayConfidence,
                                     MatchEntry['TournamentText'],
                                     HomeTeam,AwayTeam,
                                     get_TypeCname(MatchEntry['SportCode'], Odds['GroupOptionCode']),
                                     Mapping_OptionCode(Odds['OptionCode'], MatchEntry['SportCode'],Odds['GroupOptionCode'], HomeTeam, AwayTeam))

                        messages += m+"------------------\n"
                        send_JANDIMessage(m, client_ip, auth_username, '[預+賣]')


                    elif isForcast and not isSelling:
                        if Forecast_result['OptionCode'] == Odds['OptionCode']:
                            predict_sql = f'''INSERT INTO [dbo].[PredictMatch] ([UserId],[SportCode],[EventType],[EventCode],[TournamentCode],[TournamentText],[GroupOptionCode],[GroupOptionName],[PredictTeam],[OptionCode],[SpecialBetValue],[OptionRate],[status],[gameType],[MarketType],[PredictDatetime],[CreatedTime]) VALUES('{UserId}','{MatchEntry['SportCode']}', '{'0'}','{MatchEntry['EventCode']}', '{MatchEntry['SportTournamentCode']}','{MatchEntry['TournamentText']}','{Odds['GroupOptionCode']}','{get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])}','{Mapping_PredictTeamName(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'], MatchEntry['HomeTeam'], MatchEntry['AwayTeam'])}','{Odds['OptionCode']}','{Odds['SpecialBetValue']}','{Odds['OptionRate']}','{'2'}','{GameType[-1]}','{"international" if MatchEntry['SourceCode'] == "Bet365" else "sportslottery"}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}') '''
                            db.engine.execute(predict_sql)
                            HomeTeam, AwayTeam = TeamNameCorrection(MatchEntry['HomeTeam']), TeamNameCorrection(MatchEntry['AwayTeam'])
                            m = message % (idx,
                                           MatchEntry['MatchTime'].strftime('%m-%d %H:%M'),
                                           input_HomeOdds, input_AwayOdds,
                                           HomeConfidence, AwayConfidence,
                                           MatchEntry['TournamentText'],
                                           HomeTeam, AwayTeam,
                                           get_TypeCname(MatchEntry['SportCode'], Odds['GroupOptionCode']),
                                           Mapping_OptionCode(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'],HomeTeam, AwayTeam))
                            messages += m + "------------------\n"
                            send_JANDIMessage(m, client_ip, auth_username, '[預>賣]')
                        else:
                            err_msg += f'data[{idx}] Forecasts and Sellings must be the same. data=({pred})\n'
                            continue
                    else:
                        err_msg += f'data[{idx}] Have repeated sellings. data=({pred})\n'
                        continue

                elif predict_type == 'Forecast':
                    isForcast, Forecast_result = isPredictMacthExists(UserId, EventCode, GroupOptionCode, 'Forecast')
                    if isForcast:
                        err_msg += f'data[{idx}] Have repeated forecasts. data=({pred})\n'
                        continue

                    elif not isForcast:
                        predict_sql = f'''INSERT INTO [dbo].[PredictMatch] ([UserId],[SportCode],[EventType],[EventCode],[TournamentCode],[TournamentText],[GroupOptionCode],[GroupOptionName],[PredictTeam],[OptionCode],[SpecialBetValue],[OptionRate],[status],[gameType],[MarketType],[PredictDatetime],[CreatedTime]) VALUES('{UserId}','{MatchEntry['SportCode']}', '{'0'}','{MatchEntry['EventCode']}', '{MatchEntry['SportTournamentCode']}','{MatchEntry['TournamentText']}','{Odds['GroupOptionCode']}','{get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])}','{Mapping_PredictTeamName(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'], MatchEntry['HomeTeam'], MatchEntry['AwayTeam'])}','{Odds['OptionCode']}','{Odds['SpecialBetValue']}','{Odds['OptionRate']}','{'2'}','{GameType[0]}','{"international" if MatchEntry['SourceCode'] == "Bet365" else "sportslottery"}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}') '''
                        db.engine.execute(predict_sql)
                        add_userbouns(UserId)
                        HomeTeam, AwayTeam = TeamNameCorrection(MatchEntry['HomeTeam']), TeamNameCorrection(MatchEntry['AwayTeam'])

                        m = message % (idx,
                                       MatchEntry['MatchTime'].strftime('%m-%d %H:%M'),
                                       input_HomeOdds, input_AwayOdds,
                                       HomeConfidence, AwayConfidence,
                                       MatchEntry['TournamentText'],
                                       HomeTeam, AwayTeam,
                                       get_TypeCname(MatchEntry['SportCode'], Odds['GroupOptionCode']),
                                       Mapping_OptionCode(Odds['OptionCode'], MatchEntry['SportCode'],Odds['GroupOptionCode'], HomeTeam, AwayTeam))
                        messages += m + "------------------\n"
                        send_JANDIMessage(m, client_ip, auth_username, '[預]')

            except KeyError:
                traceback.print_exc()
                err_msg += f'data[{idx}] JSON data parameter incorrect. data=({pred})\n'
                continue
            except:
                traceback.print_exc()
                err_msg += f"data[{idx}] MatchEntry ({EventCode}) has no GroupOptionCode ({GroupOptionCode}). data=({pred})\n"
                continue

        print(messages+'err_msg:\n'+err_msg)
        if messages != "":
            return jsonify({'PredictSQL': messages+'err_msg:\n'+err_msg})
        else:
            return jsonify({'response':"Prediction failed for all input data.\n"+'err_msg:\n'+err_msg})

    except:
        return jsonify({'response': [{'Error Info': traceback.format_exc()}]})


@app.route('/PredictMatchEntry/', methods=['POST'])
@auth.login_required
def PredictMatchEntry():
    try:
        auth_username = auth.username()
        client_ip = request.remote_addr
        account = request.form.get('account')
        password = request.form.get('password')
        GroupOptionCode = request.form.get('GroupOptionCode')
        OptionCode = request.form.get('OptionCode')
        EventCode = request.form.get('EventCode')
        predict_type = request.form.get('PredictType')
        GameType = ['Forecast','Selling']
        if request.method == 'POST' and not account is None and not password is None \
                and not GroupOptionCode is None and not OptionCode is None  and not EventCode is None:
            MatchEntry = dict(db.engine.execute(f"select * from MatchEntry where EventCode = '{EventCode}' and MatchTime >= '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'  ").mappings().one())
            Odds = dict(db.engine.execute(f"select * from Odds where EventCode = '{EventCode}' and GroupOptionCode='{GroupOptionCode}' and OptionCode='{OptionCode}' ").mappings().one())
            UserId = get_UserId(account,password)
            level = get_UserMemberLevel(UserId)
            if UserId is None:
                return jsonify({'response':f'Account {account} does not exist.'})
            if predict_type is None or  predict_type not in GameType:
                return jsonify({'response':f"Predict type please enter 'Forecast' or 'Selling' option."})

            if predict_type == 'Selling':
                if int(level) not in (1,2,3,6):
                    return jsonify({'response': f'Account {account} non-selling member.'})

                isForcast,Forecast_result = isPredictMacthExists(UserId,EventCode,GroupOptionCode,'Forecast')
                isSelling,Selling_result = isPredictMacthExists(UserId,EventCode,GroupOptionCode,'Selling')
                if not isForcast:
                    for gametype in GameType:
                        predict_sql = f'''INSERT INTO [dbo].[PredictMatch] ([UserId],[SportCode],[EventType],[EventCode],[TournamentCode],[TournamentText],[GroupOptionCode],[GroupOptionName],[PredictTeam],[OptionCode],[SpecialBetValue],[OptionRate],[status],[gameType],[MarketType],[PredictDatetime],[CreatedTime]) VALUES('{UserId}','{MatchEntry['SportCode']}', '{'0'}','{MatchEntry['EventCode']}', '{MatchEntry['SportTournamentCode']}','{MatchEntry['TournamentText']}','{Odds['GroupOptionCode']}','{get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])}','{Mapping_PredictTeamName(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'], MatchEntry['HomeTeam'], MatchEntry['AwayTeam'])}','{Odds['OptionCode']}','{Odds['SpecialBetValue']}','{Odds['OptionRate']}','{'2'}','{gametype}','{"international" if MatchEntry['SourceCode'] == "Bet365" else "sportslottery"}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}') '''
                        db.engine.execute(predict_sql)
                    add_userbouns(UserId)
                    message = f"比賽資訊：\n" \
                              f"EventCode = {EventCode} \n" \
                              f"TournamentText = {MatchEntry['TournamentText']} \n" \
                              f"{MatchEntry['HomeTeam']} vs {MatchEntry['AwayTeam']} \n" \
                              f"預測資訊：\n" \
                              f"GroupOptionName = {get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])} \n" \
                              f"GroupOptionCode = {Odds['GroupOptionCode']}\n" \
                              f"OptionCode = {Odds['OptionCode']}\n" \
                              f"SourceCode = {MatchEntry['SourceCode']}\n"
                    send_JANDIMessage(message, client_ip, auth_username,'[預+賣]')
                    return jsonify({'PredictSQL': message})
                elif isForcast and not isSelling:
                    if Forecast_result['OptionCode']==Odds['OptionCode']:
                        predict_sql = f'''INSERT INTO [dbo].[PredictMatch] ([UserId],[SportCode],[EventType],[EventCode],[TournamentCode],[TournamentText],[GroupOptionCode],[GroupOptionName],[PredictTeam],[OptionCode],[SpecialBetValue],[OptionRate],[status],[gameType],[MarketType],[PredictDatetime],[CreatedTime]) VALUES('{UserId}','{MatchEntry['SportCode']}', '{'0'}','{MatchEntry['EventCode']}', '{MatchEntry['SportTournamentCode']}','{MatchEntry['TournamentText']}','{Odds['GroupOptionCode']}','{get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])}','{Mapping_PredictTeamName(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'], MatchEntry['HomeTeam'], MatchEntry['AwayTeam'])}','{Odds['OptionCode']}','{Odds['SpecialBetValue']}','{Odds['OptionRate']}','{'2'}','{GameType[-1]}','{"international" if MatchEntry['SourceCode'] == "Bet365" else "sportslottery"}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}') '''
                        db.engine.execute(predict_sql)
                        message = f"比賽資訊：\n" \
                                  f"EventCode = {EventCode} \n" \
                                  f"TournamentText = {MatchEntry['TournamentText']} \n" \
                                  f"{MatchEntry['HomeTeam']} vs {MatchEntry['AwayTeam']} \n" \
                                  f"預測資訊：\n" \
                                  f"GroupOptionName = {get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])} \n" \
                                  f"GroupOptionCode = {Odds['GroupOptionCode']}\n" \
                                  f"OptionCode = {Odds['OptionCode']}\n" \
                                  f"SourceCode = {MatchEntry['SourceCode']}\n"
                        send_JANDIMessage(message, client_ip, auth_username, '[預>賣]')
                        return jsonify({'PredictSQL': message})
                    else:
                        return jsonify({'response': [{'Error Info': 'Forecasts and Sellings must be the same.'}]})
                else:
                    return jsonify({'response': [{'Error Info': 'Have repeated sellings.'}]})
            elif predict_type == 'Forecast':
                isForcast,Forecast_result = isPredictMacthExists(UserId,EventCode,GroupOptionCode,'Forecast')
                if  isForcast:
                    return jsonify({'response': [{'Error Info': 'Have repeated forecasts.'}]})
                elif not isForcast:
                    predict_sql = f'''INSERT INTO [dbo].[PredictMatch] ([UserId],[SportCode],[EventType],[EventCode],[TournamentCode],[TournamentText],[GroupOptionCode],[GroupOptionName],[PredictTeam],[OptionCode],[SpecialBetValue],[OptionRate],[status],[gameType],[MarketType],[PredictDatetime],[CreatedTime]) VALUES('{UserId}','{MatchEntry['SportCode']}', '{'0'}','{MatchEntry['EventCode']}', '{MatchEntry['SportTournamentCode']}','{MatchEntry['TournamentText']}','{Odds['GroupOptionCode']}','{get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])}','{Mapping_PredictTeamName(Odds['OptionCode'], MatchEntry['SportCode'], Odds['GroupOptionCode'], MatchEntry['HomeTeam'], MatchEntry['AwayTeam'])}','{Odds['OptionCode']}','{Odds['SpecialBetValue']}','{Odds['OptionRate']}','{'2'}','{GameType[0]}','{"international" if MatchEntry['SourceCode'] == "Bet365" else "sportslottery"}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}','{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")}') '''
                    db.engine.execute(predict_sql)
                    add_userbouns(UserId)
                    message = f"比賽資訊：\n" \
                              f"EventCode = {EventCode} \n" \
                              f"TournamentText = {MatchEntry['TournamentText']} \n" \
                              f"{MatchEntry['HomeTeam']} vs {MatchEntry['AwayTeam']} \n" \
                              f"預測資訊：\n" \
                              f"GroupOptionName = {get_GroupOptionName(MatchEntry['SportCode'], Odds['GroupOptionCode'])} \n" \
                              f"GroupOptionCode = {Odds['GroupOptionCode']}\n" \
                              f"OptionCode = {Odds['OptionCode']}\n" \
                              f"SourceCode = {MatchEntry['SourceCode']}\n"
                    send_JANDIMessage(message, client_ip, auth_username, '[預]')
                    return jsonify({'PredictSQL': message})
        else:
            return jsonify({'response': [{'Error Info': 'JSON data parameter incorrect '}]})
    except Exception:
        traceback.print_exc()
        return jsonify({'response': [{'Error Info': f"MatchEntry ({EventCode}) has no GroupOptionCode ({GroupOptionCode})"}]})

def Mapping_PredictTeamName(OptionCode,SportCode,GroupOptionCode,HomeTeam,AwayTeam):
    if SportCode == '1' and GroupOptionCode in ('55'):
        texts = [OptionCode.split('/')[0].strip(), OptionCode.split('/')[1].strip()]
        if not texts[0] == 'Draw' and not texts[1] == 'Draw':
            PredictTeam = texts[1]
        elif not texts[0] == 'Draw' and texts[1] == 'Draw':
            PredictTeam = texts[0]
        elif texts[0] == 'Draw' and not texts[1] == 'Draw':
            PredictTeam = texts[1]
        return PredictTeam.replace(r"'", r"''")
    else:
        if OptionCode == '1':
            PredictTeam = HomeTeam
        elif OptionCode == '2':
            PredictTeam = AwayTeam
        else:
            PredictTeam = ''
        return PredictTeam.replace(r"'", r"''")

def Mapping_OptionCode(OptionCode,SportCode,GroupOptionCode,HomeTeam,AwayTeam):
    if SportCode == '1' and GroupOptionCode in ('55'):
        texts = [OptionCode.split('/')[0].strip(), OptionCode.split('/')[1].strip()]
        if not texts[0] == 'Draw' and not texts[1] == 'Draw':
            return '平手'
        elif not texts[0] == 'Draw' and texts[1] == 'Draw':
            return HomeTeam+'/平手'
        elif texts[0] == 'Draw' and not texts[1] == 'Draw':
            return '平手/'+AwayTeam
    else:
        if OptionCode == '1':
            return HomeTeam
        elif OptionCode == '2':
            return AwayTeam
        elif OptionCode == 'Over':
            return '大分'
        elif OptionCode == 'Under':
            return '小分'
    return None

def get_GroupOptionName(SportCode, GroupOptionCode):
    result = dict(db.engine.execute(f"select * from [GroupOptionCode] where SportCode = '{SportCode}' and GroupOptionCode1 = '{GroupOptionCode}' ").mappings().one())
    return result['Type']

def get_UserId(account,password):
    try:
        result = dict(db.engine.execute(f"select * from UserMember where member = '{account}' and Password = '{password}' ").mappings().one())
        return result['UserId']
    except:
        return None

def get_UserMemberLevel(UserId):
    try:
        result = dict(db.engine.execute(f"select * from UserMember where UserId = '{UserId}' ").mappings().one())
        return result['level']
    except:
        return None

def TeamNameCorrection(Eng_TeamName):
    Eng_TeamName = Eng_TeamName.replace(r"'", r"''")
    sql = f"SELECT name FROM teams where team = '{Eng_TeamName}' ;"
    results = db.engine.execute(sql).mappings().all()
    if len(results)>0:
        return results[0]['name']
    else:
        return ''

def send_JANDIMessage(text,IP,auth_username,gameType):
    webhook_url = 'https://wh.jandi.com/connect-api/webhook/25729815/70b1717ca561d9964afe8027643c4c65'

    jandi_data = {"body": text,
                  "connectColor": "#e31724",
                  "connectInfo": [
                      {
                          "title": f"有員工做{gameType}囉!!，來源IP={IP}，用戶={auth_username}"
                      }]
                 }
    response = requests.post(webhook_url, data=json.dumps(jandi_data),headers={'Content-type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )



def isPredictMacthExists(UserId,EventCode,GroupOptionCode,gametype):
    sql = f'''SELECT * FROM [PredictMatch] where UserId = '{UserId}' and EventCode = '{EventCode}' and GroupOptionCode = '{GroupOptionCode}' and gameType = '{gametype}' '''
    results = db.engine.execute(sql).mappings().all()
    for idx in range(len(results)):
        results[idx] = dict(results[idx])  # 將 Mapping 轉型為 dict
    if len(results)>0:
        return True,results[0]
    else:
        return False,[]

def get_TypeCname(SportCode,GroupOptionCode):
    sql = f'''SELECT [SportCode],[Type],[Type_cname],[Play_Name],[GroupOptionCode1] FROM [dbo].[GroupOptionCode] 
                where [SportCode]='{SportCode}' and  GroupOptionCode1='{GroupOptionCode}' '''
    results = db.engine.execute(sql).mappings().all()
    for idx in range(len(results)):
        results[idx] = dict(results[idx])  # 將 Mapping 轉型為 dict
    if len(results)>0:
        return results[0]['Type_cname']
    else:
        return None

def add_userbouns(UserId):
    predict_num = 1

    Modify_dd = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S.000")
    start_dd = datetime.now().astimezone(timezone(timedelta(hours=8))).replace(hour=0, minute=0,second=0,microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")
    end_dd = datetime.now().astimezone(timezone(timedelta(hours=8))).replace(hour=23, minute=59,second=59,microsecond=0).strftime("%Y-%m-%d %H:%M:%S.000")

    sql = f'''SELECT [UserId],[bonus],[Level],[start_dd],[end_dd],[Modify_dd] FROM [dbo].[UserBonus]  WHERE UserId = '{UserId}' AND start_dd = '{start_dd}' '''
    results = db.engine.execute(sql).mappings().all()

    if len(results)>0:
        ori_predict_num = int(results[0]['bonus'])
        predict_num += ori_predict_num

    if predict_num >=10 and predict_num<20:
        Level= '銅'
    elif predict_num >=20 and predict_num<30:
        Level = '銀'
    elif predict_num >=30 and predict_num<50:
        Level = '金'
    elif predict_num >=50 and predict_num<60:
        Level = '白金'
    elif predict_num >= 60 and predict_num<70:
        Level = '鑽石'
    elif predict_num >= 70:
        Level = '菁英'
    else:
        Level = '無'

    if len(results)>0:
        update_sql = f'''UPDATE [dbo].[UserBonus] SET [bonus]='{float(predict_num):.2f}',[Level]=N'{Level}',[start_dd]='{start_dd}',[end_dd]='{end_dd}',[Modify_dd]='{Modify_dd}' WHERE UserId = '{UserId}' AND start_dd = '{start_dd}' '''
        print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y/%m/%d %H:%M:%S'), '-' * 10,'執行', update_sql)
        db.engine.execute(update_sql)
    else:
        insert_sql = f'''INSERT INTO [dbo].[UserBonus]([UserId],[bonus],[Level],[start_dd],[end_dd],[Modify_dd])VALUES('{UserId}','{float(predict_num):.2f}',N'{Level}','{start_dd}','{end_dd}','{Modify_dd}')'''
        print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y/%m/%d %H:%M:%S'), '-' * 10,'執行', insert_sql)
        db.engine.execute(insert_sql)

if __name__ == "__main__":
    app.run('0.0.0.0',debug=True)

