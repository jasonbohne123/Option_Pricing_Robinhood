import robin_stocks.robinhood as rs
import pandas as pd
import numpy as np
import QuantLib as ql
import requests
import pricer

pd.set_option('display.max_columns', None)

def get_options():
  '''
      Outputs:
        - Array of Current option positions with properties & quantity
  '''
 
  options=[]

  for x in rs.get_open_option_positions():
      response=requests.get(x['option'])
      expiration=response.json()['expiration_date']
      strike=response.json()['strike_price']
      symbol=response.json()['chain_symbol']
      right=response.json()['type']
      quantity=x['quantity']
      options.append((symbol,expiration,strike,right,quantity))

  return options

def generate_df(options,model='BS'):

  option_data=[]
  for contract in options:
    option_data.append(rs.find_options_by_expiration_and_strike(inputSymbols=contract[0],expirationDate=contract[1],strikePrice=contract[2],optionType=contract[3])[0])
  df=pd.DataFrame(option_data)

  #drops uneccessary labels
  names=['chance_of_profit_short','chance_of_profit_long','last_trade_size','issue_date','chain_id','created_at','id','min_ticks','rhs_tradability','state','tradability','updated_at','url','sellout_datetime','long_strategy_code','short_strategy_code','ask_price','ask_size','bid_price','bid_size','break_even_price','high_price','instrument','instrument_id','low_price','previous_close_date','previous_close_price','adjusted_mark_price','symbol','occ_symbol','high_fill_rate_buy_price','high_fill_rate_sell_price','low_fill_rate_buy_price','low_fill_rate_sell_price']
  df=df.drop(labels=names,axis=1)
  
  #Fetch latest price
  price=rs.get_latest_price(df['chain_symbol'][0])
  
  #compute desired theoretical price
  theor=[]
  for i in range (0, int(df.shape[0])):
    theor.append(pricer.calculate_theor(df['chain_symbol'][i],float(df['strike_price'][i]),df['type'][i],df['expiration_date'][i],float(price[0]),model))
  df['Theoretical']= theor 

  #Sort by strike price for ease of use
  df['strike_price']=pd.to_numeric(df['strike_price'].values)
  df=df.sort_values(by='strike_price')
  new_sorteddf1=pd.DataFrame(df,columns=['chain_symbol','expiration_date','strike_price','type','last_trade_price', 'mark_price', 'Theoretical','delta','gamma','theta','rho','vega','implied_volatility','volume'])
  
  return new_sorteddf1

def login():
    print("\n")
    print ("Welcome! This program allows you to compute the theoretical value of options you hold in your Robinhood Portfolio ")
    print("\n")
    print(" If you would like to continue by connecting your Robinhood account enter Y")

    string=input()
    if string != "Y":
        return
    
    #login into robinstocks
    rs.login(username='',
         password='',
         expiresIn=1800, #30 mins of authentication 
         by_sms=True)

    print("Great, to see the current options in your portfolio enter ")
    newstring=input()
    options=get_options()

    print("Options currently in your portfolio")
    print(options)
    print("\n")
    print("Currently three option pricing models are supported. These are Black-Scholes [BS], Barone-Adesi-Whaley [BAW], and Bjerksund-Stensland [BJST]")
    print("\n")
    print("Type in the model you wish to compute theoretical values as BS BAW or BJST ")

    model=input()

    if model !='BS' and model!= 'BAW' and model!='BJST':
      return

    print(generate_df(options,model))
    
login()
rs.logout