#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Maxime JACQUET <m.jacquet@outlook.fr>'
__version__ = 0.1

import argparse
import xmlrpclib
import psycopg2
import traceback


class OdooPsqlConn(object):
    
    def __init__(self, dbname, host, port, user, password):
        self.conn = psycopg2.connect(database=dbname,
                                user=user,
                                password=password,
                                host=host,
                                port=port)
        self.cursor = self.conn.cursor()
    
    def _doQuery(self, query):
        self.cursor.execute(query)
        self.conn.commit() 
    
    def vacuum(self):
        old_isolation_level = self.conn.isolation_level
        self.conn.set_isolation_level(0)
        query = "VACUUM (FULL, ANALYZE) ir_attachment"
        print '...%s' % query
        self._doQuery(query)
        self.conn.set_isolation_level(old_isolation_level)
    
    def update_attachments(self):
        query = "UPDATE ir_attachment SET db_datas = null WHERE store_fname IS NOT null"
        print '...%s' % query
        self._doQuery(query)


def add_options(parser):
    parser.add_argument('-dbname', required=True, type=str, help='The database name')
    parser.add_argument('-dbuser', required=True, type=str, help='The database user')
    parser.add_argument('-dbpass', required=True, type=str, help='The database pass')
    
    parser.add_argument('-dbhost', type=str, help='The database host', default='localhost')
    parser.add_argument('-dbport', type=int, help='The database port (default: 5432)', default=5432)
    parser.add_argument('-user', type=str, help='Odoo user (default: admin)', default='admin')
    parser.add_argument('-pwd', type=str, help='Odoo user pass (default: admin)', default='admin')
    parser.add_argument('-xport', type=str, help='Xmlrpc port (default: 8069)', default=8069)


def migrate_attachment(sock, args, uid, att_id):
    att = sock.execute(args.dbname, uid, args.pwd, 'ir.attachment', 'read', [att_id], ['datas'])
    datas = att and att[0] and att[0]['datas'] or False
    datas and sock.execute(args.dbname, uid, args.pwd, 'ir.attachment', 'write', [att_id], {'datas': datas})


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Migrates Odoo attachments from dbstorage to filestorage')
        add_options(parser)
        args = parser.parse_args()
        odoo_psql = OdooPsqlConn(args.dbname,
                                 args.dbhost,
                                 args.dbport,
                                 args.dbuser,
                                 args.dbpass)

        sock_common = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (args.dbhost.replace('http://', ''),
                                                                            args.xport))
        uid = sock_common.login(args.dbname, args.user, args.pwd)
        sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (args.dbhost.replace('http://', ''),
                                                                     args.xport))
        print ''
        print '#######################################################'
        print '#    Database connection : ', odoo_psql.conn
        print '#    Xmlrpc '
        print '#        - sock_common ', sock_common
        print '#        - uid ', uid
        print '#        - sock ', sock
        print '#######################################################'
        print 
        print
        att_ids = sock.execute(args.dbname,
                               uid,
                               args.pwd,
                               'ir.attachment',
                               'search',
                               [('store_fname','=',False)])
        len_att_ids = len(att_ids)
        print 'Found attachments : ', len_att_ids
        print
        i = 1
        migrated = []
        failed = []
        for id in att_ids:
            try:
                migrate_attachment(sock, args, uid, id)
                print 'Migrated ID %d (attachment %d of %d)' % (id, i, len_att_ids)
                migrated.append(id)
            except Exception, e:
                print '/!\ An error has occured during migration. ID %d (attachment %d of %d)' % (id, i, len_att_ids)
                print traceback.print_exc()
                failed.append(id)
            i += 1
        print '#######################################################'
        print
        print
        print 'Summary :'
        print len(migrated), 'migrated attachments'
        print 
        print len(failed), 'failed attachments'
        print 'failed ids : ', failed
        print 
        if migrated:
            print 'Vaccum table...'
            odoo_psql.vacuum()
            print 'Update attachments table...'
            odoo_psql.update_attachments()
    except Exception, e:
        print 'An error has occured : %s' % e
        print traceback.print_exc()
