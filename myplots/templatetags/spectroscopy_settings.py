import pysnid

def get_pysnid_results(inputfile):
    snidres = pysnid.snid.SNIDReader.from_filename(inputfile)
    return snidres
