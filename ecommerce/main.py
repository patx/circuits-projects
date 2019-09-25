"""
Lot of [sloppy code] work todo on this, pretty much needs to be re-written
"""

from circuits.web import Server, Controller, Sessions
from jinja2 import Template
import easypost
import pickledb # need to switch to pymongo
import stripe

# need to change this to proper Env loader jinja2 uses
def render(file, **args):
    html = open('templates/%s'%(file), 'r')
    temp = str(html.read())
    return Template(temp).render(args)

class Root(Controller):
    # set the easypost api [test] key
    easypost.api_key = 'EASY POST API KEY HERE'
    # set the stripe secrete api [test] key
    stripe.api_key = 'STRIPE API KEY HERE'
    # the address we are shipping from
    from_addy = easypost.Address.create(
        company = 'Company Name',
        street1 = '5555 SE 2nd Street',
        city = 'Pompano Beach',
        state = 'FL',
        zip = '33060',
        phone = '555-444-3333')
    # database containing all emails and orders
    db = pickledb.load('database.db', True)

    def index(self):
        return render('index.html')

    def buy(self, **kwarg):
        if self.request.method == 'POST':
            # the (verified) address (of the customer) we are shipping to
            try:
                to_addy = easypost.Address.create(
                    verify = ["delivery"],
                    name = kwarg['name'],
                    street1 = kwarg['street1'],
                    street2 = kwarg['street2'],
                    city = kwarg['city'],
                    state = kwarg['state'],
                    zip = kwarg['zip'],
                    email = kwarg['email'])
            except easypost.Error:
                return 'error with address'
            # create a Parcel, weight in oz. and 'Parcel' is a predefined_package
            package = easypost.Parcel.create(
                predefined_package = 'Parcel',
                weight = 10)
            # create a Shipment to find shipping price
            shipment = easypost.Shipment.create(
                to_address = to_addy,
                from_address = self.from_addy,
                parcel = package)
            # the (lowest) price it will cost to ship
            shipping_cost = shipment.lowest_rate()
            # the id of the shipment
            shipping_id = shipment.id()
            # db structure: 'email': [0,1,2,3,4,5,6,7] --> each pos is a value
            self.db.lcreate(kwarg['email'])
            add_to_db = [
                kwarg['name'],
                kwarg['street1'],
                kwarg['street2'],
                kwarg['city'],
                kwarg['state'],
                kwarg['zip'],
                shipping_cost,
                shipping_id]
            self.db.lextend(kwarg['email'], add_to_db)
            # add this users email to the database with value 0 (0=unfilled, 1=filled)
            self.db.dadd('orders', (kwarg['email'], 0))
            # save current buyer in session, so we can pull their info on /confirm
            self.session['buyer'] = kwarg['email']
            return self.redirect('/confirm')
        elif self.request.method == 'GET':
            self.session['buyer'] = False
            return 'shipping address form'

    def confirm(self, **kwarg):
        # make sure the customer has entered email/shipping info on /buy
        if self.session('buyer', False):
            # the customers email as provided in /buy
            dbkey = self.session['buyer']
            # [0,1,2,3,4,5,6,7] list of customers info
            info = self.db.lgetall(dbkey)
            # add the price_of_product + shipping_cost
            total = int(35000 + info[6])
            if self.request.method == 'POST':
                # charge the customer based on billing info provided in checkout.js
                # and send recipt email to email provided in /buy (dbkey)
                charge = stripe.Charge.create(
                    amount = total,
                    currency = 'usd',
                    source = kwarg['stripeToken'],
                    description = dbkey,
                    receipt_email = dbkey)
                # retrieve the shipment created on /buy using its id
                shipment = easypost.Shipment.retrieve(info[7])
                # buy the shipment/label
                shipment.buy(rate=shipment.lowest_rate())
                # create a list with postage label and tracking code
                shipping_info = [
                    shipment.postage_label.label_url,
                    shipment.tracking_code]
                # add the list of shipping info to the customers db list[]
                self.db.lextend(dbkey, shipping_info)
                return self.redirect('/done')
            elif self.request.method == 'GET':
               return 'display productcost + shippingcost and a button to pay'
        else:
            return 'error page'

    def done(self):
        if self.session('buyer', False):
            email_a = self.session['buyer']
            return 'success! email has been sent to %s' %(email_a)
        else:
            return 'error page'

    def admin(self, **kwarg):
        # show admin page if user is logged in
        if self.session('logged_in', False):
            return 'todo'
        # show login page if user is not logged in
        else:
            if self.request.method == 'POST':
                # password for admin page set here
                correctpass = 'password00'
                # check if the password submitted is correct
                if kwarg['password'] == correctpass:
                    # authenticate the user and redirect to admin page
                    self.session['logged_in'] = True
                    return self.redirect('/admin')
                # display error page if password is not correct
                else:
                    return 'error page'
            elif self.request.method == 'GET':
                return 'login page'

(Server('0.0.0.0:8000') + Root() + Sessions()).run()
