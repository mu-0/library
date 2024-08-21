I didn't document any of my build or deploy process, and redoing this from scratch is going to be simpler than attempting to modify it in place. This time for real!

Outline 
- Flask app 
  - Database on Heroku
  - Files on AWS S3
- Built as a single Docker image
- Served with Gunicorn

Step 1: minimum viable docker/gunicorn/flask/heroku app

Starting from `demos/heroku_flask_gunicorn_docker` satisfies this.

Step 2: minimum viable login manager

Brought in from `demos/flask/authentication`

Step 3: serve books

Done


---

To do:
- see app.py notes about better database management
- env audit
