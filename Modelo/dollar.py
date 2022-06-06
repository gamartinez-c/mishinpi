import datetime as dt


class Dollar:
    exchanger = None

    def __init__(self, exchange_price_date_list_tuples):
        self.exchange_price_date_list_tuples = exchange_price_date_list_tuples

        Dollar.exchanger = self

    def get_price_at_date(self, date):
        if len(self.exchange_price_date_list_tuples) != 1:
            upper_limit = None
            lower_limit = None
            for price_date_tuple in self.exchange_price_date_list_tuples:
                tuple_date = price_date_tuple[1]
                if tuple_date >= date:
                    if upper_limit is None:
                        upper_limit = price_date_tuple
                    if upper_limit[1] > tuple_date:
                        upper_limit = price_date_tuple
                if tuple_date <= date:
                    if lower_limit is None:
                        lower_limit = price_date_tuple
                    if lower_limit[1] < tuple_date:
                        lower_limit = price_date_tuple

            if upper_limit is None:
                return self.exchange_price_date_list_tuples[-1][0]
            elif lower_limit is None:
                return self.exchange_price_date_list_tuples[0][0]
            elif upper_limit != lower_limit:
                diff_of_days_between_records = (upper_limit[1] - lower_limit[1]).days
                relative_position_of_date = (date - lower_limit[1]).days / diff_of_days_between_records
                price_at_date = (upper_limit[0] - lower_limit[0]) * relative_position_of_date + lower_limit[0]
                return price_at_date
            else:
                return upper_limit[0]
        elif len(self.exchange_price_date_list_tuples) == 1:
            return self.exchange_price_date_list_tuples[0][0]
        else:
            return None

    def sort_exchange_records(self):
        self.exchange_price_date_list_tuples.sort(key=lambda x: x[1])

