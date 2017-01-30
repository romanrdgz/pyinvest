#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Roman Rodriguez
Email: romanrdgz@gmail.com
"""
import datetime as dt


class Candlestick(object):
    '''
    This class represents a chart candlestick with open, close, high and low
    prices
    '''
    def __init__(self, **kwargs):
        '''
        Constructor can be called with 2 different sets of arguments:
        1. (open, high, low, close) for historical data load
        2. Otherwise, it will be assumed that is a new candlestick to be
        updated with additional later ticks
        '''
        if('open' in kwargs and 'high' in kwargs and 'low' in kwargs and
           'close' in kwargs):
            # Create the candlestick with provided data
            self.open_price = kwargs.get('open')
            self.high_price = kwargs.get('high')
            self.low_price = kwargs.get('low')
            self.close_price = kwargs.get('close')
        else:
            self.open_price = kwargs.get('last_price')
            self.close_price = kwargs.get('last_price')
            self.high_price = kwargs.get('last_price')
            self.low_price = kwargs.get('last_price')

        # Common data
        self.start_time = kwargs.get('start_time').replace(
            second=0, microsecond=0)
        self.end_time = self.start_time + kwargs.get('duration')
        self.volume = kwargs.get('volume')
        self.ticks = []

    def __repr__(self):
        return('%s - open: %f, high: %f, close: %f, low: %f, volume: %d' %
               (str(self.start_time), self.open_price, self.high_price,
                self.close_price, self.low_price, self.volume))

    def add_market_data(self, tick_time, last_price, volume):
        '''
        Adds a new data tick to current candlestick
        '''
        self.close_price = last_price
        self.volume += volume
        self.ticks.append((tick_time, last_price))
        if(last_price > self.high_price):
            self.high_price = last_price
        elif(last_price < self.low_price):
            self.low_price = last_price

    def as_dict(self):
        '''
        Returns OHLC-Volume values in a dict, so it can be appended to a
        Pandas DataFrame
        '''
        return {'volume': self.volume,     'time':  self.start_time,
                'open':   self.open_price, 'high':  self.high_price,
                'low':    self.low_price,  'close': self.close_price}
