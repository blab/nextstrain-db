import argparse
import subprocess
import os, sys
import re
import logging
from utils.colorLogging import ColorizingStreamHandler

parser = argparse.ArgumentParser()
parser.add_argument('-db', '--database', default='tdb', help="database to upload to")
parser.add_argument('--subtypes', nargs='+', type = str,  help ="flu subtypes to include, options are: h3n2, h1n1pdm, vic, yam")
parser.add_argument('--sources', nargs='+', type = str,  help ="data sources to include, options are: elife, nimr, cdc")
parser.add_argument('--nimr_path', default='data/nimr/', help="directory containing NIMR titers")
parser.add_argument('--cdc_path', default='data/cdc/', help="directory containing CDC titers")
parser.add_argument('--elife_path', default='data/elife/', help="directory containing eLife titers")
parser.add_argument("--debug", action="store_const", dest="loglevel", const=logging.DEBUG, help="Enable debugging logging")

def upload_nimr(database, nimr_path, subtype):
    '''
    Makes calls to tdb/upload.py for every file in an NIMR titer directory (default data/nimr/).
    All files in the directory should be tabular titer tables in CSV format for only one subtype
    of virus (H3N2, H1N1pdm, etc.).
    '''
    path = nimr_path + subtype + "/"
    print "Uploading NIMR data for subtype", subtype, "contained in directory", path + "."

    for fname in os.listdir(path):
        if fname[0] != '.':
            fpath = path + fname
            fstem = fname[:-4]
            print "Uploading " + fname
            command = "python tdb/nimr_upload.py -db " + database + " --subtype " + subtype + " --ftype tables --path " + path + " --fstem " + fstem
            print "Running with: " + command
            subprocess.call(command, shell=True)
            print "Done with", fname + "."

    print "Done uploading NIMR documents."

def upload_cdc(database, cdc_path):
    '''
    Makes calls to tdb/upload.py for every flat file in an CDC titer directory (default data/cdc/).
    All files in the directory should be flat titer files in TSV format.
    There are multiple subtypes within a file.
    '''
    path = cdc_path
    print "Uploading CDC data contained in directory", path + "."

    for fname in os.listdir(path):
        if fname[0] != '.':
            fpath = path + fname
            fstem = fname[:-4]
            print "Uploading " + fname
            command = "python tdb/cdc_upload.py -db cdc_tdb --path " + path + " --fstem " + fstem
            print "Running with: " + command
            subprocess.call(command, shell=True)
            print "Done with", fname + "."

    print "Done uploading CDC documents."

def upload_elife(database, elife_path, subtype):
    '''
    Makes calls to tdb/upload.py for every flat file in an eLife titer directory (default data/elife/).
    All files in the directory should be flat titer files in TSV format for only one subtype
    of virus (H3N2, H1N1pdm, etc.).
    '''
    path = elife_path + subtype + "/"
    print "Uploading eLife data for subtype", subtype, "contained in directory", path + "."

    for fname in os.listdir(path):
        if fname[0] != '.':
            fpath = path + fname
            fstem = fname[:-4]
            print "Uploading " + fname
            command = "python tdb/elife_upload.py -db " + database + " --subtype " + subtype + " --path " + path + " --fstem " + fstem
            print "Running with: " + command
            subprocess.call(command, shell=True)
            print "Done with", fname + "."

    print "Done uploading stored eLife documents."

def upload_vidrl(upload_subtypes):
    with open('data/vidrl_fail_log.txt', 'w') as o:
        path = '../../fludata/VIDRL-Melbourne-WHO-CC/raw-data/'
        for ab in os.listdir(path):
            ab_path = '{}{}/'.format(path, ab)
            for subtype in os.listdir(ab_path):
                subtype_path = '{}{}/'.format(ab_path, subtype)
                if subtype.lower() == "victoria":
                    subtype = "vic"
                if subtype.lower() == "yamagata":
                    subtype = "yam"
                if subtype.lower() in upload_subtypes:
                    for assay in os.listdir(subtype_path):
                        complete_path = '{}{}/'.format(subtype_path, assay)
                        for fname in os.listdir(complete_path):
                            fpath = complete_path + fname
                            fstem = fname.split('.')[0]
                            if ' ' in fstem:
                                fstem = re.escape(fstem)
                            print "Uploading " + fname
                            command = "python tdb/upload_vidrl.py -db vidrl_tdb -v flu --path {} --fstem {} --ftype vidrl".format(complete_path, fstem)
                            print "Running with: " + command
                            try:
                                subprocess.call(command, shell=True)
                            except:
                                logger.critical("Couldn't upload {}, please try again.".format(fname))
                            print "Done with", fname + "."
                            # sys.exit()

if __name__=="__main__":



    params = parser.parse_args()

    ## L O G G I N G
    # https://docs.python.org/2/howto/logging-cookbook.html#multiple-handlers-and-formatters
    root_logger = logging.getLogger('')
    root_logger.setLevel(args.loglevel if params.loglevel else logging.INFO)
    root_logger.addHandler(ColorizingStreamHandler())
    logger = logging.getLogger(__name__)

    print "Beginning construction of", params.database + "."

    if params.subtypes is None:
        params.subtypes = ['h3n2', 'h1n1pdm', 'vic', 'yam']

    if params.sources is None:
        params.sources = ['elife', 'nimr', 'cdc']

    for source in params.sources:
        if source == "cdc":
            upload_cdc(params.database, params.cdc_path)
        if source == "elife":
            for subtype in params.subtypes:
                if subtype != 'h1n1pdm':
                    upload_elife(params.database, params.elife_path, subtype)
        if source == "nimr":
            for subtype in params.subtypes:
                upload_nimr(params.database, params.nimr_path, subtype)
        if source == "vidrl":
            upload_vidrl(params.subtypes)

    print "Done with all uploads."
