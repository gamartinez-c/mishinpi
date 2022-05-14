import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from statistics import mean

from stock_movement import StockMovement
from base_product import BaseProduct


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

    def add_sale(self, sale, shipment_cost):
        super().add_sale(sale, shipment_cost)
        stock_movement_of_sale = StockMovement(self, sale.quantity, sale.date)
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

    def get_average_daily_demand(self):
        movement_dates = [stock_movement.date for stock_movement in self.stock_movements if stock_movement.amount > 0]
        movement_amount = [stock_movement.amount for stock_movement in self.stock_movements if stock_movement.amount > 0]
        min_date = min(movement_dates)
        max_date = max(movement_dates)
        days_diff = (max_date - min_date).days
        if days_diff != 0:
            return sum(movement_amount) / days_diff
        else:
            return 0

    def get_stock(self, date=None):
        date = date if date is not None else dt.date.today()
        movements_after_date = [movement for movement in self.stock_movements if movement.date > date]
        amount_moved = sum([movement.amount for movement in movements_after_date])

        latest_stock = self.stock_at_date_dict[max(self.stock_at_date_dict.keys())]

        stock_at_date = latest_stock + amount_moved

        # Se necesita considerar el caso de cuando los moviemintos son anteriores al stock
        return stock_at_date

    def get_next_stock_break(self):
        daily_demand = self.get_average_daily_demand()
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
