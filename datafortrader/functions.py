from smartapi import SmartConnect
import pandas as pd
from datetime import datetime, timedelta
import credentials
import requests
import numpy as np
from time import time, sleep
from talib.abstract import *
import threading
import warnings
warnings.filterwarnings('ignore')


SYMBOL_LIST = ['DCM']
TRADED_SYMBOL = []
timeFrame = 60 + 5 #5 sec coz dealy repsone of historical API

def place_order(token,symbol,qty,buy_sell,ordertype,price,variety= 'NORMAL',exch_seg='NSE',triggerprice=0):
    try:
        orderparams = {
            "variety": variety,
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": buy_sell,
            "exchange": exch_seg,
            "ordertype": ordertype,
            "producttype": "DELIVERY",
            "duration": "DAY",
            "price": price,
            "squareoff": "0",
            "stoploss": "0",
            "quantity": qty,
            "triggerprice":triggerprice
            }
        orderId=credentials.SMART_API_OBJ.placeOrder(orderparams)
        print("The order id is: {}".format(orderId))
    except Exception as e:
        print("Order placement failed: {}".format(e.message))

def intializeSymbolTokenMap():
    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    d = requests.get(url).json()
    global token_df
    token_df = pd.DataFrame.from_dict(d)
    token_df['expiry'] = pd.to_datetime(token_df['expiry'])
    token_df = token_df.astype({'strike': float})
    credentials.TOKEN_MAP = token_df

def getTokenInfo (symbol, exch_seg ='NSE',instrumenttype='OPTIDX',strike_price = '',pe_ce = 'CE'):
    df = credentials.TOKEN_MAP
    strike_price = strike_price*100
    if exch_seg == 'NSE':
        eq_df = df[(df['exch_seg'] == 'NSE') & (df['symbol'].str.contains('EQ')) ]
        return eq_df[eq_df['name'] == symbol]
#     elif exch_seg == 'NFO' and ((instrumenttype == 'FUTSTK') or (instrumenttype == 'FUTIDX')):
#         return df[(df['exch_seg'] == 'NFO') & (df['instrumenttype'] == instrumenttype) & (df['name'] == symbol)].sort_values(by=['expiry'])
#     elif exch_seg == 'NFO' and (instrumenttype == 'OPTSTK' or instrumenttype == 'OPTIDX'):
#         return df[(df['exch_seg'] == 'NFO') & (df['instrumenttype'] == instrumenttype) & (df['name'] == symbol) & (df['strike'] == strike_price) & (df['symbol'].str.endswith(pe_ce))].sort_values(by=['expiry'])


def calculate_inidcator(res_json):
    columns = ['timestamp','O','H','L','C','V']
    df = pd.DataFrame(res_json['data'], columns=columns)
    df['timestamp'] = pd.to_datetime(df['timestamp'],format = '%Y-%m-%dT%H:%M:%S')
    df['EMA'] = EMA(df.C, timeperiod=20)
    df['RSI'] = RSI(df.C, timeperiod=14)
    df['ATR'] = ATR(df.H, df.L, df.C, timeperiod=20)
    df['CROSS_UP'] = df['CROSS_DOWN'] =df['RSI_UP'] = 0
    df = df.round(decimals=2)
    
    for i in range(20,len(df)):
        if df['C'][i-1]<= df['EMA'][i-1] and df['C'][i] > df['EMA'][i]:
            df['CROSS_UP'][i] = 1
        if df['C'][i-1] >= df['EMA'][i-1] and df['C'][i] < df['EMA'][i]:
            df['CROSS_DOWN'][i] = 1
        if df['RSI'][i] > 50 : 
            df['RSI_UP'][i] = 1 
   
#     print(df.tail(10))
    return df

def calculate_bd_inidcator(res_json):
    columns = ['timestamp','O','H','L','C','V']
    df = pd.DataFrame(res_json['data'], columns=columns)
    df['timestamp'] = pd.to_datetime(df['timestamp'],format = '%Y-%m-%dT%H:%M:%S')
