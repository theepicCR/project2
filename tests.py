#import libraries
import pytest
import json
import re
import sqlite3
from main import app


#testing /.well-known/jwks.json endpoint with GET method
def testJwksJsonGET():
  #checks if status code is 200, if data is valid JWK,
  #and if type is application/json
  with app.test_client() as client:
    response = client.get('/.well-known/jwks.json')
    assert response.status_code == 200

    #check if JWK is in proper JWK format & includes a kid & all are unexpired
    regex = b'^{"keys":.*"kid":.*"exp": 1739978287.*}\n$'
    assert re.match(regex, response.data)
    assert response.mimetype == 'application/json'


#testing /.well-known/jwks.json endpoint with POST method
def testJwksJsonPOST():
  #checks if status code is 405
  with app.test_client() as client:
    response = client.post('/.well-known/jwks.json')
    assert response.status_code == 405


#testing auth endpoint by itself with GET method
def testAuthGET():
  #checks if status code is 405
  with app.test_client() as client:
    response = client.get('/auth')
    assert response.status_code == 405


#testing auth endpoint by itself with POST method
def testAuthPOST():
  #checks if status code is 200, if data is JSON decodable,
  #and if type is application/json
  with app.test_client() as client:
    response = client.post('/auth')
    assert response.status_code == 200
    assert response.mimetype == 'application/jwt'


#testing /auth endpoint with expiry parameter with GET method
def testAuthExpGET():
  #checks if status code is 405
  with app.test_client() as client:
    response = client.get('/auth?expired=true')
    assert response.status_code == 405


#testing /auth endpoint with expiry parameter with POST method
def testAuthExpPOST():
  #checks if status code is 200, if data is JSON decodable,
  #and if type is application/json
  with app.test_client() as client:
    response = client.post('/auth?expired=true')
    assert response.status_code == 200
    assert response.mimetype == 'application/jwt'


#checks if the database file exists in the current directory
def testDBFileExists():
  assert open('totally_not_my_privatekeys.db', 'r')


#checks if the database actually contains keys
def testDBHasKeys():
  connect = sqlite3.connect('totally_not_my_privatekeys.db')
  cursor = connect.cursor()
  #checks if database has keys
  assert cursor.execute("SELECT * FROM keys").fetchall()
  connect.close()


#checks if the database has at least one expired key
def testDBHasExpiredKey():
  connect = sqlite3.connect('totally_not_my_privatekeys.db')
  cursor = connect.cursor()
  assert cursor.execute("SELECT * FROM keys WHERE exp = 1708355887").fetchall()
  connect.close()


#checks if database has at least one unexpired key
def testDBHasUnexpiredKey():
  connect = sqlite3.connect('totally_not_my_privatekeys.db')
  cursor = connect.cursor()
  assert cursor.execute("SELECT * FROM keys WHERE exp = 1739978287").fetchall()
  connect.close()

  
#calling test functions
testAuthGET()
testAuthPOST()
testAuthExpGET()
testAuthExpPOST()
testJwksJsonGET()
testJwksJsonPOST()
testDBFileExists()
testDBHasKeys()
testDBHasExpiredKey()
testDBHasUnexpiredKey()
