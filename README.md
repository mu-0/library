I didn't document any of my build or deploy process, and redoing this from scratch is going to be simpler than attempting to modify it in place. This time for real!

Outline 
- Flask app 
  - Database on Heroku
  - Files on AWS S3
- Built as a single Docker image
- Served with Gunicorn

Step 1: minimum viable docker/gunicorn/flask/heroku app