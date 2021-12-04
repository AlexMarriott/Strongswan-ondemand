import os
import logging
import random
from time import sleep

from Common import ssh_gen


class Droplet:
    def __init__(self, droplet_id, droplet_name, droplet_ip, droplet_tag=None, ssh_key=None):
        self.droplet_id = droplet_id
        self.droplet_tag = droplet_tag
        self.droplet_name = droplet_name
        self.droplet_ip = droplet_ip
        self.ssh_key = ssh_key


class DigitalOceanAPI:
    import digitalocean
    from sshpubkeys import SSHKey, InvalidKeyError

    def __init__(self):
        self.manager = self.digitalocean.Manager(token=os.environ['DIGITALOCEAN_ACCESS_TOKEN'])

    def tag_server(self, tag_name, droplet_id):
        tag = self.digitalocean.Tag(self.manager.token, name=tag_name)
        tag.create()  # create tag if not already created
        tag.add_droplets([droplet_id])
        pass

    def poll_droplet(self, droplet):
        poll_count = 0
        while poll_count < 10:
            actions = droplet.get_actions()
            for action in actions:
                action.load()
                # Once it shows "completed", droplet is up and running
                if action.status == "completed":
                    return True
                else:
                    poll_count += 1
                    print(f"Waiting for server...... Time: {poll_count} seconds")
                    sleep(1)
        return False

    def get_all_servers_by_tag(self, tag_name):
        droplets = self.manager.get_all_droplets(tag_name=tag_name)
        return droplets

    def load_droplet(self,droplet_id):
        droplet = self.digitalocean.Droplet(token=self.manager.token)


    def add_sshkey_to_account(self, ssh_public_key):
        try:
            # Checking to see if the public key is legit
            ssh = self.SSHKey(ssh_public_key)
            ssh.parse()
            name = f"strongswan-{random.getrandbits(128)}"
            # If the key is good, we add to the account.
            key = self.digitalocean.SSHKey(self.manager.token,
                                           name=name,
                                           public_key=ssh_public_key)
            key.create()
            return name
        except self.InvalidKeyError as err:
            print(f"Invalid Key: {err}")
            logging.warning(f"Invalid Key: {err}")
            return False
        except NotImplementedError as err:
            print(f"Invalid Key type: {err}")
            logging.warning(f"Invalid Key type: {err}")
            return False

    def get_ssh_key_by_name(self, name):
        keys = self.manager.get_all_sshkeys()
        for key in keys:
            if key.name == name:
                return key
        return False

    def create_droplet(self, name=f'StrongSwan.ain.internal', region='LON1', ssh_key=""):
        droplet = self.digitalocean.Droplet(token=self.manager.token,
                                            name=name,
                                            region=region,
                                            image='ubuntu-20-04-x64',
                                            size_slug='s-1vcpu-1gb',
                                            ssh_key=ssh_key,
                                            backups=False,
                                            tags="Strongswan")

        droplet.create()

        return self.poll_droplet(droplet)

    def delete_droplet(self, droplet):
        print("deleting Droplet")
        droplet.destroy()

    def delete_ssh_key(self, key):
        print("deleting sshkey")
        key.destroy()



"""
# example
do = DigitalOceanAPI()
public_key = ssh_gen()
public_key_name = do.add_sshkey_to_account(public_key)
ssh_key = do.get_ssh_key_by_name(public_key_name)
do.create_droplet(ssh_key=ssh_key)

droplets_to_destory = do.get_all_servers_by_tag("Strongswan")

for droplet in droplets_to_destory:
    do.delete_droplet(droplet)
do.delete_ssh_key(ssh_key)
"""
