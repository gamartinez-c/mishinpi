import pandas as pd
import datetime as dt
import os

path_to_new_orders = 'dolar/'
new_orders_files = os.listdir(path_to_new_orders)

new_orders_df_list = [pd.read_csv(path_to_new_orders + file) for file in new_orders_files]
new_orders_df = pd.concat(new_orders_df_list)


old_orders = 