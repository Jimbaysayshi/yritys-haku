
from flask import Flask, render_template, request, redirect, url_for, current_app, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import json
import os
import datetime
import xlwt
import uuid
import time
import atexit

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads/'


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
       
        valid_form['maxResults'] =  int(valid_form['maxResults'])
        if valid_form['maxResults'] > 100:
            valid_form['maxResults'] = 100
    except TypeError:
        valid_form['maxResults'] = 10
    
    #print(valid_form)
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

        sorted_data = {}
    return sorted_data


def create_wb(data, path):
    now = time.time()
    workbook = xlwt.Workbook()
    wb = workbook.add_sheet('wb')
    titles = ['Name', 'Founder', 'Registered', 'Locality', 'Post code', 'Address',
              'Business line', 'Phone num', 'Mobile num', 'Website', 'Company form']
    bold = xlwt.easyxf('font: bold 1')
    for i, title in enumerate(titles):
        wb.write(0, i, title, bold)
    i = 1
    for company, values in data.items():
        x = 0
        wb.write(i, x, values['name'])
        wb.write(i, x + 1, values['founder'])
        wb.write(i, x + 2, values['registered'])
        wb.write(i, x + 3, values['locality'])
        wb.write(i, x + 4, values['post_code'])
        wb.write(i, x + 5, values['first_address'])
        wb.write(i, x + 6, values['business_line'])
        wb.write(i, x + 7, values['phone_num'])
        wb.write(i, x + 8, values['mobile_num'])
        wb.write(i, x + 9, values['website'])
        wb.write(i, x + 10, values['company_form'])
        i += 1

    try:
        workbook.save(path)
    except TypeError as te:
        pass


@ app.route("/uploads/<path:filename>", methods=['GET', 'POST'])
def download(filename):
    if os.path.isfile(app.config['UPLOAD_FOLDER'] + filename):
        uploads = os.path.join(current_app.root_path,
                               app.config['UPLOAD_FOLDER'])
        return send_from_directory(directory=uploads, filename=filename)
    else:
        pass
        # TODO something went wrong 404


@ app.route("/", methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        if len(request.form) > 0:
            valid_form = validate_form(request.form)
            sorted_data = get_data(valid_form)
            if sorted_data == {}:
                return render_template('index.html', dates=get_dates())
            else:
                uu_id = uuid.uuid4()
                filename = uu_id.hex + ".xls"
                results = {
                    "amount": len(sorted_data),
                    "locality": valid_form['registeredOffice'],
                    "code": valid_form['businessLineCode'],
                    "from": valid_form['companyRegisterationFrom'],
                    "to": valid_form['companyRegistrationTo'],
                    "filename": filename
                }

                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                create_wb(sorted_data, path)
                return render_template('table.html', data=sorted_data, results=results)

    else:

        return render_template('index.html', dates=get_dates())

    # return render_template('index.html', data=get_data())


def scheduled_delete():
    now = time.time()
    path = app.config['UPLOAD_FOLDER']
    for f in os.listdir(path):
        real_path = os.path.join(path, f)
        if os.stat(real_path).st_mtime < now - 15 * 60:
            os.remove(real_path)


scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_delete, trigger="interval", minutes=15)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    #app.run(port=8000)
    app.run(host='127.0.0.1', port=8000, debug=False)
