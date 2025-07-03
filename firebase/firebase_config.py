import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("firebase/vaultcoin_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://vaultcoin-87145-default-rtdb.firebaseio.com/'
})

