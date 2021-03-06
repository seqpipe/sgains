'''
Created on Aug 2, 2017

@author: lubo
'''


def test_prepare_long(
        argparser, tests_config, prepare_command, mocker):

    prepare_command.add_options(tests_config)

    argv = [
        "--dry-run", "--force",
        "--config", "tests/data/scpipe_tests.yml",
        "prepare",
        "--mappable-dir", "data/proba",
        "--genome-index", "genomeindex",
        "--genome-dir", "data/hg19/",
        "--read-length", "200",
        "--bowtie-opts", "-1 -2 -3",
    ]

    with mocker.patch("os.path.exists"), \
            mocker.patch("sgains.config.Config.mapping_reads_filenames"), \
            mocker.patch("os.listdir"):

        args = argparser.parse_args(argv)
        args.func(args)

        config = prepare_command.config
        assert config is not None

        assert config.force
        assert config.dry_run

        assert config.genome.work_dir == "data/hg19/"
        assert config.genome.index == "genomeindex"

        assert config.mappable_regions.length == 200
        assert config.mappable_regions.work_dir == "data/proba"
        assert config.mappable_regions.bowtie_opts == "-1 -2 -3"
