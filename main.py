#! /usr/bin/env python
# -*- coding: utf-8 -*-
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
import ib_data_types as datatype
from time import sleep
from argparse import ArgumentParser
import datetime as dt
from candlestick import Candlestick
import linecache
import sys


def print_exception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(
          filename, lineno, line.strip(), exc_obj))


candlestick_data = {}


# print all messages from TWS
def __on_error_event(msg):
    try:
        print('[ERROR #%d] - %s' % (int(msg.errorCode), msg.errorMsg))
    except Exception as e:
        print_exception()
        print(msg)


# read historical data
def __on_historicaldata_event(msg):
    try:
        # Check if a new dataset has to be created
        if msg.reqId not in candlestick_data.keys():
            candlestick_data[msg.reqId] = []

        # Check if all the data has been received already (in that case,
        # received data will be -1:
        if msg.open != -1:
            candlestick_data[msg.reqId].append(Candlestick(
                start_time=dt.datetime.strptime(msg.date, '%Y%m%d %H:%M:%S'),
                duration=dt.timedelta(minutes=1),
                open=msg.open,
                high=msg.high,
                low=msg.low,
                close=msg.close,
                volume=msg.volume)
            )
        else:
            # All the data has been received, cancel request
            con.cancelHistoricalData(msg.reqId)
            print('All the requested historical data has been received')

            # Suscribe to realtime ticks data. For forex we need to use the
            # midpoint, and for the rest of contracts we use RTvolume
            if contract.m_secType == 'CASH':
                con.reqMktData(msg.reqId, contracts_dict[msg.reqId], '', False)
            else:
                con.reqMktData(
                    msg.reqId, contracts_dict[msg.reqId], '233,mdoff', False)
    except Exception as e:
        print_exception()


# read RTVolume tick data
def __on_rtvolume_event(msg):
    try:
        if(msg.typeName == 'tickString'):
            if msg.tickType == 48:
                tick_data = msg.value.split(';')
                last_price = float(tick_data[0])
                traded_volume = int(tick_data[1])
                trade_time = dt.datetime.fromtimestamp(
                                int(tick_data[2]) / 1000.0)
                # daily_volume = tick_data[3]
                # vwap = tick_data[4]
                # single_market_maker = (tick_data[5] == 'true')

            # Check if a new dataset has to be created
            if msg.tickerId not in candlestick_data.keys():
                candlestick_data[msg.tickerId] = []

            # Check if a new candlestick shall be created
            if((not candlestick_data[msg.tickerId]) or
               (trade_time > candlestick_data[msg.tickerId][-1].end_time)):
                # Print last finished candlestick
                if(candlestick_data[msg.tickerId]):
                    print(candlestick_data[msg.tickerId][-1])
                candlestick_data[msg.tickerId].append(
                    Candlestick(
                        start_time=trade_time,
                        duration=dt.timedelta(minutes=1),
                        last_price=last_price,
                        volume=traded_volume
                    )
                )
            else:
                candlestick_data[msg.tickerId][-1].add_market_data(
                    dt.datetime.now(), last_price, traded_volume)
    except Exception as e:
        print_exception()


def make_contract(contractTuple):
    newContract = Contract()
    newContract.m_symbol = contractTuple[0]
    newContract.m_secType = contractTuple[1]
    newContract.m_exchange = contractTuple[2]
    newContract.m_currency = contractTuple[3]
    newContract.m_expiry = contractTuple[4]
    newContract.m_strike = contractTuple[5]
    newContract.m_right = contractTuple[6]
    print('Contract Values:%s,%s,%s,%s,%s,%s,%s:' % contractTuple)
    return newContract


if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    '''
    parser.add_argument('-t', '--tickers', nargs='+', required=True,
                        help='[Required] Determines a list of option tickers')
    '''
    parser.add_argument('-ho', '--tws_host', type=str, default='localhost',
                        help=('Determines the host where TWS/Gateway is '
                              'listening'))
    parser.add_argument('-p', '--tws_port', type=int, default=7496, help=(
                        'Determines the port where TWS/Gateway is listening. '
                        'TWS default is 7496, and Gateway default is 4002'))
    parser.add_argument('-o', '--output_file', type=str,
                        help='Determines the output file for market data')
    config = parser.parse_args()

    con = ibConnection(host=config.tws_host, port=config.tws_port)
    # Set watcher callback functions
    con.register(__on_rtvolume_event, message.tickString)
    con.register(__on_historicaldata_event, message.historicalData)
    con.register(__on_error_event, message.error)

    con.connect()
    sleep(1)
    tickId = 1

    # Note: Option quotes will give an error if they aren't shown in TWS
    contracts_dict = {
        # 1: make_contract(('YM', 'FUT', 'ECBOT', 'USD', '201703', 0.0, ''))
        1: make_contract(('YM', 'SMART:FUT', 'ECBOT', 'USD', '201703', 0.0,
                          ''))
    }

    '''
    2: make_contract(('QQQQ', 'STK', 'SMART', 'USD', '', 0.0, '')),
    3: make_contract(('QQQQ', 'OPT', 'SMART', 'USD', '20070921', 47.0,
                      'CALL')),
    4: make_contract(('ES', 'FOP', 'GLOBEX', 'USD', '20070920', 146.0,
                      'CALL')),
    5: make_contract(('EUR', 'CASH', 'IDEALPRO', 'USD', '', 0.0, '')),
    '''

    # Request historical data from the last day. Once received, it will
    # get suscribed to realtime tick data
    for ticker_id, contract in contracts_dict.items():
        end_datetime = (
            '%s US/Eastern' % dt.datetime.now().strftime('%Y%m%d %H:%M:%S'))
        con.reqHistoricalData(
            tickerId=ticker_id, contract=contract, endDateTime=end_datetime,
            durationStr=datatype.DURATION_1_DAY,
            barSizeSetting=datatype.BAR_SIZE_1_MIN,
            whatToShow=(datatype.SHOW_BID_ASK if contract.m_secType == 'CASH'
                        else datatype.SHOW_TRADES),
            useRTH=datatype.RTH_ALL, formatDate=datatype.DATEFORMAT_STRING)

    print('* * * * REQUESTING MARKET DATA * * * *')
    input('PRESS <ENTER> TO CLOSE DATA CONNECTION\n')
    print('* * * * CANCELING MARKET DATA * * * *')
    [con.cancelMktData(tickId) for tickId in contracts_dict.keys()]
    sleep(1)
    con.disconnect()
    sleep(1)

    # Store candlesticks in a file (from the first contract for now)
    tick_id = contracts_dict.keys()[0]
    if(config.output_file):
        with open(config.output_file, 'w') as out:
            [out.write(str(candle) + '\n')
             for candle in candlestick_data[tick_id]]
