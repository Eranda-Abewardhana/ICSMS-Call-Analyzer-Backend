import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

# Path to your service account JSON file
cred = credentials.Certificate("E:\Personal\Python\ICSMS-Call-Analyzer-Backend\service-account.json")
firebase_admin.initialize_app(cred)

# access_token = cred.get_access_token().access_token
# print(f"Access Token: {access_token}")


def send_message():
    # This registration token comes from the client FCM SDKs.
    registration_token = 'fgXgJ2Tb2zLTuvawQEO8Vi:APA91bEPGrpcY3U7P-dkPG2y0KAHz9T1Zh0exbWN1RH5qRLF0piLdsJYalTk-QTKFUcKAZyqCZ10w5GNaAzRZ3ApZUqF3iG3nhAFJcdifql_sxRV78L1oR9YnzMjJvLC6uNCX6D3ekr7'

    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=messaging.Notification(
            title='Test Notification',
            body='This is a test notification from Python Admin SDK',
        ),
        token=registration_token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send(message)
    # Response is a message ID string.
    print('Successfully sent message:', response)
