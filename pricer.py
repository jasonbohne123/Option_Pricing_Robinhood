import pandas as pd
import numpy as np
import QuantLib as ql
import robin_stocks.robinhood as rs


def get_vol(symbol):
  '''
    Input: 
      symbol:str of underlying
    
    Output:
      vol: float, monthly daily volatility computed from close to clsoe
  '''
  close=[float(x['close_price']) for x in rs.get_stock_historicals('AAPL', interval='day', span='month')]
  vol=np.log(close).std()*np.sqrt(30)
  return vol
  
def calculate_theor(symbol,strike,optionType,expirationDate,underlying_open,model,settlement=ql.Date.todaysDate()):
  '''
  Inputs:
        symbol: Str, of the Underlying
        strike: Str, strike price of contract
        optionType: Str, Type of option, call or put
        expirationDate: String: Date of Expiration
        underlying_open: Float, Last open price of underlying
        model= BS, BAW, BJST, see below
        settlement: Str, defaults to today's date

      Outputs:
        BS: Float, BS Solution 
        BAW: Float, Barone-Adesi-Approx
        BJST: Float, Bjerksund-Stensland Approx
       
  '''

  #Expiration and Settlement date
  maturity_date=ql.Date(expirationDate, '%Y-%m-%d')
  if type(settlement) is str :
     calculation_date = ql.Date(settlement, '%Y-%m-%d')
  else: 
    calculation_date =settlement
  ql.Settings.instance().evaluationDate = calculation_date

  #Divdend rate
  if rs.get_fundamentals(symbol)[0]['dividend_yield'] is None:
    dividend_rate=0
  else:
    dividend_rate =  float(rs.get_fundamentals(symbol)[0]['dividend_yield'])/100

  #Risk free rate and calendar convention
  risk_free_rate = 0.0142 #based off the ten year bond (US Treasury Rate)
  day_count = ql.Actual365Fixed()
  calendar = ql.UnitedStates()

  # Option Type
  if optionType =='call':
    option_type = ql.Option.Call
  else:
    option_type = ql.Option.Put
 #Monthly Daily Realized Volatility
  volatility=get_vol(symbol)

  #Initiate option payoff and exercise styles
  payoff = ql.PlainVanillaPayoff(option_type, strike)
  europeanexercise=ql.EuropeanExercise(maturity_date)
  americanexercise = ql.AmericanExercise(calculation_date,maturity_date)
  european_option=ql.VanillaOption(payoff, europeanexercise)
  american_option = ql.VanillaOption(payoff, americanexercise)

  #Initiate Black Scholes Metron Process
  spot_handle = ql.QuoteHandle(
    ql.SimpleQuote(float(underlying_open))
)
  flat_ts = ql.YieldTermStructureHandle(
    ql.FlatForward(calculation_date, risk_free_rate, day_count)
)
  dividend_yield = ql.YieldTermStructureHandle(
  ql.FlatForward(calculation_date, dividend_rate, day_count)
)
  flat_vol_ts = ql.BlackVolTermStructureHandle(
  ql.BlackConstantVol(calculation_date, calendar, volatility, day_count)
)

  bsm_process = ql.BlackScholesMertonProcess(spot_handle, 
                                          dividend_yield, 
                                        flat_ts, 
                                         flat_vol_ts)
  #Black-Scholes Analytical Solution, Approximation to American options
  if model =='BS':
    european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
    val=european_option.NPV()
  
  #Barone Adesi-Whaley Quadratic Approximation
  elif model=='BAW':
    american_option.setPricingEngine(ql.BaroneAdesiWhaleyApproximationEngine(bsm_process))
    val=american_option.NPV()

  #
  elif model=='BJST':
    ql.BjerksundStenslandApproximationEngine
    american_option.setPricingEngine(ql.BjerksundStenslandApproximationEngine(bsm_process))
    val=american_option.NPV()
 
  else:
    return None

  return val