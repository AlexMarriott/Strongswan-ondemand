 Get a working Stongswan server
 Using the config files, get a ansible version which deploys static files for strongswan
 Next will be to take the values of the running server and template it across a new instance each time
 Note, this will use selfsigned CA. Could also add a way of using windows CA for furture
 For testing purposes, you can install apache2 on the DO server and then change the listen directive in the ports.conf file to a private address to verify you can connect to that ip address.


# Strongswan Packages
sudo apt update && sudo apt install strongswan strongswan-pki libcharon-extra-plugins libcharon-extauth-plugins libstrongswan-extra-plugins

# Create the local ipsec key directories
mkdir -p ~/pki/{cacerts,certs,private}
chmod 700 ~/pki

# Generating the server root key
pki --gen --type rsa --size 4096 --outform pem > ~/pki/private/ca-key.pem

pki --self --ca --lifetime 3650 --in ~/pki/private/ca-key.pem --type rsa --dn "CN=VPN root CA" --outform pem > ~/pki/cacerts/ca-cert.pem

# Generating the server certificate
pki --gen --type rsa --size 4096 --outform pem > ~/pki/private/server-key.pem

# Signing the new root certificate./
# This is where we do our first drop in replacement, the IP address will be swaped out each time a new server is created.
pki --pub --in ~/pki/private/server-key.pem --type rsa | pki --issue --lifetime 1825 --cacert ~/pki/cacerts/ca-cert.pem --cakey ~/pki/private/ca-key.pem --dn "CN=46.101.43.136" --san @46.101.43.136 --san 46.101.43.136 --flag serverAuth --flag ikeIntermediate --outform pem >  ~/pki/certs/server-cert.pem

# Moving the certificates to the ipsec directory
sudo cp -r ~/pki/* /etc/ipsec.d/

# Backing up the original files, (optional)
sudo mv /etc/ipsec.conf{,.original}

# Edit and create the new ipsec.conf
 sudo vim /etc/ipsec.conf
 This can be found in the strongswan/ipsec.conf

# Next, we need to create a ipsec.secrets file
sudo vim /etc/ipsec.secrets
 This can be found in the strongswan/ipsec.conf

# Next the strongswan service needs a restart.
sudo systemctl restart strongswan-starter

# Now we need to config the UFW rules
sudo ufw allow OpenSSH

# Need to skip the prompt
sudo ufw enable

# ipsec taffic is 500 & 4500/udp
sudo ufw allow 500,4500/udp,80


# Need to checkl what interface is used for the public ip address.
ip route show default

# Now we need to edit the /etc/ufw/before.rules file, we should sed the new lines in.
vim /etc/ufw/before.rules

# Now we need to enable packet forwarding to the server, sed should be used again.
vim /etc/ufw/sysctl.conf

 uncomment: net/ipv4/ip_forward=1
 add: net/ipv4/conf/all/accept_redirects=0
 add: net/ipv4/conf/all/send_redirects=0
 add: net/ipv4/ip_no_pmtu_disc=1

# Now reload ufw.
sudo ufw disable
# skip the prompt again
sudo ufw enable









# Ipsec conf
# Server
# Left is me, the Server
# Right is the remote, the Phone

# Phone
# Left is me, the phone
# Right is the remote, the Server


# references
# https://www.digitalocean.com/community/tutorials/how-to-set-up-an-ikev2-vpn-server-with-strongswan-on-ubuntu-20-04 <-- Strongswan server conf
# https://github.com/ansible/ansible-examples/tree/master/wordpress-nginx
# https://docs.ansible.com/ansible/latest/user_guide/playbooks_templating.html

# TODO
# Make this deployable on the fly with ansible
# Make this code which can be ran from a local server / Authenicated login on my webpage which lets me create a strongswan server on the fly with ansible.
