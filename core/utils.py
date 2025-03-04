import stripe

def get_product_details(product):
    product_details = {
        'id': product['id'],
        'name': product['name'],
        'description': product['description'],
        'price': stripe.Price.list(product=product['id']).data[0].unit_amount / 100,
    }

    return product_details