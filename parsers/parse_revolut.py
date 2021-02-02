import PyPDF2
import pandas as pd
from typing import Union

from parsers.consts import TRADE_DATE, SYMBOL, FULL_NAME, QUANTITY, PRICE, CDEP, CSD, AMOUNT
import datetime

PDFFilePath = str


def parse_date(date: str) :
    return datetime.datetime.strptime(date, '%m/%d/%Y')


def parse_price(price: str) -> float:
    return float(price)


def parse_amount(amount: str) -> float:
    return float(amount.replace('(', '').replace(')', ''))


def parse_quantity(quantity: str) -> float:
    return float(quantity)


def parse(col: str, token_: str) -> Union[str, float, datetime.datetime]:
    """
    Parsing the tokens based on related column name
    :param col: column name string
    :param token_: token string
    :return:
    """
    if col == TRADE_DATE:
        return parse_date(token_)
    if col == PRICE:
        return parse_price(token_)
    if col == QUANTITY:
        return parse_quantity(token_)
    if col == AMOUNT:
        return parse_amount(token_)

    return token_


def parse_invoice(path: PDFFilePath) -> pd.DataFrame:
    """
    Parses revolut invoice pdf file in a quite hacky, but seemingly
    working way. Note: Not tested in cases where the activity goes
    over a single page.
    :param path: path to file
    :return: dataframe containing the stock activity
    """
    sep = '\n'
    reader = PyPDF2.PdfFileReader(path)
    r = [reader.getPage(i).extractText() for i in range(reader.getNumPages())]
    activity = [activity for activity in r if f'ACTIVITY\n{TRADE_DATE}' in activity]
    activity[0].split(sep)

    start = activity[0].find(f"{TRADE_DATE}\nSettle")
    stop = activity[0].find("Page")
    activity_table = activity[0][start:stop].split(sep)

    header_cnt = 8
    headers = activity_table[0:header_cnt]

    def create_row() -> dict:
        row = {}
        for i in range(header_cnt):
            row[headers[i]] = None
        row[SYMBOL] = None
        row[FULL_NAME] = None
        return row

    rows = [create_row()]
    offset = 0
    for index, token in enumerate(activity_table[header_cnt:-1]):
        # The activity table is either terminated by reading a page count,
        # or the next table, SWEEP ACTIVITY
        if 'SWEEP ACTIVITY' in token or 'PAGE' in token:
            break
        index_w_offset = index + offset
        col_index = index_w_offset % header_cnt
        row_index = int(index_w_offset / header_cnt)
        col_name = headers[col_index]

        # Random strings get parsed as quantity.. small hack to remove those.
        if col_name == PRICE:
            try:
                parse_price(token)
            except Exception as e:
                #print(f"Failed to parse [{token}] as Price =>{e}")
                continue
        if col_name == QUANTITY:
            try:
                float(token)
            except Exception as e:
                #print(f'Failed to parse [{token}] as  quantity => {e}')
                offset -= 1
                continue
        # These 2 rows seems to be missing 2 tokens, so we need to offset with it if encountered.
        if token == CDEP or token == CSD:
            offset += 2

        # Just some extra convenience when parsing here instead of later.
        if col_name == f"{SYMBOL} / Description":
            splitted = token.split('-')
            rows[row_index][SYMBOL] = splitted[0]
            rows[row_index][FULL_NAME] = splitted[1]

        if col_index == 0:
            rows.append(create_row())
        rows[row_index][col_name] = parse(col_name, token)
    stocks = pd.DataFrame().from_records(rows)
    stocks.dropna()
    return stocks
