import requests
import json
import os
import datetime
# ?totalResults=false&maxResults=20&resultsFrom=0&registeredOffice=helsinki&businessLine=kiinteist%C3%B6nv%C3%A4litys&businessLineCode=68310&companyRegistrationFrom=2020-02-20"
parameters = {
    "maxResults": 1,
    "resultsFrom": 0,
    "registeredOffice": "Helsinki",
    "businessLineCode": 68310,
    "companyRegisterationFrom": "2019-01-01",
    "companyRegistrationTo": str(datetime.date.today())
}


def get_data():
    response = requests.get(
        "https://avoindata.prh.fi/bis/v1", params=parameters)
    data = response.json()['results']
    # print(data)
    # print(response.text)
    sorted_data = {}

    with open('testi.txt', 'w+') as text_file:
        #    text_file.write()

        for object in data:
            name = object['name']
            _id = object['businessId']
            registered = object['registrationDate']
            company_form = object['companyForm']
            details = object['detailsUri']

            s = ("{}: [ {}       y-tunnus: {}{}       rekisteröity: {}{}       yritysmuoto: {}{}]{} ").format(
                name, os.linesep, _id, os.linesep, registered, os.linesep, company_form, os.linesep, os.linesep)
            text_file.write(s)
            # s = ("{}: [ {}       y-tunnus: {}{}       rekisteröity: {}{}       yritysmuoto: {}{}       lisätietoja: {}{}]{} ").format(
            #    name, os.linesep, _id, os.linesep, registered, os.linesep, company_form, os.linesep, details, os.linesep, os.linesep)
            # text_file.write(s)

            sorted_data[name] = {
                "id": _id, "registered": registered, "company form": company_form}

    #a = json.dumps(sorted_data)
    #sorted_data += s
    # print(sorted_data)


get_data()
