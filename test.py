
from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os
import datetime


app = Flask(__name__)
# parameters = {
#       "maxResults": 10,
#       "resultsFrom": 0,
#       "registeredOffice": "Helsinki",
#       "businessLineCode": 68310,
#       "companyRegisterationFrom": "2019-01-01",
#       "companyRegistrationTo": str(datetime.date.today())
#   }


def sort_data(data):

    _id = data['businessId']
    name = data['name']
    registered = data['registrationDate']
    company_form = data['companyForm']
    details = data['detailsUri']

    response = requests.get(details)
    detail_data = response.json()['results']
    # print(detail_data)
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
        # phone_num = detail_data[0]['contactDetails'][0]['value']

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


def get_data(form):

    parameters = {
        "maxResults": form['maxResults'],
        "resultsFrom": 0,  # form['resultsFrom']
        "registeredOffice": form['registeredOffice'],
        "businessLineCode": form['businessLineCode'],
        "companyRegisterationFrom": form['companyRegisterationFrom'],
        "companyRegistrationTo": form['companyRegistrationTo'],
    }
    # parameters = {
    #    "maxResults": 10,
    #    "resultsFrom": 0,
    #    "registeredOffice": "Helsinki",
    #    "businessLineCode": 68310,
    #    "companyRegisterationFrom": "2019-01-01",
    #    "companyRegistrationTo": str(datetime.date.today())
    # }

    sorted_data = {}
    response = requests.get(
        "https://avoindata.prh.fi/bis/v1", params=parameters)
    data = response.json()['results']

    for item in data:
        sorted_item = sort_data(item)
        sorted_data[sorted_item['name']] = sorted_item
    return sorted_data


@ app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if len(request.form) > 0:

            sorted_data = get_data(request.form)
            print(len(sorted_data))
            results = {
                "amount": len(sorted_data),
                "locality": request.form['registeredOffice'],
                "code": request.form['businessLineCode'],
                "from": request.form['companyRegisterationFrom'],
                "to": request.form['companyRegistrationTo']
            }
            return render_template('table.html', data=sorted_data, results=results)

    else:
        return render_template('index.html')

    # return render_template('index.html', data=get_data())


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
