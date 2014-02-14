import utils.python.util as _utils
import recurrent_mutation
import utils.python.math as mymath
from utils.python.amino_acid import AminoAcid
import plot_data
import pandas as pd
import numpy as np
import pandas.io.sql as psql
import logging

logger = logging.getLogger(name=__file__)

def _count_mutation_position(hgvs_iterable):
    """Counts the total mutations and stratifies mutation
    counts according to position.

    **Parameters**

    hgvs_iterable : iterable
        container object with HGVS protein strings

    **Returns**

    gene_pos_ctr : dict
        maps positions to mutation counts
    total_mutation_ctr : int
        total number of mutations

    NOTE: This function requires the input HGVS container to contain
    mutations only for a single gene.
    """
    gene_pos_ctr = {}
    total_mutation_ctr = 0
    for hgvs in hgvs_iterable:
        aa = AminoAcid(hgvs)
        if aa.is_valid and aa.pos:
            gene_pos_ctr.setdefault(aa.pos, 0)
            gene_pos_ctr[aa.pos] += 1  # add 1 to dict of pos
            total_mutation_ctr += 1  # add 1 to total missense
    return gene_pos_ctr, total_mutation_ctr


def mutation_position_entropy(conn):
    logger.info('Calculating mutation position entropy . . .')

    # query database
    sql = "SELECT Gene, AminoAcid FROM nucleotide"  # get everything from table
    df = psql.frame_query(sql, con=conn)
    gene_to_indexes = df.groupby('Gene').groups

    # calculate missense position entropy by gene
    gene_items = gene_to_indexes.items()
    gene_list, _ = zip(*gene_items)
    result_df = pd.DataFrame(np.zeros(len(gene_list)), columns=['missense position entropy'], index=gene_list)
    for gene, indexes in gene_items:
        tmp_df = df.ix[indexes]
        # myct = recurrent_mutation.count_recurrent_by_number(tmp_df['AminoAcid'])
        myct, total_ct = _count_mutation_position(tmp_df['AminoAcid'])
        pos_ct = np.array(myct.values())  # convert to numpy array
        total_mutation = np.sum(pos_ct)  # total number of missense
        p = pos_ct / float(total_mutation)  # normalize to a probability
        mutation_entropy = mymath.shannon_entropy(p)  # calc shannon entropy
        result_df.ix[gene, 'mutation position entropy'] = mutation_entropy  # store result

    logger.info('Finsihed calculating mutation position entropy.')
    return result_df


def missense_position_entropy(conn):
    logger.info('Calculating missense position entropy . . .')

    # query database
    sql = "SELECT Gene, AminoAcid FROM nucleotide"  # get everything from table
    df = psql.frame_query(sql, con=conn)
    gene_to_indexes = df.groupby('Gene').groups

    # calculate missense position entropy by gene
    gene_items = gene_to_indexes.items()
    gene_list, _ = zip(*gene_items)
    result_df = pd.DataFrame(np.zeros(len(gene_list)), columns=['missense position entropy'], index=gene_list)
    for gene, indexes in gene_items:
        tmp_df = df.ix[indexes]
        # myct = recurrent_mutation.count_recurrent_by_number(tmp_df['AminoAcid'])
        myct, total_missense = recurrent_mutation._count_recurrent_missense(tmp_df['AminoAcid'])
        pos_ct = np.array(myct.values())  # convert to numpy array
        total_missense = np.sum(pos_ct)  # total number of missense
        p = pos_ct / float(total_missense)  # normalize to a probability
        missense_entropy = mymath.shannon_entropy(p)  # calc shannon entropy
        result_df.ix[gene, 'missense position entropy'] = missense_entropy  # store result

    logger.info('Finsihed calculating missense position entropy.')
    return result_df


def main(conn):
    cfg_opts = _utils.get_output_config('position_entropy')

    # get information about missense position entropy
    entropy_df = missense_position_entropy(conn)
    entropy_df['true class'] = 0
    onco_mask = [True if gene in _utils.oncogene_set else False for gene in entropy_df.index]
    tsg_mask = [True if gene in _utils.tsg_set else False for gene in entropy_df.index]
    entropy_df.ix[onco_mask, 'true class'] = 1
    entropy_df.ix[tsg_mask, 'true class'] = 2
    entropy_df.to_csv(_utils.result_dir + cfg_opts['missense_pos_entropy'], sep='\t')

    # plot distribution of missense position entropy
    plot_data.missense_entropy_kde(entropy_df,
                                   _utils.plot_dir + cfg_opts['missense_pos_entropy_dist'],
                                   title='Distribution of Missense Position Entropy',
                                   xlabel='Missense Position Entropy (bits)')

    # get information about mutation position entropy
    entropy_df = mutation_position_entropy(conn)
    entropy_df['true class'] = 0
    onco_mask = [True if gene in _utils.oncogene_set else False for gene in entropy_df.index]
    tsg_mask = [True if gene in _utils.tsg_set else False for gene in entropy_df.index]
    entropy_df.ix[onco_mask, 'true class'] = 1
    entropy_df.ix[tsg_mask, 'true class'] = 2
    entropy_df.to_csv(_utils.result_dir + cfg_opts['mutation_pos_entropy'], sep='\t')

    # plot distribution of mutation position entropy
    plot_data.missense_entropy_kde(entropy_df,
                                   _utils.plot_dir + cfg_opts['mutation_pos_entropy_dist'],
                                   title='Distribution of Mutation Position Entropy',
                                   xlabel='Mutation Position Entropy (bits)')