#     df['EMA'] = EMA(df.C, timeperiod=20)
    df['upperband'], df['middleband'], df['lowerband'] = BBANDS(df.C, timeperiod=5, nbdevup=20.0, nbdevdn=2.0, matype=0)
    df['RSI'] = RSI(df.C, timeperiod=14)
    df['ATR'] = ATR(df.H, df.L, df.C, timeperiod=20)
    df['CROSS_UP'] = df['CROSS_DOWN'] =df['RSI_UP'] = 0
    df = df.round(decimals=2)
    
    # for i in range(20,len(df)):
    #     if ( df['upperband'][i-1]-df['C'][i-1] in range(0,1)) and ( df['upperband'][i]-df['C'][i] in range(0,1)):
    #         df['CROSS_UP'][i] = 1
    #     if ( df['lowerband'][i-1]-df['C'][i-1] in range(0,1)) and ( df['lowerband'][i]-df['C'][i] in range(0,1)):
    #         df['CROSS_DOWN'][i] = 1
    #     if df['RSI'][i] > 50 : 
    #         df['RSI_UP'][i] = 1 
    for i in range(20,len(df)):
        if ( df['upperband'][i-1]-df['C'][i-1] <=0.5 )and ( df['upperband'][i]-df['C'][i] <=0.5):
            df['CROSS_UP'][i] = 1
        if ( df['lowerband'][i-1]-df['C'][i-1]<=0.5) and ( df['lowerband'][i]-df['C'][i] <=0.5):
            df['CROSS_DOWN'][i] = 1
        if df['RSI'][i] > 50 : 
            df['RSI_UP'][i] = 1             
   
    print(df.tail(10))
    return df


def getHistoricalAPI(token,interval= 'ONE_MINUTE'):
    to_date= datetime.now()
    from_date = to_date - timedelta(days=5)
    from_date_format = from_date.strftime("%Y-%m-%d %H:%M")
    to_date_format = to_date.strftime("%Y-%m-%d %H:%M")
    try:
        historicParam={
        "exchange": "NSE",
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date_format, 
        "todate": to_date_format
        }
        candel_json  = credentials.SMART_API_OBJ.getCandleData(historicParam)
        return candel_json
    except Exception as e:
        print("Historic Api failed: {}".format(e.message))

def checkSingnal():
    start = time()
    global TRADED_SYMBOL
    
    for symbol in SYMBOL_LIST :
        if symbol not in TRADED_SYMBOL:
            tokenInfo = getTokenInfo(symbol).iloc[0]
            token = tokenInfo['token']
            symbol = tokenInfo['symbol']
#             print(symbol, token)
            candel_df = getHistoricalAPI(token)
            if candel_df is not None :
                latest_candel = candel_df.iloc[-1]
                if latest_candel['CROSS_UP'] == 1 and latest_candel['RSI_UP'] ==1:
                   
                    ltp = latest_candel['C']
                    SL = ltp -  2*latest_candel['ATR']
                    target = ltp + 5*latest_candel['ATR']
                    qty = 1   #qunatity to trade
                    
                    # res1= place_order(token,symbol,qty,'BUY','MARKET',0) #buy order
                    candel_df.tail(10)
#                     res2 = place_order(token,symbol,qty,'SELL','STOPLOSS_MARKET',0,variety='STOPLOSS',triggerprice= SL) #SL order
#                     res3 = place_order(token,symbol,qty,'SELL','LIMIT',target) #taget order
#                     print(res1, res2 , res3)
                    print(f'Order Placed for {symbol} LTP={ltp} SL={SL}  TGT={target} QTY={qty} at {datetime.now()}')
                    TRADED_SYMBOL.append(symbol)


    interval = timeFrame - (time()-start)  
#     print(f'interval is {interval} and time now {datetime.now()}')
    threading.Timer(interval, checkSingnal).start()



if __name__ == '__main__':
    intializeSymbolTokenMap()
    obj=SmartConnect(api_key=credentials.API_KEY)
    data = obj.generateSession(credentials.USER_NAME,credentials.PWD)
    credentials.SMART_API_OBJ = obj
   
    interval = timeFrame - datetime.now().second
    print(f"Code run after {interval} sec")
    sleep(interval)
    checkSingnal()

   
