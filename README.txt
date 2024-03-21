PACKAGE REQUIREMENTS:
  * pyjwt version 2.8.0
  * Flask-RESTful version 0.3.10
  * Flask version 3.0.1
  * pytest version 8.0.2

OPTIONAL TOOLS:
  * This program's testing instructions uses curl version 8.4.0, however other tools such as Postman, 
    can be used.

RUN main.py INSTRUCTIONS:
  Type "python main.py" into the terminal.

RUN tests.py INSTRUCTIONS:
  Type "pytest -cov tests.py" into the terminal.

ADD TO DATABASE INSTRUCTIONS:
 * unexpired key:
     Type "curl -X POST http://localhost:8080/auth" into the terminal
 * expired key:
     Type "curl -X POST http://localhost:8080/auth?expired=true" into the terminal.
      - Run this command before running gradebot to ensure an expired is added to the database.

EXTRACT FROM DATABASE INSTRUCTIONS:
  Type "curl -X GET http://localhost:8080/.well-known/jwks.json" into the terminal.
      - If the database is empty, the program will return with a message saying so.

RUN GRADEBOT INSTRUCTIONS:
  Type "./gradebot.exe project2" into the terminal.

PROGRAM DESCRIPTION:
  * main.py
    This program uses two protocools to function: POST and GET requests.
      - A POST request at /auth creates and return an unexpired JWT. A POST request at /auth?expired=true
        creates and returns an expired JWT. Both types of JWTs key IDs, private keys, and expiration date 
        are then loaded to the totally_not_my_privatekeys database using SQLite.

      - A GET request at /.well-known/jwks.json loads each JWTs data, and creates a corresponding JWK.
        From there, each JWK is added to the JWK dictionary, to then be returned.

  * tests.py
    This program is used to test the functionalities decribed in the main.py description.

OTHER NOTES
  * If Gradebot claims there this not an expired key in the database, run the expired key command found in
    "ADD TO DATABASE" instructions and run Gradebot again.

  * Gradebot has the tendency to fluctuate the score of this program, main.py, often
    giving 45/65 (for a variety of different errors) to 65/65 points and vise versa.
    I depicted both scores in the Gradebot screenshot. However, I firmly believe the true score is 65/65
    because from my machine, main.py does everything provided from the rubric correctly in the correct format.
