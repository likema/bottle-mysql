=====================
Bottle-MySQL
=====================

MySQL is the world's most used relational database management system (RDBMS) that runs
as a server providing multi-user access to a number of databases.

This plugin simplifies the use of mysql databases in your Bottle applications.
Once installed, all you have to do is to add an ``db`` keyword argument
(configurable) to route callbacks that need a database connection.

Installation
===============

Install using pip:

    $ pip install bottle-mysql

or download the latest version from github:

    $ git clone git://github.com/MTecknology/bottle-mysql.git
    $ cd bottle-mysql
    $ python setup.py install

Usage
===============

Once installed to an application, the plugin passes an open
:class:`MySQLdb.connect().cursor()` instance to all routes that requires an ``db`` keyword
argument:

```python
import bottle
import bottle_mysql

app = bottle.Bottle()
# dbhost is optional, default is localhost
plugin = bottle_mysql.Plugin(user='user', passwd='pass', db='some_db')
app.install(plugin)

@app.route('/show/<item>')
def show(item, db):
    db.execute('SELECT * from items where name="%s"', (item,))
    row = db.fetchone()
    if row:
        return template('showitem', page=row)
    return HTTPError(404, "Page not found")
```

Routes that do not expect an ``db`` keyword argument are not affected.

The connection handle is configurable so that rows can be returned as either an
index (like tuples) or as dictionaries. At the end of the request cycle, outstanding
transactions are committed and the connection is closed automatically. If an error
occurs, any changes to the database since the last commit are rolled back to keep
the database in a consistent state.

Configuration
=============

The following configuration options exist for the plugin class:

        self._kwargs = kwargs
* **keyword**: The keyword argument name that triggers the plugin (default: 'db').
* **autocommit**: Whether or not to commit outstanding transactions at the end of the request cycle (default: True).
* **dictrows**: Whether or not to support dict-like access to row objects (default: True).
* **timezone**: Database connection time zone (default: None).
* kwargs: Database connection parameters.
    * **host**: name of host to connect to. Default: use the local host via a UNIX socket (where applicable)
    * **port**: TCP port of MySQL server. Default: standard port (3306).
    * **user**: user to authenticate as. Default: current effective user.
    * **passwd**: password to authenticate with. Default: no password.
    * **db**: database to use. Default: no default database.
    * **unix_socket**: location of UNIX socket. Default: use default location or TCP for remote hosts.
    * **conv**: type conversion dictionary. Default: a copy of MySQLdb.converters.conversions
    * **compress**: Enable protocol compression. Default: no compression.
    * **connect_timeout**: Abort if connect is not completed within given number of seconds. Default: no timeout (?)
    * **named_pipe**: Use a named pipe (Windows). Default: don't.
    * **init_command**: Initial command to issue to server upon connection. Default: Nothing.
    * **read_default_file**: MySQL configuration file to read; see the MySQL documentation for mysql_options().
    * **read_default_group**: Default group to read; see the MySQL documentation for mysql_options().
    * **cursorclass**: cursor class that cursor() uses, unless overridden. Default: MySQLdb.cursors.Cursor. This must be a keyword parameter.
    * **use_unicode**:
        * True: CHAR, VARCHAR and TEXT columns are returned as Unicode strings in the configured character set. It is best to set the default encoding in the server configuration, or client configuration (read with read_default_file). If you change the character set after connecting (MySQL-4.1 and later), you'll need to put the correct character set name in connection.charset.
        * False: text-like columns are returned as normal strings, but you can always write Unicode strings.
    * **charset**:
        * If present, the connection character set will be changed to this character set, if they are not equal. Support for changing the character set requires MySQL-4.1 and later server; if the server is too old, UnsupportedError will be raised. This option implies use_unicode=True, but you can override this with use_unicode=False, though you probably shouldn't.
        * Otherwise the default character set is used.
    * **sql_mode**:
        * If present, the session SQL mode will be set to the given string. For more information on sql_mode, see the MySQL documentation. Only available for 4.1 and newer servers.
        * Otherwise the session SQL mode will be unchanged.
    * **ssl**: It takes a dictionary or mapping, where the keys are parameter names used by the mysql_ssl_set MySQL C API call.  If it is set, it initiates an SSL connection to the server; if there is no SSL support in the client, an exception is raised.

You can override each of these values on a per-route basis:

```python
@app.route('/cache/<item>', mysql={'db': 'xyz_db'})
def cache(item, db):
    ...
```

or install two plugins with different ``keyword`` settings to the same application:

```python
@app.route('/cache/<item>', mysql={'dbname': 'xyz_db'})
app = bottle.Bottle()
local_db = bottle_mysql.Plugin(user='user', passwd='pass', db='local_db')
prod_db = bottle_mysql.Plugin(user='user', passwd='pass', db='some_db', host='sql.domain.tld', keyword='remote_db')
app.install(local_db)
app.install(prod_db)

@app.route('/show/<item>')
def show(item, db):
    ...

@app.route('/cache/<item>')
def cache(item, remote_db):
    ...
```
