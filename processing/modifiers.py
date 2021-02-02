import datetime

from parsers.consts import TRADE_DATE
from processing.enrich_data import enrich_with_daily_usd_huf_rate
import pandas as pd

def combine_clean_and_convert(stonks : pd.DataFrame) -> pd.DataFrame:
    data = pd.concat(stonks).reset_index(drop = True).dropna()
    data[TRADE_DATE] = pd.to_datetime(data[TRADE_DATE])
    data['Settle Date'] = pd.to_datetime(data['Settle Date'])
    data['SignedAmount_USD'] = data['Quantity'] * data['Price'] * -1
    return data.sort_values(by=TRADE_DATE)

def remove_noise(df):
    return df[[TRADE_DATE, 'Activity Type', 'Symbol', 'Price', 'Amount', 'SignedAmount_USD', 'Quantity']]

def filter_by_date(activity, date_string : str):
    return activity[activity['Trade Date'] < datetime.datetime.strptime(date_string, '%m/%d/%Y')]

def calculate_szja_for_2020(activity):
    activity = combine_clean_and_convert(activity)
    activity = remove_noise(activity)
    activity = enrich_with_daily_usd_huf_rate(activity)
    activity = filter_by_date(activity, '12/31/2020')
    summed_earnings = activity.groupby(['Symbol']).sum().round(decimals=4)
    closed_positions = summed_earnings[summed_earnings['Quantity'] < 0.0001]
    return closed_positions['SignedAmount_HUF'].sum() * 0.15