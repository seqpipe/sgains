#!/usr/bin/env python
# encoding: utf-8
'''
Created on Jul 20, 2017

@author: lubo
'''
from argparse import ArgumentParser,\
    RawDescriptionHelpFormatter
import os
import sys
import traceback

from sgains.commands.bins_command import BinsCommand
from sgains.commands.genomeindex_command import GenomeIndexCommand
from sgains.commands.mappable_regions_command import MappableRegionsCommand
from sgains.commands.mapping_command import MappingCommand
from sgains.commands.prepare_command import PrepareCommand
from sgains.commands.process_command import ProcessCommand
from sgains.commands.sc_clust_command import SCclustCommand
from sgains.commands.varbin_command import VarbinCommand
from sgains.config import Config
from sgains.commands.common import OptionsBase


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):

        return self.msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    else:
        argv.extend(sys.argv)

    # Setup argument parser
    program_name = os.path.basename(sys.argv[0])
    program_shortdesc = \
        'sgains - sparse genomic analysis of individual nuclei by ' \
        'sequencing pipeline'
    program_description = '''%s

USAGE
''' % (program_shortdesc, )

    try:
        import setproctitle  # @UnresolvedImport
        setproctitle.setproctitle('sgains')
    except ImportError:
        pass

    try:

        defaults_config = Config.parse_args(argv)

        argparser = ArgumentParser(
            description=program_description,
            formatter_class=RawDescriptionHelpFormatter)

        OptionsBase.common_options(argparser)

        subparsers = argparser.add_subparsers(
            title="subcommands"
        )

        process_command = ProcessCommand(
            argparser, subparsers)
        process_command.add_options(defaults_config)

        prepare_command = PrepareCommand(
            argparser, subparsers)
        prepare_command.add_options(defaults_config)

        genomeindex_command = GenomeIndexCommand(
            argparser, subparsers)
        genomeindex_command.add_options(defaults_config)

        mappable_regions_command = MappableRegionsCommand(
            argparser, subparsers)
        mappable_regions_command.add_options(defaults_config)

        bins_command = BinsCommand(
            argparser, subparsers)
        bins_command.add_options(defaults_config)

        mapping_command = MappingCommand(
            argparser, subparsers)
        mapping_command.add_options(defaults_config)

        varbin_command = VarbinCommand(
            argparser, subparsers)
        varbin_command.add_options(defaults_config)

        scclust_command = SCclustCommand(
            argparser, subparsers)
        scclust_command.add_options(defaults_config)

        args = argparser.parse_args(argv[1:])
        args.func(args)

        return 0
    except KeyboardInterrupt:
        traceback.print_exc()
        return 0
    except Exception as e:
        traceback.print_exc()

        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        sys.stderr.write('\n')
        return 2


if __name__ == "__main__":
    sys.exit(main())
