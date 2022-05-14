class Cost:
    costs_list = []

    def __init__(self, date, reason, amount):
        self.date = date
        self.reason = reason
        self.amount = amount

        Cost.costs_list.append(self)