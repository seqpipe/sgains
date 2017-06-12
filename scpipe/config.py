'''
Created on Jun 10, 2017

@author: lubo
'''
from box import Box
import os


def load_config(filename):
    assert os.path.exists(filename)

    with open(filename, 'r') as infile:
        config = Box.from_yaml(infile)
        config.filename = os.path.abspath(filename)
        dirname = os.path.dirname(config.filename)
        config.genome.src = os.path.join(
            dirname,
            config.genome.src)
        config.genome.dst = os.path.join(
            dirname,
            config.genome.dst)
        print(config)

        return config