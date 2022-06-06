import itertools

import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from statistics import mean

from stock_movement import StockMovement
from base_product import BaseProduct
from sale import Sale


class Product(BaseProduct):
    products_list = []
    products_by_sku = {}
    products_by_name = {}

    def __init__(self, price, cost, sku_name, name):
        super().__init__(price, cost, sku_name, name)
        self.stock_movements = []
        self.stock_at_date_dict = {}

        Product.products_list.append(self)
        Product.products_by_sku[self.sku_name] = self
        Product.products_by_name[self.name] = self

    def add_sale(self, sale, shipment_cost, shipping_type=None):
        shipping_type = shipping_type if shipping_type is not None else 'Envio a Domicilio'
        super().add_sale(sale, shipment_cost)
        stock_movement_of_sale = StockMovement(self, sale.quantity, sale.date, shipping_type)
        self.stock_movements.append(stock_movement_of_sale)

    def plot_stock_movements(self, time_window=None, ax=None):
        date_list = []
        amount_list = []
        for movement in self.stock_movements:
            date_list.append(movement.date)
            amount_list.append(movement.amount)

        df = pd.DataFrame({'date': date_list, 'amount': amount_list})
        df['date'] = pd.to_datetime(df['date'])
        df = df.groupby('date').sum().reset_index()
        if time_window is not None:
            df = df.set_index('date').resample(time_window).amount.sum()

        if ax is None:
            fig, ax = plt.subplots()
            should_show = True
        else:
            should_show = False

        df.plot(title=f'{self.name} stock', ax=ax, style='.-')
        if should_show:
            plt.show()

    def adjust_stock(self):
        pass

    def get_average_daily_demand_for_stock(self, last_timedelta=None, consider_just_sends=True):
        if last_timedelta is None:
            sales_list = [sale.date for sale in Sale.sales_list]
            last_timedelta = max(sales_list) - min(sales_list)
        first_date_to_start_tracking = dt.date.today() - last_timedelta
        movements = []
        for stock_movement in self.stock_movements:
            if (stock_movement.amount > 0) and (stock_movement.date >= first_date_to_start_tracking):
                if consider_just_sends:
                    if stock_movement.shipping_type != 'Loria 275, Lomas de Zamora, Provincia de Buenos Aires':
                        movements.append(stock_movement)
                else:
                    movements.append(stock_movement)
        movement_dates = [stock_movement.date for stock_movement in movements]
        movement_amount = [stock_movement.amount for stock_movement in movements]
        if len(movement_dates) != 0:
            days_diff = last_timedelta.days
            if days_diff != 0:
                return sum(movement_amount) / days_diff
            return 0
        return 0

    def get_stock(self, date=None):
        date = date if date is not None else dt.date.today()
        movements_after_date = [movement for movement in self.stock_movements if movement.date > date]
        amount_moved = sum([movement.amount for movement in movements_after_date])

        latest_stock = self.stock_at_date_dict[max(self.stock_at_date_dict.keys())]

        stock_at_date = latest_stock + amount_moved

        # Se necesita considerar el caso de cuando los moviemintos son anteriores al stock
        return stock_at_date

    def get_next_stock_break(self, timedelta_to_consider_demand=None):
        daily_demand = self.get_average_daily_demand_for_stock(timedelta_to_consider_demand)
        stock_today = self.get_stock()
        if stock_today < 0:
            return dt.date.today()
        elif daily_demand == 0:
            return dt.date.today() + dt.timedelta(weeks=52)
        else:
            day_until_break = stock_today // daily_demand
            return dt.date.today() + dt.timedelta(days=day_until_break)

    def __str__(self):
        return f'Product Name: {self.name} | SKU Name: {self.sku_name}'

    @staticmethod
    def get_stock_record_of_time_window(timedelta_to_consider_demand=dt.timedelta(days=60), filter_products=None):
        if filter_products is None:
            filter_products = [*Product.products_by_name]
        next_breaking_stock_dates = Product.get_next_break_of_all_products(timedelta_to_consider_demand)
        next_breaking_stock_dates = next_breaking_stock_dates[['name', 'break_date']].rename(columns={'name': 'product', 'break_date': 'date'})
        next_breaking_stock_dates['stock'] = 0

        all_stock_movements_dates_in_timedelta = set()
        for product in Product.products_list:
            for sale in product.sales:
                if sale.date > (dt.date.today() - timedelta_to_consider_demand):
                    all_stock_movements_dates_in_timedelta.add(sale.date)

        all_combination_product_date = itertools.product([Product.products_by_name[name] for name in filter_products], all_stock_movements_dates_in_timedelta)
        stocks_dates_data = {'date': [], 'product': [], 'stock': []}
        for product, date in all_combination_product_date:
            stocks_dates_data['date'].append(date)
            stocks_dates_data['product'].append(product.name)
            stocks_dates_data['stock'].append(product.get_stock(date))

        stocks_dates_data = pd.DataFrame(stocks_dates_data)
        stocks_dates_data = pd.concat([stocks_dates_data, next_breaking_stock_dates], ignore_index=True)
        stocks_dates_data.reset_index(drop=True, inplace=True)

        return stocks_dates_data

    @staticmethod
    def plot_stock(timedelta_to_consider_demand, filter_products):
        stock_records = Product.get_stock_record_of_time_window(timedelta_to_consider_demand, filter_products)
        stock_records = stock_records[(stock_records['date'] <= dt.date.today() + timedelta_to_consider_demand) & (stock_records['date'] >= dt.date.today() - timedelta_to_consider_demand)]
        stock_records.sort_values(by='date', inplace=True)

        fig, ax = plt.subplots()
        plt.xticks(rotation=-45)
        for product in stock_records['product'].unique():
            product_records = stock_records[stock_records['product'] == product]
            ax.plot(product_records['date'], product_records['stock'], label=product)

        ax.vlines(dt.date.today(), 0, stock_records['stock'].max(), colors='black', linestyles=(0, (3, 5, 1, 5)))
        # plt.legend()
        return fig, ax

    @staticmethod
    def get_next_break_of_all_products(timedelta_to_consider_demand=None):
        next_break_info_dict = {'name': [], 'break_date': [], 'stock_today': [], 'daily_demand': []}
        for product in Product.products_list:
            next_breaking_date = product.get_next_stock_break(timedelta_to_consider_demand)
            stock = product.get_stock()
            daily_demand = product.get_average_daily_demand_for_stock(timedelta_to_consider_demand)
            next_break_info_dict['name'].append(product.name)
            next_break_info_dict['break_date'].append(next_breaking_date)
            next_break_info_dict['stock_today'].append(stock)
            next_break_info_dict['daily_demand'].append(daily_demand)

        next_break_info_df = pd.DataFrame(next_break_info_dict)
        return next_break_info_df

    @staticmethod
    def buy_calculation(time_laps_until_next_purchase=None, timedelta_to_consider_demand=None):
        if time_laps_until_next_purchase is None:
            time_laps_until_next_purchase = dt.timedelta(days=30)
        next_breaking_df = Product.get_next_break_of_all_products(timedelta_to_consider_demand)

        first_date_for_breaking_product = next_breaking_df['break_date'].min()
        date_to_buy = first_date_for_breaking_product - dt.timedelta(days=2)
        if date_to_buy < dt.date.today():
            date_to_buy = dt.date.today() + dt.timedelta(days=1)

        days_until_buy = (date_to_buy - dt.date.today()).days

        amount_to_supply_between_buys = next_breaking_df['daily_demand'] * time_laps_until_next_purchase.days
        amount_demanded_util_first_buy = next_breaking_df['daily_demand'] * days_until_buy
        amount_to_buy_per_product = amount_to_supply_between_buys - (next_breaking_df['stock_today'] - amount_demanded_util_first_buy)

        amount_to_buy_per_product = np.around(amount_to_buy_per_product)
        next_breaking_df['amount_to_buy_per_product'] = np.where(amount_to_buy_per_product > 0, amount_to_buy_per_product, 0)

        return next_breaking_df
