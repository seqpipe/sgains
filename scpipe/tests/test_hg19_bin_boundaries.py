'''
Created on Jun 23, 2017

@author: lubo
'''
import pandas as pd
import os
from hg19 import HumanGenome19
import pytest


@pytest.mark.parametrize("chromozome", HumanGenome19.CHROMS)
def test_calc_bin_boundaries(hg, chromozome):
    bins_boundaries_fixture = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "data/bin.boundaries.bowtie.txt"
    )

    df = pd.read_csv(bins_boundaries_fixture, sep='\t')
    assert df is not None

    mappable_regions_df = hg.load_mappable_regions()

    for chrom in [chromozome]:
        chrom_df = df[df.chrom == chrom]
        for index, mappable_bin in enumerate(hg.calc_bin_boundaries(
                [chrom], mappable_regions_df)):
            fixture_bin = chrom_df.iloc[index, :]

            assert mappable_bin.chrom == fixture_bin['chrom']
            assert mappable_bin.chrom == fixture_bin['chrom']
            assert mappable_bin.current_size == \
                fixture_bin['mappable.positions'], \
                (index, mappable_bin, fixture_bin)
            assert mappable_bin.start_pos == fixture_bin['bin.start.chrompos']
            assert mappable_bin.end_pos == \
                fixture_bin['bin.end.chrompos'], \
                (index, mappable_bin, fixture_bin)


# def test_calc_bin_boundaries_chr(hg):
#     bins_boundaries_fixture = os.path.join(
#         os.path.abspath(os.path.dirname(__file__)),
#         "data/bin.boundaries.bowtie.txt"
#     )
#     df = pd.read_csv(bins_boundaries_fixture, sep='\t')
#     assert df is not None
#
#     mappable_regions_df = hg.load_mappable_regions()
#
#     chrom = 'chr1'
#     chrom_df = df[df.chrom == chrom]
#     for index, mappable_bin in enumerate(hg.calc_bin_boundaries(
#             [chrom], mappable_regions_df)):
#         fixture_bin = chrom_df.iloc[index, :]
#
#         assert mappable_bin.chrom == fixture_bin['chrom']
#         assert mappable_bin.current_size == \
#             fixture_bin['mappable.positions'], \
#             (index, mappable_bin, fixture_bin)
#         assert mappable_bin.start_pos == fixture_bin['bin.start.chrompos']
#         assert mappable_bin.end_pos == \
#             fixture_bin['bin.end.chrompos'], \
#             (index, mappable_bin, fixture_bin)
#
#         # assert mappable_bin.end_pos == fixture_bin['bin.end.chrompos']
