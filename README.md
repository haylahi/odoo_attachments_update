odoo_attachments_update
=======================

A small script to re-write attachments on a Odoo (v8) migrated database

/!\ This is not a full ir.attachments migration (vX to v8) /!\

With Odoo (v8) the default system for attachments storage is a filestorage.
By re-writting attachments from the migrated database that'll force switch dbstorage to filestorage.


Todo :
 - use getpass for a pwd prompt instead of using argparse opt
 - create files with migrated and failed attachement ids
 - send theses files by email
 - maybe a better and fully migration of the attachments for older Odoo version to Odoo 8
