from pathlib import Path
import subprocess as sp
import pandas as pd
from ete3 import NCBITaxa

import argparse

SRC_DIR = Path(__file__).parent
RUST_APP = '{}/genome_annotation/target/release/genome_annotation'.format(SRC_DIR)

RANKS = ["superkingdom", "phylum", "class", "order", "family", "genus", "species"]

def parse_args():
    '''
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('--taxids', type=str, default="taxids.csv")
    parser.add_argument('--accessions', type=str, default=None)
    parser.add_argument('--ranks', type=str, nargs='*', default=RANKS)
    args = parser.parse_args()

    if args.accessions is not None:
        args.accessions = Path(args.accessions).resolve()
    if args.taxids is not None:
        args.taxids = Path(args.taxids).resolve()

    return args

def get_taxids(accessions_file, output):
    cmd = [RUST_APP,
           '--query', str(accessions_file),
           '--db', '{}/db/nucl_gb.accession2taxid'.format(SRC_DIR),
           '-o', str(output)]
    sp.run(cmd, check=True)

def taxid2lineage(db, acc, taxid, ranks=None):
    try:
        lineage = db.get_lineage(taxid)
    except ValueError:
        print('No match for {} ({})'.format(acc, taxid))
        return
    names = pd.Series(db.get_taxid_translator(lineage)).rename(acc)
    names.index = pd.Series(db.get_rank(names.index)).values
    names = names[~names.index.duplicated()].drop('no rank', errors='ignore')

    if ranks:
        names = names.reindex(ranks)

    return names

def process_all_taxids(query_file, ranks=None):
    data = pd.read_csv(query_file, dtype=str, header=guess_header(query_file, sep=',')).dropna()
    ncbi = NCBITaxa()

    lineages = []
    processed = {}

    for i, (acc, taxid, _) in enumerate(data.to_numpy()):
        print("{:.1%}".format(i/len(data)), end='\r')

        if taxid in processed:
            lineages.append(processed[taxid])
            continue
        
        names = taxid2lineage(ncbi, acc, taxid, ranks=ranks)
        if names is not None:
            lineages.append(names)

        processed[taxid] = names
        
    lineage_df = (pd.concat(lineages, axis=1).T
                  .dropna(how='all')
                  .drop_duplicates()
                  .rename(columns={'superkingdom': 'kingdom'}))
                  
    lineage_df.to_csv('lineages.csv')

def guess_header(filename, sep):
    first_line = next(open(filename)).split(',')

    if not any(x.replace('.', '').isdigit() for x in first_line):
        return 0
    
def main():
    '''
    '''

    args = parse_args()

    if args.accessions:
        get_taxids(args.accessions, output=args.taxids)

    process_all_taxids(args.taxids, ranks=args.ranks)
            

if __name__ == '__main__':
    main()
