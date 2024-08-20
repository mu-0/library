You will need to have a database containing users in `./instance/db.sqlite` for this to work.

## LOCAL RUN

From within this directory:

```
docker build -t testapp .
docker run --env-file env -p5001:5001 testapp
```


## HEROKU DEPLOY

From within this directory:

```
heroku login
heroku container:login
heroku container:push web -a <name of heroku app>
heroku container:release web -a <name of heroku app>
```
