from difflib import SequenceMatcher
import pandas as pd
import numpy as np
import datetime as dt
import streamlit as st
import itertools
import matplotlib.pyplot as plt

from cost import Cost
from sale import Sale
from product import Product
from base_product import BaseProduct


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def plot_cumulative_revenue(min_cut):
    df = get_margin_information()

    df['amount'] = np.where(df['reason'] != 'sale', -df['amount'], df['amount'])
    df = df.set_index('date').resample(min_cut).amount.sum().reset_index()
    df = df.groupby('date').sum()
    df['amount'] = df['amount'].cumsum()

    fig, ax = plt.subplots()
    plt.xticks(rotation=-45)
    ax.plot(df.index, df['amount'], label='total revenue', marker='o')
    return fig, ax


def get_margin_information():
    amount = []
    reason = []
    date = []

    for cost in Cost.costs_list:
        amount.append(cost.amount)
        date.append(cost.date)
        reason.append(cost.reason)
    for sale in Sale.sales_list:
        amount.append(sale.amount_price)
        date.append(sale.date)
        reason.append('sale')

    df = pd.DataFrame({'reason': reason, 'date': date, 'amount': amount})

    # Filter with latest sales data
    df['date'] = pd.to_datetime(df['date'])
    max_sale_date = df[df['reason'] == 'sale']['date'].max()
    df = df[df['date'] <= max_sale_date]

    return df


def plot_sales_and_costs(min_cut):
    df = get_margin_information()

    net_margin = df[['date', 'reason', 'amount']].copy().groupby(['date', 'reason']).sum().reset_index()
    net_margin['amount'] = np.where(net_margin['reason'] == 'sale', net_margin['amount'], -net_margin['amount'])
    net_margin = net_margin[['date', 'amount']].groupby('date').sum().reset_index()
    net_margin = net_margin.set_index('date').resample(min_cut).amount.sum()

    total_cost = df[df['reason'] != 'sale'].copy()
    total_cost['reason'] = 'total'
    total = total_cost.set_index('date').resample(min_cut).amount.sum()

    fig, ax = plt.subplots()
    plt.xticks(rotation=-45)
    ax_twin = ax.twinx()

    ax_twin.bar(net_margin.index, net_margin, label='net', color=(net_margin > 0).map({True: 'g', False: 'r'}), alpha=0.5, width=3)

    ax.plot(total.index, total, label='total_cost', marker='x')
    for reason in df.reason.unique():
        df_for_reason = df[df['reason'] == reason][['date', 'amount']]
        df_for_reason = df_for_reason.set_index('date').resample(min_cut).amount.sum()
        ax.plot(df_for_reason.index, df_for_reason, label=reason, marker='x')

    ax.legend()
    ax_twin.legend()

    return fig, ax


def hist_margin():
    margin_dict = {product: product.get_perc_margin() for product in BaseProduct.base_products_list if len(product.sales) > 0}

    fig, ax = plt.subplots()

    _, _, patches = ax.hist(margin_dict.values(), align="mid", color='blue', edgecolor='black', linewidth=1.2)
    for pp in patches:
        x = (pp._x0*2 + pp._width/2) / 2
        y = pp._height + 0.05
        ax.text(x, y, int(pp._height), color='black')

    return fig, ax
