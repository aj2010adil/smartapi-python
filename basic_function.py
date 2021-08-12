
from decouple import config
from smartapi import webSocket
ClientID = config('ClientID')
PASSWORD = config('PASSWORD')
AppType = config('AppType')
APIKey = config('APIKey')
SecretKey = config('SecretKey')


# package import statement
from smartapi import SmartConnect #or from smartapi.smartConnect import SmartConnect
# import smartapi.smartExceptions(for smartExceptions)

#create object of call
obj=SmartConnect(api_key=APIKey)

#login api call

data = obj.generateSession(ClientID,PASSWORD)
refreshToken= data['data']['refreshToken']

def fetch_the_feedtoken(obj):
    feedToken=obj.getfeedToken()
    return feedToken

def fetch_User_Profile(obj):
    userProfile= obj.getProfile(refreshToken)
    return userProfile

def place_order(obj):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": "SBIN-EQ",
            "symboltoken": "3045",
            "transactiontype": "BUY",
            "exchange": "NSE",
            "ordertype": "LIMIT",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "19500",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": "1"
            }
        orderId=obj.placeOrder(orderparams)
        print("The order id is: {}".format(orderId))
    except Exception as e:
        print("Order placement failed: {}".format(e.message))
    return orderId,orderparams

def gtt_rule_creation():
    try:
        gttCreateParams={
                "tradingsymbol" : "SBIN-EQ",
                "symboltoken" : "3045",
                "exchange" : "NSE", 
                "producttype" : "MARGIN",
                "transactiontype" : "BUY",
                "price" : 100000,
                "qty" : 10,
                "disclosedqty": 10,
                "triggerprice" : 200000,
                "timeperiod" : 365
            }
        rule_id=obj.gttCreateRule(gttCreateParams)
        print("The GTT rule id is: {}".format(rule_id))
    except Exception as e:
        print("GTT Rule creation failed: {}".format(e.message))
    
def gtt_rule_list():
    try:
        status=["FORALL"] #should be a list
        page=1
        count=10
        lists=obj.gttLists(status,page,count)
    except Exception as e:
        print("GTT Rule List failed: {}".format(e.message))

def hist_data(obj):
    try:
        historicParam={
        "exchange": "NSE",
        "symboltoken": "3045",
        "interval": "ONE_MINUTE",
        "fromdate": "2021-02-08 09:00", 
        "todate": "2021-02-08 09:16"
        }
        hist_data=obj.getCandleData(historicParam)
    except Exception as e:
        print("Historic Api failed: {}".format(e.message))
    return hist_data

def logout():
    try:
        logout=obj.terminateSession('Your Client Id')
        print("Logout Successfull")
    except Exception as e:
        print("Logout failed: {}".format(e.message))



def WebSocket():
    from smartapi import SmartWebSocket
    
    FEED_TOKEN= fetch_the_feedtoken(obj)
    CLIENT_CODE=ClientID
    token="nse_cm" #"nse_cm|2885&nse_cm|1594&nse_cm|11536"
    task="mw" #"mw"|"sfi"|"dp"
    ss = SmartWebSocket(FEED_TOKEN, CLIENT_CODE)
    return ss

def on_tick(ws, tick):
    print("Ticks: {}".format(tick))

def on_connect(ws, response):
    ws.websocket_connection() # Websocket connection  
    ws.send_request(token,task) 
    
def on_close(ws, code, reason):
    ws.stop()

# Assign the callbacks.
# ss.on_ticks = on_tick
# ss.on_connect = on_connect
# ss.on_close = on_close

# ss.connect()
import  json
data=hist_data(obj)
# ws= WebSocket()
# data =json.dumps(Historic_api(obj))
# print(data)
# print(ws)

FEED_TOKEN= fetch_the_feedtoken(obj)
ss = WebSocket()
# print(ss)
import talib



