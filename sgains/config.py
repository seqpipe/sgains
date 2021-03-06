'''
Created on Jun 10, 2017

@author: lubo
'''
from box import Box
import os
import glob
from termcolor import colored
import copy


class NonEmptyWorkDirectory(Exception):

    def __init__(self, dirname):
        super(NonEmptyWorkDirectory, self).__init__(dirname)


class Config(Box):
    DEFAULT_CONFIG = {
        "force": False,
        "dry_run": False,
        "parallel": 1,

        "genome": {
            "version": "hg19",
            "data_dir": "data/hg19_safe",
            "work_dir": "data/hg19",
            "index": "genomeindex",
        },
        "mappable_regions": {
            "length": 100,
            "work_dir": "data/R100",
            "mappable_regions": "hg19_R100_mappable_regions.txt",
            "chrom_sizes": "chrom_sizes.yml",
            "bowtie_opts": "",
        },
        "bins": {
            "bins_count": 10000,
            "bins_dir": "data/R100_B10k",
            "bins_boundaries": "bins_boundaries.tst",
        },
        "mapping": {
            "reads_dir": "",
            "reads_suffix": "",
            "mapping_dir": "",
            "mapping_suffix": ".rmdup.bam",
            "mapping_bowtie_opts": "",
        },
        "varbin": {
            "varbin_dir": "",
            "varbin_suffix": ".varbin.txt",
        },
        "scclust": {
            "scclust_dir": ".",
            "case_name": "test",
            "cytoband": "hg19/cytoBand.txt",
            "nsim": 150,
            "sharemin": 0.80,
            "fdrthres": -3,
            "nshare": 4,
            "climbtoshare": 4,
        }
    }

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(
            *args,
            **kwargs)

    @staticmethod
    def copy(config):
        new_box = Box(copy.deepcopy(config.to_dict()))
        return Config(new_box)

    @staticmethod
    def cellname(filename):
        return os.path.basename(filename).split(os.extsep, 1)[0]

    @staticmethod
    def default():
        data = copy.deepcopy(Config.DEFAULT_CONFIG)
        config = Box(data, default_box=True)
        config.filename = None
        config.dirname = os.getcwd()
        return Config(
            config.to_dict(),
            default_box=True,
        )

    @staticmethod
    def parse_args(argv):
        if '-c' in argv:
            index = argv.index('-c')
        elif '--config' in argv:
            index = argv.index('--config')
        else:
            try:
                config = Config.load('./sgains.yml')
                return config
            except AssertionError:
                config = Config.default()
                return config

        index += 1
        if index < 0 or index >= len(argv):
            raise ValueError('config filename not found')

        filename = argv[index]
        config = Config.load(filename)
        return config

    @staticmethod
    def load(filename, use_config_dir=False):
        default = Config.default()

        filename = os.path.abspath(filename)
        assert os.path.exists(filename), filename

        with open(filename, 'r') as infile:
            config = Box.from_yaml(infile)
            config.filename = os.path.abspath(filename)
            config.dirname = os.curdir
            if use_config_dir:
                config.dirname = os.path.dirname(config.filename)
            default.update(config.to_dict())

            return Config(
                default.to_dict(),
                default_box=True,
            )

    def abspath(self, filename):
        return os.path.abspath(
            os.path.join(
                self.dirname,
                filename))

    def genome_index_filename(self):
        filename = self.abspath(os.path.join(
            self.genome.work_dir,
            self.genome.index
        ))
        return self.abspath(filename)

    def genome_index_filename_exists(self):
        filename = os.path.join(
            self.genome.work_dir,
            "{}.1.ebwt".format(self.genome.index)
        )
        return os.path.exists(filename)

    def mappable_regions_filename(self, chrom=None):
        mname = self.mappable_regions.mappable_regions
        if chrom:
            mname = "{}_{}".format(
                chrom, self.mappable_regions.mappable_regions)
        filename = os.path.join(
            self.mappable_regions.work_dir,
            mname
        )
        return self.abspath(filename)

    def mappable_positions_count_filename(self):
        filename = os.path.join(
            self.bins.bins_dir,
            "B{}_mappable_positions_count.yaml".format(self.bins.bins_count)
        )
        return self.abspath(filename)

    def chrom_sizes_filename(self):
        filename = os.path.join(
            self.mappable_regions.work_dir,
            self.mappable_regions.chrom_sizes
        )
        filename = self.abspath(filename)
        return filename

    def bins_boundaries_filename(self, chrom=None):
        bname = self.bins.bins_boundaries
        if chrom:
            bname = "{}_{}".format(
                chrom, self.bins.bins_boundaries)
        filename = os.path.join(
            self.bins.bins_dir,
            bname
        )
        return self.abspath(filename)

    def chrom_filename(self, chrom, pristine=False):
        if pristine:
            cache_dir = self.genome.data_dir
        else:
            cache_dir = self.genome.work_dir
        filename = os.path.join(
            cache_dir,
            "{}.fa".format(chrom)
        )
        print(filename, self.abspath(filename))

        return self.abspath(filename)

    def varbin_filenames(self):
        if not os.path.exists(self.varbin.varbin_dir):
            return []
        dirname = self.abspath(self.varbin.varbin_dir)
        pattern = os.path.join(
            dirname,
            "*{}".format(self.varbin.varbin_suffix)
        )
        filenames = glob.glob(pattern)
        return filenames

    def varbin_filename(self, cellname):
        outfile = os.path.join(
            self.varbin_dirname(),
            "{}{}".format(cellname, self.varbin.varbin_suffix)
        )
        outfile = self.abspath(outfile)
        return outfile

    def varbin_dirname(self):
        dirname = self.abspath(self.varbin.varbin_dir)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        return dirname

    def scclust_dirname(self):
        dirname = self.abspath(self.scclust.scclust_dir)
        dirname = os.path.join(dirname, self.scclust.case_name)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return dirname

    def mapping_reads_dirname(self):
        assert os.path.exists(self.mapping.reads_dir), self.mapping.reads_dir
        dirname = self.abspath(self.mapping.reads_dir)
        return dirname

    def mapping_reads_filenames(self):
        pattern = os.path.join(
            self.mapping_reads_dirname(),
            "*{}".format(self.mapping.reads_suffix)
        )
        filenames = glob.glob(pattern)
        return filenames

    def mapping_dirname(self):
        dirname = self.abspath(self.mapping.mapping_dir)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        return dirname

    def mapping_filenames(self):
        pattern = os.path.join(
            self.mapping_dirname(),
            "*{}".format(self.mapping.mapping_suffix)
        )
        filenames = glob.glob(pattern)
        return filenames

    def check_nonempty_workdir(self, dirname):
        if not os.path.exists(dirname):
            return
        if len(os.listdir(dirname)) and \
                not self.force and not self.dry_run:
            print(colored(
                "ERROR: non-empty output directory and no --force option",
                "red"))
            raise NonEmptyWorkDirectory(dirname)

    def __getstate__(self):
        state = self.to_dict()
        state['_box_config'] = copy.copy(self._box_config)

    def __setstate__(self, state):
        self._box_config = state['_box_config']
        self.__dict__.update(state)
