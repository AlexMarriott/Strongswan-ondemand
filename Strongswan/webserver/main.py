from flask import Flask, render_template
from api.digital_ocean_api import DigitalOceanApi
from datetime import datetime

import os

#from database import DataBase

app = Flask(__name__)
do = DigitalOceanApi()
@app.route('/')
def index():
    droplets = do.list_droplets()
    node_list = []
    for droplet in droplets:
        print(droplet)
        node_list.append({'id': droplet['id'], 'name': droplet['name'],
                          'ip_address': droplet['networks']['v4'][0]['ip_address'],
                          'date_created': datetime.strptime(droplet['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                          'status': droplet['status']})
    return render_template('index.html', droplets=node_list)

@app.route('/static/')
def send_css():
    return app.send_static_file('website.css')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="80") #ssl_context="adhoc")
