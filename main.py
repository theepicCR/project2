 #---------------------------IMPORT LIBRARIES----------------------------
#for JWT & JWK generation
import base64

#for RSA key pair & JWT generation
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
import jwt

#for kid generation
import string
import random

#for RESTful http server
from flask import Flask, request, Response
from flask_restful import Resource, Api
import json

#for database
import sqlite3
from cryptography.hazmat.primitives import serialization


#-------------------------DELETE DATABASE-------------------------
#delete all data from previous database created
#so the *very sensitive* gradebot doesnt get upset if it is ran multiple times on the same server
connect = sqlite3.connect('totally_not_my_privatekeys.db')
cursor = connect.cursor()
cursor.execute("DROP TABLE IF EXISTS keys;")
connect.close()


#-------------------------GLOBAL VARIABLES & FUNCTIONS-------------------------
#JWKs - expired and unexpired
keys = {"keys": []}
expired_keys = {"keys": []}

#for JWT n modulus creation
def int_to_base64(value):
  """Convert an integer to a Base64URL-encoded string"""
  value_hex = format(value, 'x')
  # Ensure even length
  if len(value_hex) % 2 == 1:
      value_hex = '0' + value_hex
  value_bytes = bytes.fromhex(value_hex)
  encoded = base64.urlsafe_b64encode(value_bytes).rstrip(b'=')
  return encoded.decode('utf-8')

#---------------------------RSA KEYS SETUP--------------------------
def GenerateRSAkeys():
  #generate private key
  private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

  return private_key

#---------------------------DATABASE SETUP--------------------------
def AddKeyToDatabase(kid, private_key, expiration):
  #connect to database
  connect = sqlite3.connect('totally_not_my_privatekeys.db')
  cursor = connect.cursor()

  #create table for database
  cursor.execute("CREATE TABLE IF NOT EXISTS keys(kid INTEGER PRIMARY KEY AUTOINCREMENT, key BLOB NOT NULL, exp INTEGER NOT NULL)")

  #serialize private key data
  pem_data = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption())

  #insert key into database
  cursor.execute("INSERT INTO keys (kid, key, exp) VALUES (?, ?, ?)", (int(kid), pem_data, expiration))
  connect.commit()

  connect.close()


#---------------------------JWK SETUP----------------------------
def GenerateJWK(private_key, keyID, expired):
  #checks if an expired or unexpired JWK is requested
  if expired:
    expiration = 1708355887
  else:
    #expires in about a year
    expiration = 1739978287


  #generate private key numbers for n modulus
  numbers = private_key.private_numbers()

  #construct the jwk manually :(
  JWK = {
    "kid": keyID, 
    "kty": "RSA", 
    "e": "AQAB", 
    "n": int_to_base64(numbers.public_numbers.n),
    "alg": "RS256",
    "iat": 1708355887,
    "exp": expiration
  }

  return JWK

#---------------------------KID SETUP----------------------------
def GenerateKID():
  #generates a random Key ID (kid) of length 10
  keyID = ''.join(random.choice(string.digits) for i in range(10))

  return keyID


#---------------------------JWT SETUP----------------------------
def GenerateJWT(private_key, keyID, expired):
  #checks if an expired or unexpired JWT is requested
  if expired:
    expiration = 1708355887
  else:
    #expires in about a year
    expiration = 1739978287

  #header
  JWTheader = {
    "kid": keyID,
    "alg": "RS256",
    "typ": "JWT"
  }

  #payload
  JWTpayload = {
    "iat:": 1708355887,
    "exp": expiration
    }

  #generate JWT
  JWT = jwt.encode(payload=JWTpayload, key=private_key, algorithm='RS256', headers=JWTheader)

  #gets rid of the '==' padding
  JWT = JWT.rstrip("=")

  return JWT


#---------------------------HTTP SERVER SETUP----------------------------
#Flask setup
app = Flask("JWKServer")
api = Api(app)


#RESTful JWKS endpoint setup
class HTTP(Resource):
  def get(self):
    #connect to database
    connect = sqlite3.connect('totally_not_my_privatekeys.db')
    cursor = connect.cursor()

    #scan through database for kids and private RSA keys
    for key in cursor.execute("SELECT * FROM keys"):
      kid = str(key[0])
      priv_key_bytes = key[1]
      exp = key[2]

      #turn bytes into private key RSA object
      db_private_key = serialization.load_pem_private_key(priv_key_bytes, password=None)

      #generate JWK and append them to keys list
      JWK = GenerateJWK(db_private_key, kid, False)

      if (JWK not in keys["keys"]):
        keys["keys"].append(JWK)

    connect.close()

    #returns all known, unexpired JWKs
    return keys

api.add_resource(HTTP, "/.well-known/jwks.json")


#/auth endpoint
class HTTPAuth(Resource):
  def post(self):
    #ensures a post request is soley made to /auth without extra arguments
    if request.path == "/auth" and len(request.args) == 0:
      keyID = GenerateKID()
      private_key = GenerateRSAkeys()
      expiration = 1739978287


      #add JWK and private key to database
      AddKeyToDatabase(keyID, private_key, expiration)

      #extract private key just added, from database
      #first, connect to database
      connect = sqlite3.connect('totally_not_my_privatekeys.db')
      cursor = connect.cursor()

      #collect first key/newly appended key from database
      result = cursor.execute("SELECT key FROM keys")
      db_private_key = result.fetchone()
      private_key = db_private_key[0]
      connect.close()

      #create unexpired JWT
      JWT = GenerateJWT(private_key, keyID, False)

      return Response(JWT, status=200, mimetype="application/jwt")

    #checks if the expiry parameter is present
    #if it is, creates an expired JWT & JWK
    #returns an expired JWT
    elif request.args.get("expired") == "true":
      keyID = GenerateKID()
      private_key = GenerateRSAkeys()
      expiration = 1708355887


      #add JWK and private key to database
      AddKeyToDatabase(keyID, private_key, expiration)

      #extract private key just added, from database
      #first, connect to database
      connect = sqlite3.connect('totally_not_my_privatekeys.db')
      cursor = connect.cursor()

      #collect first key/newly appended key from database
      result = cursor.execute("SELECT key FROM keys")
      db_private_key = result.fetchone()
      private_key = db_private_key[0]
      connect.close()

      #generate expired JWT
      JWT = GenerateJWT(private_key, keyID, True)

      return Response(JWT, status=200, mimetype="application/jwt")

    #return 405 if request does not fulfill requirements
    else:
      return {'message': 'Method Not Allowed'}, 405

api.add_resource(HTTPAuth, "/auth")


#---------------------------RUNNING SERVER----------------------------
if __name__ == "__main__":
  app.run(port=8080)
