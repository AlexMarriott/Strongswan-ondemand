import logging
import random

import requests
import json
import time
import os


from .Common import ssh_gen
"""
"""
class DigitalOceanApi:
    from sshpubkeys import SSHKey, InvalidKeyError

    def __init__(self):
        self.access_token = os.environ['DO_access_token']
        self.session = requests.Session()
        self.session.headers = {"Authorization": "Bearer {0}".format(self.access_token)}
        self.url = "https://api.digitalocean.com/v2"

    def poll_droplet(self, droplet_id, wait_timer=0):
        while wait_timer < 30:
            print(f"wait timer is: {wait_timer}")
            resp = self.session.get(f"{self.url}/droplets/{droplet_id}/actions/")
            actions = json.loads(resp.text)["actions"]

            print(actions[0])
            if actions[0]["completed_at"] is not None and actions[0]['type'] in ['create', 'delete']:
                return True
            else:
                time.sleep(1)
                wait_timer += 1

        return False

    def create_droplet(self, name="Strongswan.internal.ain", ssh_key_id="", tags=""):
        data = {
            "name": name,
            "region": "lon1",
            "size": "s-1vcpu-1gb",
            "image": "ubuntu-20-04-x64",
            "ssh_keys": [ssh_key_id],
            "tags": [tags]
        }
        resp = self.session.post("{0}/droplets/".format(self.url), data=data)
        print(resp.status_code)
        if resp.status_code == 202:
            # polling the status of the server
            poll_server = self.poll_droplet(json.loads(resp.text)['droplet']['id'])
            if poll_server:
                return {"status_code": resp.status_code, "respone": json.loads(resp.text)}
            else:
                # Something went wrong when trying to create the server
                return {"status_code": 500, "respone": "Something happened to the server when creating it."}
        else:
            # Digital ocean did not like the request we sent it.
            return {"status_code": resp.status_code, "respone": json.loads(resp.text)}

    def add_sshkey_to_account(self, ssh_public_key):
        try:
            # Checking to see if the public key is legit
            ssh = self.SSHKey(ssh_public_key)
            ssh.parse()
            name = f"strongswan-{random.getrandbits(128)}"
            # If the key is good, we add to the account.
            data = {"name": name, "public_key": ssh_public_key}
            resp = self.session.post("{0}/account/keys".format(self.url), json=data)
            return {"status_code": resp.status_code, "respone": json.loads(resp.text)}

        except self.InvalidKeyError as err:
            print(f"Invalid Key: {err}")
            logging.warning(f"Invalid Key: {err}")
            return False
        except NotImplementedError as err:
            print(f"Invalid Key type: {err}")
            logging.warning(f"Invalid Key type: {err}")
            return False

    def delete_droplet(self, droplet_id):
        resp = self.session.delete(f"{self.url}/droplets/{droplet_id}")
        if resp.status_code == 204:
            return {"status_code": resp.status_code}

    def delete_droplets_by_tag(self, tag):
        resp = self.session.delete(f"{self.url}/droplets?tag_name={tag}")
        return {"status_code": resp.status_code}

    def get_droplet(self, droplet_name):
        nodes = self.list_droplets()
        for i in nodes:
            if i['name'] == droplet_name:
                return json.loads(self.session.get(f"{self.url}/droplets/{i['id']}").text)

    def get_all_sshkeys(self):
        return json.loads(self.session.get(f"{self.url}/account/keys/").text)['ssh_keys']

    def list_droplets(self):
        droplets = []
        resp = self.session.get(f"{self.url}/droplets/")
        json_resp = json.loads(resp.text)

        for i in json_resp['droplets']:
            droplets.append(i)
        return droplets

    def delete_ssh_key(self, ssh_key_name):
        ssh_keys = self.get_all_sshkeys()
        for key in ssh_keys:
            if key['name'] == ssh_key_name:
                resp = self.session.delete(f"{self.url}/account/keys/{key['id']}")
                if resp.status_code == 204:
                    return {"status_code": resp.status_code}

        return {"status_code": 404}

    def delete_all_ssh_keys(self):
        ssh_keys = self.get_all_sshkeys()
        for key in ssh_keys:
            resp = self.session.delete(f"{self.url}/account/keys/{key['id']}")
            if resp.status_code == 204:
                logging.info(f"sshkey: {key['name']} removed, status code: {resp.status_code}")
            else:
                print(f"sshkey: {key['name']} could not be deleted... status code: {resp.status_code}")
                logging.warning(f"sshkey: {key['name']} could not be deleted... status code: {resp.status_code}")
                return {"status_code": resp.status_code, "respone": resp.text}
        return True