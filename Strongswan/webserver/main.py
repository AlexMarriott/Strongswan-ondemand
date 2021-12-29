from flask import Flask, render_template, request, redirect, url_for, flash
from api.digital_ocean_api import DigitalOceanApi
from datetime import datetime

import uuid
import os

#from database import DataBase


app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

do = DigitalOceanApi()
@app.route('/')
def index():
    node_list = refresh_servers()
    return render_template('index.html', droplets=node_list)

@app.route('/static/')
def send_css():
    return app.send_static_file('website.css')

@app.route('/api/refresh_servers')
def refresh_servers():
    # Return  the status of all running servers
    droplets = do.list_droplets()
    node_list = []
    for droplet in droplets:
        node_list.append({'id': droplet['id'], 'name': droplet['name'],
                          'ip_address': droplet['networks']['v4'][0]['ip_address'],
                          'date_created': datetime.strptime(droplet['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                          'status': droplet['status']})
    return node_list

@app.route('/api/create_server', methods=['GET'])
def create_server():
    #try:
    req = request.get_json()
    print(req)
    #except as Ex

    # Run the DO create server api
    do = DigitalOceanApi()
    from api.Common import ssh_gen
    public_key = ssh_gen()
    sshkey = do.add_sshkey_to_account(public_key)

    do.create_droplet(ssh_key_id=sshkey['respone']['ssh_key']['id'], tags="StrongSwan")
    return redirect(url_for('index'))

# Run the ansible scripts using a ip call back + ssh key from create DO server

# Return the CA certificate + username + password


@app.route('/api/delete_server', methods=['GET','POST'])
def delete_server():
    ids = request.form.getlist('ids')
    for dropletid in ids:
        do.delete_droplet(dropletid)
    flash(f"Successfully Deleted: {request.form.getlist('checkbox')}")
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(host="0.0.0.0", port="80") #ssl_context="adhoc")
