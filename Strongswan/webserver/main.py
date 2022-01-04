import sys
import time

from flask import Flask, render_template, request, redirect, url_for, flash,send_from_directory
from api.digital_ocean_api import DigitalOceanApi
from datetime import datetime

import uuid
import os
import ansible_runner

#from database import DataBase


app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

do = DigitalOceanApi()
@app.route('/')
def index():
    node_list = refresh_servers()
    filename = 'server-cert.pem'
    return render_template('index.html', droplets=node_list, filename=filename)

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
    # Run the DO create server api

    do = DigitalOceanApi()
    from api.Common import ssh_gen
    public_key = ssh_gen()
    sshkey = do.add_sshkey_to_account(public_key)

    resp = do.create_droplet(ssh_key_id=sshkey['respone']['ssh_key']['id'], tags="StrongSwan")
    print(resp)
    if 200 < resp['status_code'] < 205:
        node_details = do.get_droplet_by_id(resp['respone']['droplet']['id'])
        print(node_details)

        # Prearing the ansible files.
        # input file
        fin = open("../ansible/hosts.template", "rt")
        # output file to write the result to
        fout = open("../ansible/hosts", "wt")
        # for each line in the input file
        for line in fin:
            # read replace the string and write to output file
            fout.write(line.replace('{{IP}}', node_details['droplet']['networks']['v4'][0]['ip_address']))

        # close input and output files
        fin.close()
        fout.close()

        os.chmod('/tmp/id_rsa', 0o700)
        #Run the ansible scripts using a ip call back + ssh key from create DO server
        time.sleep(20)
        out, err, rc = ansible_runner.run_command(
                    executable_cmd='ansible-playbook',
                    cmdline_args=['strongswan.yml', '-i', 'hosts','-v', '-u',  'root'],
                    host_cwd='../ansible',
                    input_fd=sys.stdin,
                    output_fd=sys.stdout,
                    error_fd=sys.stderr,
                )
        print("rc: {}".format(rc))
        print("out: {}".format(out))
        print("err: {}".format(err))
        # Return the CA certificate + username + password
        stored_file_name = 'server-cert.pem'
        # TODO make a vpn key for each running server
        #node_details['droplet']['id']
        return redirect(url_for('index', filename=stored_file_name))

@app.route('/api/vpncertdownload/<filename>')
def vpncert_download(filename):
    return send_from_directory('/tmp/', filename)


@app.route('/api/delete_server', methods=['GET','POST'])
def delete_server():
    ids = request.form.getlist('ids')
    for dropletid in ids:
        do.delete_droplet(dropletid)
    flash(f"Successfully Deleted: {request.form.getlist('checkbox')}")
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(host="0.0.0.0", port="80") #ssl_context="adhoc")
