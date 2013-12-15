from ..utils.python import util as _utils
import sqlite3
import pandas.io.sql as psql


def test_vogelstein_oncogenes():
    """Tests how many oncogenes in vogelstein's science paper is
    found in the COSMIC_nuc database"""
    onco_list = _utils.oncogene_list  # oncogenes according to paper
    num_oncogenes = len(onco_list)  # correspondig number of oncogenes

    # query COSMIC_nuc
    genes_db_path = _utils.get_db_config('genes')['db']
    conn = sqlite3.connect(genes_db_path)
    sql = ("SELECT Count(DISTINCT(Gene)) as NumOncoFound FROM nucleotide "
           "WHERE Gene in " + str(tuple(onco_list)))
    df = psql.frame_query(sql, con=conn)
    num_found_oncogenes = df['NumOncoFound'][0]
    conn.close()

    assert_str = 'ONCOGENES: Number found (%d) is less than total (%s)' % (num_found_oncogenes,
                                                                           num_oncogenes)
    assert num_oncogenes == num_found_oncogenes, assert_str


def test_vogelstein_tsg():
    """Tests how many tsg in vogelstein's science paper are
    found in the COSMIC_nuc database"""
    tsg_list = _utils.tsg_list  # oncogenes according to paper
    num_tsg = len(tsg_list)  # correspondig number of oncogenes

    # query COSMIC_nuc
    genes_db_path = _utils.get_db_config('genes')['db']
    conn = sqlite3.connect(genes_db_path)
    sql = ("SELECT Count(DISTINCT(Gene)) as NumTsgFound FROM nucleotide "
           "WHERE Gene in " + str(tuple(tsg_list)))
    df = psql.frame_query(sql, con=conn)
    num_found_tsg = df['NumTsgFound'][0]
    conn.close()

    assert_str =  'TSG: Number found (%d) is less than total (%s)' % (num_found_tsg,
                                                                      num_tsg)
    assert num_tsg == num_found_tsg, assert_str


def test_kandoth_smg():
    """Tests how many smg in kandoth et al's nature paper are
    found in the COSMIC_nuc database"""
    smg_list = _utils.smg_list  # oncogenes according to paper
    num_smg = len(smg_list)  # correspondig number of oncogenes

    # query COSMIC_nuc
    genes_db_path = _utils.get_db_config('genes')['db']
    conn = sqlite3.connect(genes_db_path)
    sql = ("SELECT Count(DISTINCT(Gene)) as NumSmgFound FROM nucleotide "
           "WHERE Gene in " + str(tuple(smg_list)))
    df = psql.frame_query(sql, con=conn)
    num_found_smg = df['NumSmgFound'][0]
    conn.close()

    assert_str =  'SMG: Number found (%d) is less than total (%s)' % (num_found_smg,
                                                                      num_smg)
    assert num_smg == num_found_smg, assert_str