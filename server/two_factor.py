import pyotp


def createNewURI(user_name):
    key = pyotp.random_base32()

    uri = pyotp.totp.TOTP(key).provisioning_uri(name = user_name, issuer_name="Money Magnet")
    return key, uri

def authenticateUser(OTPkey, OTPcode):
    totp = pyotp.TOTP(OTPkey)
    return totp.verify(OTPcode)
