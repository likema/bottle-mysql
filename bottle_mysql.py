'''
Bottle-MySQL is a plugin that integrates MySQL with your Bottle
application. It automatically connects to a database at the beginning of a
request, passes the database handle to the route callback and closes the
connection afterwards.

To automatically detect routes that need a database connection, the plugin
searches for route callbacks that require a `db` keyword argument
(configurable) and skips routes that do not. This removes any overhead for
routes that don't need a database connection.

Results are returned as dictionaries.

Usage Example::

    import bottle
    import bottle_mysql

    app = bottle.Bottle()
    # dbhost is optional, default is localhost
    plugin = bottle_mysql.Plugin(user='user', passwd='pass', db='db')
    app.install(plugin)

    @app.route('/show/:<tem>')
    def show(item, db):
        db.execute('SELECT * from items where name="%s"', (item,))
        row = db.fetchone()
        if row:
            return template('showitem', page=row)
        return HTTPError(404, "Page not found")
'''

__author__ = "Michael Lustfield"
__version__ = '0.1.5'
__license__ = 'MIT'

### CUT HERE (see setup.py)

import inspect
import MySQLdb
import MySQLdb.cursors as cursors
from bottle import HTTPResponse, HTTPError, PluginError


class MySQLPlugin(object):
    '''
    This plugin passes a mysql database handle to route callbacks
    that accept a `db` keyword argument. If a callback does not expect
    such a parameter, no connection is made. You can override the database
    settings on a per-route basis.
    '''

    name = 'mysql'

    def __init__(self, autocommit=True, dictrows=True, keyword='db',
                 timezone=None, **kwargs):
        self.autocommit = autocommit
        self.dictrows = dictrows
        self.keyword = keyword
        self.timezone = timezone
        self._kwargs = kwargs

    def setup(self, app):
        '''
        Make sure that other installed plugins don't affect the same keyword
        argument.
        '''
        for other in app.plugins:
            if not isinstance(other, MySQLPlugin):
                continue
            if other.keyword == self.keyword:
                raise PluginError("Found another mysql plugin with "
                                  "conflicting settings (non-unique keyword).")

    def _pop(self, conf, name):
        if name in conf:
            val = conf[name]
            del conf[name]
        else:
            val = getattr(self, name)

        return val

    def _assign(self, conf):
        '''
        Override global configuration with route-specific values.
        '''
        kwargs = dict(self._kwargs)

        if conf:
            conf = dict(conf)
            autocommit = self._pop(conf, 'autocommit')
            dictrows = self._pop(conf, 'dictrows')
            keyword = self._pop(conf, 'keyword')
            timezone = self._pop(conf, 'timezone')
            kwargs.update(conf)
        else:
            autocommit = self.autocommit
            dictrows = self.dictrows
            keyword = self.keyword
            timezone = self.timezone

        # Using DictCursor lets us return result as a dictionary
        # instead of the default list
        if dictrows:
            kwargs["cursorclass"] = cursors.DictCursor

        if timezone and "init_command" not in kwargs:
            kwargs["init_command"] = "set time_zone='%s'" % timezone
            timezone = None

        return autocommit, dictrows, keyword, timezone, kwargs

    def apply(self, callback, context):
        autocommit, dictrows, keyword, timezone, kws = self._assign(
            context['config'].get('mysql'))

        # Test if the original callback accepts a 'db' keyword.
        # Ignore it if it does not need a database handle.
        args = inspect.getargspec(context['callback'])[0]
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            # Add the connection handle as a keyword argument.
            con, kwargs[keyword] = self._connect(timezone, **kws)

            try:
                rv = callback(*args, **kwargs)
                if autocommit:
                    con.commit()
            except MySQLdb.IntegrityError as e:
                con.rollback()
                raise HTTPError(500, "Database Error", e)
            except HTTPError as e:
                raise
            except HTTPResponse:
                if autocommit:
                    con.commit()
                raise
            finally:
                if con:
                    con.close()
            return rv

        # Replace the route callback with the wrapped one.
        return wrapper

    @staticmethod
    def _connect(timezone, **kwargs):
        try:
            con = MySQLdb.connect(**kwargs)
            cur = con.cursor()
            if timezone:
                cur.execute("set time_zone=%s", (timezone, ))
        except HTTPResponse as e:
            raise HTTPError(500, "Database Error", e)

        return con, cur


Plugin = MySQLPlugin

# vim: ts=4 sw=4 sts=4 et:
