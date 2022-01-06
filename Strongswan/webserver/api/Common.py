def ssh_gen():
    def write_file_bytes(**kwargs):
        for file, bytes in kwargs.items():
            if file == "private_key":
                ssh_file_location = "/tmp/id_rsa"

            else:
                ssh_file_location = "/tmp/id_rsa.pub"
            with open(ssh_file_location, "wb") as f:
                f.write(bytes)
                f.close()

    from cryptography.hazmat.primitives import serialization as crypto_serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend as crypto_default_backend

    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )

    write_file_bytes(private_key=private_key, public_key=public_key)

    return public_key.decode("utf-8")
