# sakura
[![Build Status](https://travis-ci.org/leannmak/sakura.svg?branch=master)](https://travis-ci.org/leannmak/sakura)  

**sakura**, named from **sakura kinomoto**, is developed as a tool for configuration file management based on `Etcd`, `Confd` and `Ansible`.

## External Tool Required
```shell
1. Etcd (better use TLS)
2. Confd
3. MySQL (or other databases)
4. RabbitMQ
5. Minio
```

## Setup

```shell
$ git clone https://github.com/leannmak/sakura.git
$ git branch dev
$ cd sakura
$ pip install -r requirements.txt
$ vi config.py
$ python manage.py recreatedb
$ python runserver.py
$ export PYTHONOPTIMIZE=1
$ celery worker -B -A  sakura.celery --loglevel=debug --pidfile=.tmp/sakura-celery.pid -f .log/sakura-celery.log -c 2 -Q sakura
```

### Run Test

```shell
$ pip install tox
$ vi instance/test_config.py
$ tox
```

### Run Script

```shell
$ python manage.py --help
usage: manager script support for sakura

manager script support for sakura

positional arguments:
  {shell,db,recreatedb,initdb,runserver,dropdb}
    shell               Runs a Python shell inside Flask application context.
    db                  Perform database migrations
    recreatedb          Recreates database tables (same as issuing 'dropdb'
                        and 'initdb')
    initdb              Initialize database tables
    runserver           Runs the Flask development server i.e. app.run()
    dropdb              Drops database tables

optional arguments:
  -?, --help            show this help message and exit
```

### API Usage

See [realtime.md](document/realtime.md) and [history.md](document/history.md).
