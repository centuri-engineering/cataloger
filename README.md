# Cataloger

A biology experiment metadata filling service (with an emphasis on microscopy)

## Screenshots

### Card collection

![Cards view](assets/img/cards_view.png)


### Card edition

![Cards edition](assets/img/card_edition1.png)

![Cards edition](assets/img/card_edition2.png)


## Install

### Install docker for your platform

### Grab an API key at Bioportal

### Write a .env file

Bellow is an example of .env file - user management is easier if
it is delegated to OMERO, so if you have an OMERO server choose this.

For now, local user management will not allow any control over who logs in.

If you (unfortunately) need to use LDAP, I found that the `ldap3`
python module was very helpfull in a interactive session to discover a ldap server idiosyncrasies.


```sh
# Environment variable overrides for local development
FLASK_APP=autoapp.py
FLASK_DEBUG=0
FLASK_ENV=production

POSTGRES_USER=cataloger
POSTGRES_DB=cataloger
POSTGRES_PASSWORD=Cattta10ger

DATABASE_URL=postgresql+psycopg2://cataloger:Cattta10ger@cataloger_db/cataloger
GUNICORN_WORKERS=1
LOG_LEVEL=debug
SECRET_KEY="secret"
# In production, set to a higher number, like 31556926
SEND_FILE_MAX_AGE_DEFAULT=31556926
BIOPORTAL_API_KEY="aaaaaaaa-zzzz-aaaa-aaaa-aaaaaaaaa"

AUTH_METHOD="OMERO" #  "LDAP", "OMERO" or "LOCAL"
## LDAP
LDAP_PORT=3268
LDAP_HOST="10.2.4.2"
LDAP_READONLY=true
LDAP_BIND_DIRECT_PREFIX=""
LDAP_BASE_DN="dc=example,dc=com"
LDAP_BIND_USER_DN="admin"
LDAP_BIND_USER_PASSWORD=""
LDAP_USER_LOGIN_ATTR="sAMAccountName"
LDAP_USER_RDN_ATTR="sAMAccountName"
LDAP_USER_DN="ou=ibdml"
LDAP_USER_SEARCH_SCOPE="SUBTREE"
LDAP_USER_OBJECT_FILTER="(objectclass=person)"
LDAP_USE_SSL=false
LDAP_CHECK_NAMES=true
LDAP_BIND_DIRECT_CREDENTIALS=false
LDAP_BIND_DIRECT_SUFFIX=""
LDAP_BIND_DIRECT_GET_USER_INFO=true
LDAP_ALWAYS_SEARCH_BIND=true
LDAP_SEARCH_FOR_GROUPS=false
LDAP_FAIL_AUTH_ON_MULTIPLE_FOUND=false
LDAP_BIND_AUTHENTICATION_TYPE=SIMPLE
LDAP_GET_USER_ATTRIBUTES="*"
LDAP_ADD_SERVER=true

## OMERO
OMERO_HOST="localhost"
OMERO_PORT="4064"
```
### Create host-side directories

(Those are refered to in the `docker-compose.yml` file, you can change their values there).

```bash
mkdir ~/data/
mkdir ~/data/cataloger # Will contain the db
mkdir ~/data/backups
mkdir ~/data/backups/cataloger # For db backups
```

### Initialze

You first need to create and initalize de database, by entering the 3 following lines:

```bash
docker-compose run --rm manage db init
docker-compose run --rm manage db migrate
docker-compose run --rm manage db upgrade
```

After updates to the service, if the db changes, you'll need to run
the two last lines to update your database.


### Run the developement version

To run the development version of the app

```bash
docker-compose up flask-dev
```

To run the production version of the app

You should be able to see your app by visiting http://localhost:5020


### Deploying


You can run the production version with:

```bash
docker-compose up flask-prod
```

I (@glyg) use caddy as a reverse proxy service and to provide https, it is very lightweight.



## flask cookie-cutter documentation


## Docker Quickstart

This app can be run completely using `Docker` and `docker-compose`. **Using Docker is recommended, as it guarantees the application is run using compatible versions of Python and Node**.

There are three main services:

To run the development version of the app

```bash
docker-compose up flask-dev
```

To run the production version of the app

```bash
docker-compose up flask-prod
```

The list of `environment:` variables in the `docker-compose.yml` file takes precedence over any variables specified in `.env`.

To run any commands using the `Flask CLI`

```bash
docker-compose run --rm manage <<COMMAND>>
```

Therefore, to initialize a database you would run

```bash
docker-compose run --rm manage db init
docker-compose run --rm manage db migrate
docker-compose run --rm manage db upgrade
```

A docker volume `node-modules` is created to store NPM packages and is reused across the dev and prod versions of the application. For the purposes of DB testing with `sqlite`, the file `dev.db` is mounted to all containers. This volume mount should be removed from `docker-compose.yml` if a production DB server is used.

### Running locally

Run the following commands to bootstrap your environment if you are unable to run the application using Docker

```bash
cd cataloger
pip install -r requirements/dev.txt
npm install
npm start  # run the webpack dev server and flask server using concurrently
```

You will see a pretty welcome screen.

#### Database Initialization (locally)

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration

```bash
flask db init
flask db migrate
flask db upgrade
```

## Deployment

When using Docker, reasonable production defaults are set in `docker-compose.yml`

```text
FLASK_ENV=production
FLASK_DEBUG=0
```

Therefore, starting the app in "production" mode is as simple as

```bash
docker-compose up flask-prod
```

If running without Docker

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_URL="<YOUR DATABASE URL>"
npm run build   # build assets with webpack
flask run       # start the flask server
```

## Shell

To open the interactive shell, run

```bash
docker-compose run --rm manage db shell
flask shell # If running locally without Docker
```

By default, you will have access to the flask `app`.

## Running Tests/Linter

To run all tests, run

```bash
docker-compose run --rm manage test
flask test # If running locally without Docker
```

To run the linter, run

```bash
docker-compose run --rm manage lint
flask lint # If running locally without Docker
```

The `lint` command will attempt to fix any linting/style errors in the code. If you only want to know if the code will pass CI and do not wish for the linter to make changes, add the `--check` argument.

## Migrations

Whenever a database migration needs to be made. Run the following commands

```bash
docker-compose run --rm manage db migrate
flask db migrate # If running locally without Docker
```

This will generate a new migration script. Then run

```bash
docker-compose run --rm manage db upgrade
flask db upgrade # If running locally without Docker
```

To apply the migration.

For a full migration command reference, run `docker-compose run --rm manage db --help`.

If you will deploy your application remotely (e.g on Heroku) you should add the `migrations` folder to version control.
You can do this after `flask db migrate` by running the following commands

```bash
git add migrations/*
git commit -m "Add migrations"
```

Make sure folder `migrations/versions` is not empty.

## Asset Management

Files placed inside the `assets` directory and its subdirectories
(excluding `js` and `css`) will be copied by webpack's
`file-loader` into the `static/build` directory. In production, the plugin
`Flask-Static-Digest` zips the webpack content and tags them with a MD5 hash.
As a result, you must use the `static_url_for` function when including static content,
as it resolves the correct file name, including the MD5 hash.
For example

```html
<link rel="shortcut icon" href="{{static_url_for('static', filename='build/img/favicon.ico') }}">
```

If all of your static files are managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in ``.env``:

```text
SEND_FILE_MAX_AGE_DEFAULT=31556926  # one year
```
