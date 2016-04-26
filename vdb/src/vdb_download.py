import os, json, datetime
import rethinkdb as r
from Bio import SeqIO

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-db', '--database', default='vdb', help="database to download from")
parser.add_argument('-v', '--virus', default='Zika', help="virus table to interact with")
parser.add_argument('--path', default='vdb/data/', help="path to dump output files to")
parser.add_argument('--ftype', default='fasta', help="output file format, default \"fasta\", other is \"json\"")
parser.add_argument('--fstem', default=None, help="default output file name is \"VirusName_Year_Month_Date\"")
parser.add_argument('--host', default=None, help="rethink host url")
parser.add_argument('--auth_key', default=None, help="auth_key for rethink database")
parser.add_argument('--public_only', default=False, action="store_true", help="include to subset public sequences")
parser.add_argument('--countries', nargs = '+', type = str, default = None, help="Countries(in CamelCase Format) to be include in download")

class vdb_download(object):

    def __init__(self, **kwargs):
        '''
        parser for virus, fasta fields, output file names, output file format path, interval
        '''
        self.kwargs = kwargs
        if 'host' in self.kwargs:
            self.host = self.kwargs['host']
        if 'RETHINK_HOST' in os.environ and self.host is None:
            self.host = os.environ['RETHINK_HOST']
        if self.host is None:
            raise Exception("Missing rethink host")
        if 'auth_key' in self.kwargs:
            self.auth_key = self.kwargs['auth_key']
        if 'RETHINK_AUTH_KEY' in os.environ and self.auth_key is None:
            self.auth_key = os.environ['RETHINK_AUTH_KEY']
        if self.auth_key is None:
            raise Exception("Missing rethink auth_key")
        if 'path' in self.kwargs:
            self.path = self.kwargs['path']
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

        if 'database' in self.kwargs:
            self.database = self.kwargs['database']
        if 'virus' in self.kwargs:
            self.virus = self.kwargs['virus'].title()
        if 'ftype' in self.kwargs:
            self.ftype = self.kwargs['ftype']
        if 'public_only' in self.kwargs:
            self.public_only = self.kwargs['public_only']
        if 'countries' in kwargs:
            self.countries = kwargs['countries']
        self.viruses = []

        self.current_date = str(datetime.datetime.strftime(datetime.datetime.now(),'%Y_%m_%d'))
        if 'fstem' in self.kwargs:
            self.fstem = self.kwargs['fstem']
        if self.fstem is None:
            self.fstem = self.virus + '_' + self.current_date
        self.fname = self.fstem + '.' + self.ftype

        self.connect_rethink()

    def connect_rethink(self):
        '''
        Connect to rethink database,
        Check for existing table, otherwise create it
        '''
        try:
            r.connect(host=self.host, port=28015, db=self.database, auth_key=self.auth_key).repl()
            print("Connected to the \"" + self.database + "\" database")
        except:
            print("Failed to connect to the database, " + self.database)
            raise Exception

        existing_tables = r.db(self.database).table_list().run()
        if self.virus not in existing_tables:
            raise Exception("No table exists yet for " + self.virus)

    def count_documents(self):
        '''
        return integer count of number of documents in table
        '''
        return r.db(self.database).table(self.virus).count().run()

    def download(self):
        '''
        download documents from table
        '''
        print("Downloading all viruses from the table: " + self.virus)
        cursor = list(r.db(self.database).table(self.virus).run())
        cursor = self.subsetting(cursor)
        self.viruses = cursor
        self.output()

    def subsetting(self, cursor):
        '''
        filter through documents in vdb to return subsets of sequence
        '''
        result = cursor
        print("Documents in table before subsetting: " + str(len(result)))
        if self.public_only:
            result = filter(lambda doc: doc['public'], result)
            print('Removed documents that were not public, remaining documents: ' + str(len(result)))
        if self.countries is not None:
            result = filter(lambda doc: any(doc['country'] == cn for cn in self.countries), result)
            print('Removed documents that were not in countries specified (' + ','.join(self.countries) + '), remaining documents: ' + str(len(result)))
        print("Documents in table after subsetting: " + str(len(result)))
        return result

    def write_json(self, data, fname, indent=1):
        '''
        writes as list of viruses (dictionaries)
        '''
        try:
            handle = open(fname, 'w')
        except:
            print("Couldn't open output file")
            print(fname)
            raise FileNotFoundError
        else:
            json.dump(data, handle, indent=indent)
            handle.close()
            print("Wrote to " + fname)

    def write_fasta(self, viruses, fname):
        fasta_fields = ['strain', 'virus', 'accession', 'date', 'region', 'country', 'division', 'location', 'source', 'locus', 'authors', 'subtype']
        try:
            handle = open(fname, 'w')
        except IOError:
            pass
        else:
            for v in viruses:
                handle.write(">")
                for field in fasta_fields:
                    if field in v and v[field] is not None:
                        handle.write(str(v[field]) + '|')
                    else:
                        handle.write('?|')

                handle.write("\n")
                handle.write(v['sequence'] + "\n")
            handle.close()
            print("Wrote to " + fname)

    def output(self):
        if self.ftype == 'json':
            self.write_json(self.viruses, self.path+self.fname)
        else:
            self.write_fasta(self.viruses, self.path+self.fname)

if __name__=="__main__":

    args = parser.parse_args()
    connVDB = vdb_download(**args.__dict__)
    connVDB.download()