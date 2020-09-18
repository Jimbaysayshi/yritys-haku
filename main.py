
from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os
import datetime

app = Flask(__name__)


def get_dates():
    now = datetime.datetime.now()
    week = datetime.timedelta(days=7)
    dates = {
        "now": now.strftime("%Y-%m-%d"),
        "weekago": (now-week).strftime("%Y-%m-%d")
    }
    return dates


def sort_data(data):

    _id = data['businessId']
    name = data['name']
    registered = data['registrationDate']
    company_form = data['companyForm']
    details = data['detailsUri']

    response = requests.get(details)
    detail_data = response.json()['results']

    founder = ""
    locality = ""
    post_code = ""
    first_address = ""
    business_line = ""
    business_line_code = ""
    phone_num = ""
    mobile_num = ""
    website = ""
    try:
        founder = detail_data[0]['addresses'][0]['careOf']
        locality = detail_data[0]['registedOffices'][0]['name']
        post_code = detail_data[0]['addresses'][0]['postCode']
        first_address = detail_data[0]['addresses'][0]['street']
        business_line_code = detail_data[0]['businessLines'][0]['code']
        business_line = detail_data[0]['businessLines'][1]['name']

        contacts = detail_data[0]['contactDetails']
        for item in contacts:

            if 'Puhelin' in item.values():
                phone_num = item.get('value')
            elif 'Matkapuhelin' in item.values():
                mobile_num = item.get('value')
            elif 'Kotisivun www-osoite' in item.values():
                website = item.get('value')

    except IndexError as ie:
        print(ie)
        pass
    company = {
        'name': name,
        'registered': registered,
        'company_form': company_form,
        'details': details,
        'founder': founder or "-",
        'locality': locality or "-",
        'post_code': post_code or "-",
        'first_address': first_address or "-",
        'business_line_code': business_line_code or "-",
        'business_line': business_line or "-",
        'phone_num': phone_num or "-",
        'mobile_num': mobile_num or "-",
        'website': website or "-",
    }
    return company


def validate_form(form):
    now = datetime.datetime.now()
    week = datetime.timedelta(days=7)
    valid_form = {}
    default_parameters = {
        "maxResults": 10,
        "registeredOffice": "Helsinki",
        "businessLineCode": "",
        "resultsFrom": 0,
        "companyRegisterationFrom": 0,
        "companyRegistrationTo": now.strftime("%Y-%m-%d")
    }
    for key, value in form.items():
        if value == "":
            valid_form[key] = default_parameters[key]
        else:
            valid_form[key] = value
    try:
        if valid_form['maxResults'] > 100:
            valid_form['maxResults'] = 100
    except TypeError:
        valid_form['maxResults'] = 10
    return valid_form


def get_data(form):

    parameters = {
        "maxResults": form['maxResults'],
        "resultsFrom": 0,  # form['resultsFrom']
        "registeredOffice": form['registeredOffice'],
        "businessLineCode": form['businessLineCode'],
        "companyRegisterationFrom": form['companyRegisterationFrom'],
        "companyRegistrationTo": form['companyRegistrationTo'],
    }

    sorted_data = {}
    response = requests.get(
        "https://avoindata.prh.fi/bis/v1", params=parameters)
    try:
        data = response.json()['results']
        for item in data:
            sorted_item = sort_data(item)
            sorted_data[sorted_item['name']] = sorted_item
    except json.decoder.JSONDecodeError as js:
        print(js)
        sorted_data = {}
    return sorted_data


@ app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if len(request.form) > 0:
            valid_form = validate_form(request.form)
            sorted_data = get_data(valid_form)
            if sorted_data == {}:
                return render_template('index.html', dates=get_dates())
            else:
                results = {
                    "amount": len(sorted_data),
                    "locality": valid_form['registeredOffice'],
                    "code": valid_form['businessLineCode'],
                    "from": valid_form['companyRegisterationFrom'],
                    "to": valid_form['companyRegistrationTo']
                }
                return render_template('table.html', data=sorted_data, results=results)

    else:

        return render_template('index.html', dates=get_dates())

    # return render_template('index.html', data=get_data())


if __name__ == "__main__":
    app.run(port=8000)
    #app.run(host='127.0.0.1', port=8000, debug=True)
