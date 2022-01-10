from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from api.digital_ocean_api import DigitalOceanApi
from datetime import datetime
from __init__ import create_app, db
from models import User

import os
import sys
import time
import logging
import ansible_runner

do = DigitalOceanApi()
app = create_app()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'GET':  # if the request is a GET we return the login page
        return render_template('login.html')
    else:  # if the request is POST the we check if the user exist and with te right password
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('index'))


@login_required
@app.route('/logout')  # define logout path
def logout():  # define the logout function
    logout_user()
    return redirect(url_for('login'))


@login_required
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('.login'))
    node_list = refresh_servers()
    filename = 'server-cert.pem'
    return render_template('index.html', droplets=node_list, filename=filename)


@app.route('/static/')
def send_css():
    return app.send_static_file('website.css')


@login_required
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


@login_required
@app.route('/api/create_server', methods=['GET'])
def create_server():
    # Run the DO create server api

    do = DigitalOceanApi()
    from api.Common import ssh_gen
    public_key = ssh_gen()
    sshkey = do.add_sshkey_to_account(public_key)
    logging.info("ssh key created")
    resp = do.create_droplet(ssh_key_id=sshkey['respone']['ssh_key']['id'], tags="StrongSwan")
    logging.info(f"status_code: {resp['status_code']} message: {resp['respone']}")
    if 200 < resp['status_code'] < 205:
        node_details = do.get_droplet_by_id(resp['respone']['droplet']['id'])
        print(node_details)

        # Prearing the ansible files.
        # input file
        fin = open("ansible/hosts.template", "rt")
        # output file to write the result to
        fout = open("ansible/hosts", "wt")
        # for each line in the input file
        for line in fin:
            # read replace the string and write to output file
            fout.write(line.replace('{{IP}}', node_details['droplet']['networks']['v4'][0]['ip_address']))

        # close input and output files
        fin.close()
        fout.close()

        os.chmod('/tmp/id_rsa', 0o700)
        # Run the ansible scripts using a ip call back + ssh key from create DO server
        time.sleep(20)
        out, err, rc = ansible_runner.run_command(
            executable_cmd='ansible-playbook',
            cmdline_args=['strongswan.yml', '-i', 'hosts', '-v', '-u', 'root'],
            host_cwd='ansible/',
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
        # node_details['droplet']['id']
        return redirect(url_for('index', filename=stored_file_name))
    else:
        logging.warning(resp)
        flash(f"Could not create the strongswan server. Error Code: {resp.status}, Error Message: {resp.text}")
        return redirect(url_for('index'))


@login_required
@app.route('/api/vpncertdownload/<filename>')
def vpncert_download(filename):
    return send_from_directory('/tmp/', filename)


@login_required
@app.route('/api/delete_server', methods=['GET', 'POST'])
def delete_server():
    ids = request.form.getlist('ids')
    for dropletid in ids:
        do.delete_droplet(dropletid)
    flash(f"Successfully Deleted: {request.form.getlist('checkbox')}")
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all(app=create_app())
    # create admin user
    with app.app_context():
        user = User.query.filter_by(username=os.environ['ADMIN_USERNAME']).first()
        if not user:
            admin_user = User(username=os.environ['ADMIN_USERNAME'],
                              password=generate_password_hash(os.environ['ADMIN_PASSWORD'], method='sha256'))
            db.session.add(admin_user)
            db.session.commit()
    app.run(host="0.0.0.0", port="80")  # ssl_context="adhoc")
