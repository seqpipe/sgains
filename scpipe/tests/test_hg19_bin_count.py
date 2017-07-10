'''
Created on Jul 6, 2017

@author: lubo
'''
import numpy as np


def test_bin_counts_0918(hg, varbin0918):

    df = hg.bin_count("CJA0918.jude58.rmdup.bam")

    print(df.head())
    print(varbin0918.head())

    assert np.all(varbin0918.columns == df.columns)
    assert np.all(varbin0918.chrom == df.chrom)
    assert np.all(varbin0918.chrompos == df.chrompos)

    for index, row in varbin0918.iterrows():
        if row['bincount'] != df.iloc[index, 3]:
            print(index, row, df.iloc[index, ])

    assert np.all(
        np.abs(varbin0918.bincount - df.bincount) <= 1
    )
    assert np.all(
        np.abs(varbin0918.ratio - df.ratio) < 1E-2
    )

    assert np.all(varbin0918.bincount == df.bincount)
