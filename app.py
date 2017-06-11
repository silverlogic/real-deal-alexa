import re

from flask import Flask
from flask_ask import Ask, statement, question, session

import requests

app = Flask(__name__)
ask = Ask(app, '/')


@ask.intent('DealsNearMeIntent')
def deals_near_me():
    merchant_names = set()
    for offer in get_offers():
        for merchant in offer['merchants']:
            merchant_names.add(merchant['name'])
    merchant_names = list(merchant_names)
    merchants_str = ', '.join(merchant_names[:-1])
    merchants_str += f', and {merchant_names[-1]}'
    return question(f'I found deals at {merchants_str}, which would you like to hear?')


@ask.intent('MerchantDealsIntent')
def merchant_deals(merchant):
    print(merchant)
    session.attributes['merchant'] = merchant

    deals = []
    offers = get_offers()
    for offer in offers:
        if merchant.lower().replace('and', '&') in [merchant['name'].lower() for merchant in offer['merchants']]:
            deals.append(offer)

    deal_names = [deal['title'] for deal in deals]
    if not deals:
        return statement('I couldn\'nt find any deals for {}'.format(merchant))
    if len(deals) == 1:
        deals_str = deal_names[0]
        session.attributes['deal'] = offer['copy']
        return question(f'I found 1 deal at {merchant}. {deals_str}, would you like to hear it?')
    else:
        deals_str = ', '.join(deal_names[:-1])
        deals_str += f', and {deal_names[-1]}'
        return question(f'I found {len(deals)} deals at {merchant}. {deals_str}, which would you like to hear?')


@ask.intent('DealIntent')
def deal(deal):
    print(deal)
    if not session.attributes.get('merchant'):
        return question('Which merchant would you like to hear the deal for?')
    merchant = session.attributes['merchant']
    match = re.search(r'(\d+) dollars', deal)
    if match:
        deal = 'save ${}'.format(match.group(1))

    deals = []
    offers = get_offers()
    for offer in offers:
        if merchant.lower().replace('and', '&') in [merchant['name'].lower() for merchant in offer['merchants']]:
            if deal.lower() == offer['title'].lower():
                return statement(offer['copy'])

    return statement('I couldn\'t find an offer for that, sorry!')


@ask.intent('YesNoIntent')
def yes_no(yesno):
    print(yesno)
    if yesno == 'yes':
        return statement(session.attributes['deal'])
    return statement('Okay, goodbye.')


def get_offers():
    return requests.get('http://localhost:8000/api/offers').json()


if __name__ == '__main__':
    app.run()
