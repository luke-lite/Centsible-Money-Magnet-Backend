import pyotp
import qrcode

def createNewURI(username):
    key = pyotp.random_base32()

    uri = pyotp.totp.TOTP(key).provisioning_uri(name = username, issuer_name="Money Magnet")
    return uri

def authenticateUser(OPTkey, OTPcode):
    totp = pyotp.TOTP(key)
    totp.verify()


key = "testetststasdkatfdyta"

# uri = pyotp.totp.TOTP(key).provisioning_uri(name = "test", issuer_name="Money Magnet")
# qrcode.make(uri).save("totp.png")

totp = pyotp.TOTP(key)

while True:
    print(totp.verify(input("Enter")))