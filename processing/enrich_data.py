import datetime

import pandas as pd
import yfinance as yf
from exchangeratesapi import Api as exchangeApi

from parsers.consts import TRADE_DATE


def get_stock_current_value(stock_symbol):
    stonk = yf.Ticker(stock_symbol)
    # get historical market data, here max is 5 years.
    return stonk.history(period="max").iloc[-1]['Close']


def get_huf_to_usd_exchange_rate_in_interval(start, stop):
    api = exchangeApi()
    huf_to_usd = pd.DataFrame.from_records(
        api.get_rates('USD', ['HUF'], start_date=start, end_date=stop)[
            'rates']).transpose()
    huf_to_usd.index = pd.to_datetime(huf_to_usd.index)
    huf_to_usd.index.name = 'date'
    return huf_to_usd


def enrich_with_daily_usd_huf_rate(activity):
    rates = ExchangeRateProvider2020().rates['USD']

    transations_with_usd = pd.merge_asof(activity.sort_index(), rates, left_on=TRADE_DATE, right_on='date')
    transations_with_usd['SignedAmount_HUF'] = transations_with_usd['SignedAmount_USD'] \
                                                               * transations_with_usd['USD']

    return transations_with_usd

class ExchangeRateProvider2020:
    def __init__(self):
        self.year = 2020
        self.rates = pd.read_excel('./data/mnb_arfolyamok.xlsx').set_index('Dátum/ISO').drop('Egység')
        self.rates.index = pd.to_datetime(self.rates.index)
        self.rates.index = self.rates.index.rename('date')

    def get_rate_for_usd_by_date(self, month, day):
        return self.rates.iloc[self.rates.index.get_loc(datetime.datetime(self.year, month,day),method='nearest')]['USD']
