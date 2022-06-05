from stock_movement import StockMovement
from base_product import BaseProduct


class Kit(BaseProduct):
    kits_list = []

    def __init__(self, price, cost, sku_name, name, products_composed_of):
        super().__init__(price, cost, sku_name, name)
        self.products_composed_of = products_composed_of

        Kit.kits_list.append(self)

    def add_sale(self, sale, shipment_cost, shipping_type=None):
        shipping_type = shipping_type if shipping_type is not None else 'Envio a Domicilio'
        super().add_sale(sale, shipment_cost)

        for product in self.products_composed_of:
            stock_movement_of_sale = StockMovement(product, sale.quantity, sale.date, shipping_type)
            product.stock_movements.append(stock_movement_of_sale)
