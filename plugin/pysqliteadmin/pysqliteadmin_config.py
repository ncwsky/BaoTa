#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# editor: mufei(ypdh@qq.com tel:15712150708)
'''
牧飞 _ __ ___   ___   ___  / _| ___(_)
| '_ ` _ \ / _ \ / _ \| |_ / _ \ |
| | | | | | (_) | (_) |  _|  __/ |
|_| |_| |_|\___/ \___/|_|  \___|_|
'''
#+--------------------------------------------------------------------
#|   宝塔第三方应用开发 pysqliteadmin
#+--------------------------------------------------------------------

import os,datetime

try:
    import peewee
except:
    os.system('pip install peewee')
try:
    import pygments
except:
    os.system('pip install pygments')
from peewee import *
from peewee import IndexMetadata
from peewee import sqlite3
from playhouse.dataset import DataSet
from collections import namedtuple, OrderedDict

from BTPanel import session

DEBUG = False
MAX_RESULT_SIZE = 1000
ROWS_PER_PAGE = 50

__all__ = ['dataset', 'migrator','initialize_db','dataSetCache',
           'MAX_RESULT_SIZE', 'ROWS_PER_PAGE', 'DEBUG']

#
# Database helpers.
#

dataset = None
migrator = None

#
# Database metadata objects.
#

TriggerMetadata = namedtuple('TriggerMetadata', ('name', 'sql'))

ViewMetadata = namedtuple('ViewMetadata', ('name', 'sql'))


class cDataSetCache:
    _DataSets = {}

    def set(self, path, dataset):
        self._DataSets[path] = dataset

    @property
    def dataset(self):
        if 'pysqliteadmin-db-id' in session:
            path = session['pysqliteadmin-db-id']
            if path in self._DataSets:
                return self._DataSets[path]['dataset']
        return dataset
            
    @property
    def migrator(self):
        if 'pysqliteadmin-db-id' in session:
            path = session['pysqliteadmin-db-id']
            if path in self._DataSets:
                return self._DataSets[path]['migrator']
        return migrator

dataSetCache = cDataSetCache()


class SqliteDataSet(DataSet):
    @property
    def filename(self):
        db_file = self._database.database #dataset._database.database
        if db_file.startswith('file:'):
            db_file = db_file[5:]
        return os.path.realpath(db_file.rsplit('?', 1)[0])

    @property
    def is_readonly(self):
        db_file = self._database.database #dataset._database.database
        return db_file.endswith('?mode=ro')

    @property
    def base_name(self):
        return os.path.basename(self.filename)

    @property
    def created(self):
        stat = os.stat(self.filename)
        return datetime.datetime.fromtimestamp(stat.st_ctime)

    @property
    def modified(self):
        stat = os.stat(self.filename)
        return datetime.datetime.fromtimestamp(stat.st_mtime)

    @property
    def size_on_disk(self):
        stat = os.stat(self.filename)
        return stat.st_size

    def get_indexes(self, table):
        #return dataset._database.get_indexes(table)
        return self._database.get_indexes(table)

    def get_all_indexes(self):
        cursor = self.query(
            'SELECT name, sql FROM sqlite_master '
            'WHERE type = ? ORDER BY name',
            ('index',))
        return [IndexMetadata(row[0], row[1], None, None, None)
                for row in cursor.fetchall()]

    def get_columns(self, table):
        #return dataset._database.get_columns(table)
        return self._database.get_columns(table)

    def get_foreign_keys(self, table):
        #return dataset._database.get_foreign_keys(table)
        return self._database.get_foreign_keys(table)

    def get_triggers(self, table):
        cursor = self.query(
            'SELECT name, sql FROM sqlite_master '
            'WHERE type = ? AND tbl_name = ?',
            ('trigger', table))
        return [TriggerMetadata(*row) for row in cursor.fetchall()]

    def get_all_triggers(self):
        cursor = self.query(
            'SELECT name, sql FROM sqlite_master '
            'WHERE type = ? ORDER BY name',
            ('trigger',))
        return [TriggerMetadata(*row) for row in cursor.fetchall()]

    def get_all_views(self):
        cursor = self.query(
            'SELECT name, sql FROM sqlite_master '
            'WHERE type = ? ORDER BY name',
            ('view',))
        return [ViewMetadata(*row) for row in cursor.fetchall()]

    def get_virtual_tables(self):
        cursor = self.query(
            'SELECT name FROM sqlite_master '
            'WHERE type = ? AND sql LIKE ? '
            'ORDER BY name',
            ('table', 'CREATE VIRTUAL TABLE%'))
        return set([row[0] for row in cursor.fetchall()])

    def get_corollary_virtual_tables(self):
        virtual_tables = self.get_virtual_tables()
        suffixes = ['content', 'docsize', 'segdir', 'segments', 'stat']
        return set(
            '%s_%s' % (virtual_table, suffix) for suffix in suffixes
            for virtual_table in virtual_tables)



def initialize_db(filename, read_only=False):
    global dataset
    global migrator

    if read_only:
        if sys.version_info < (3, 4, 0):
            die('Python 3.4.0 or newer is required for read-only access.')
        if peewee_version < (3, 5, 1):
            die('Peewee 3.5.1 or newer is required for read-only access.')
        db = SqliteDatabase('file:%s?mode=ro' % filename, uri=True)
        try:
            db.connect()
        except OperationalError:
            die('Unable to open database file in read-only mode. Ensure that '
                'the database exists in order to use read-only mode.')
        db.close()
        dataset = SqliteDataSet(db, bare_fields=True)
    else:
        dataset = SqliteDataSet('sqlite:///%s' % filename, bare_fields=True)

    migrator = dataset._migrator
    dataset.close()
    rs = {'dataset':dataset, 'migrator':migrator}
    session['pysqliteadmin-db-id'] = filename
    dataSetCache.set(filename,rs)
     

#L = ['/www/server/data/default.db','/BtSoft/panel/data/default.db']
#initialize_db(L[[(os.path.isfile(e) and 1 or 0) for e in L].index(1)])
#initialize_db('/BtSoft/panel/data/default.db')
    
    




