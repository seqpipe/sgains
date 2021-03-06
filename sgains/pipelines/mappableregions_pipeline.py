'''
Created on Jul 31, 2017

@author: lubo
'''
from sgains.genome import Genome
import asyncio
from termcolor import colored
import os
from Bio.SeqRecord import SeqRecord  # @UnresolvedImport

from sgains.utils import MappableState, Mapping, MappableRegion, LOG
import sys
import multiprocessing
import shutil
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)7s: %(message)s',
    stream=sys.stderr,
)


class MappableRegionsPipeline(object):

    def __init__(self, config):
        self.config = config
        self.hg = Genome(self.config)

    def mappable_regions_check(self, chroms, mappable_regions_df):
        # if mappable_regions_df is None:
        #     mappable_regions_df = self.load_mappable_regions()

        for chrom in chroms:
            chrom_df = mappable_regions_df[mappable_regions_df.chrom == chrom]
            chrom_df = chrom_df.sort_values(
                by=['chrom', 'start_pos', 'end_pos'])
            start_pos_count = len(chrom_df.start_pos.unique())
            if start_pos_count < len(chrom_df):
                LOG.error(
                    "chrom {} has duplicate mappable regions".format(chrom))

    def generate_reads(self, chroms, read_length):
        try:
            for chrom in chroms:
                seq_record = self.hg.load_chrom(chrom)
                for i in range(len(seq_record) - read_length + 1):
                    out_record = SeqRecord(
                        seq_record.seq[i: i + read_length],
                        id="{}.{}".format(chrom, i + 1),
                        description="generated_read"
                    )
                    yield out_record
        finally:
            pass

    async def async_start_bowtie(self, bowtie_opts=""):
        genomeindex = self.config.genome_index_filename()
        if bowtie_opts:
            command = [
                'bowtie', '-S', '-t', '-v', '0', '-m', '1',
                *bowtie_opts.split(' '),
                '-f', genomeindex, '-',
            ]
        else:
            command = [
                'bowtie', '-S', '-t', '-v', '0', '-m', '1',
                '-f', genomeindex, '-',
            ]
        print(colored(
            "going to execute bowtie: {}".format(" ".join(command)),
            "green"
        ))
        create = asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        proc = await create
        return proc

    @staticmethod
    async def async_write_fasta(outfile, rec):
        out = Genome.to_fasta_string(rec)
        outfile.write(out)
        await outfile.drain()

    async def async_write_reads_generator(self, out, reads_generator):
        for rec in reads_generator:
            await self.async_write_fasta(out, rec)
        out.close()

    async def async_mappings_generator(self, reads_generator, bowtie):
        writer = asyncio.Task(
            self.async_write_reads_generator(bowtie.stdin, reads_generator)
        )

        while True:
            line = await bowtie.stdout.readline()
            if not line:
                break
            yield line.decode()

        await bowtie.wait()
        await writer

    async def async_generate_mappings(
            self, chroms, read_length, outfile=None):
        if outfile is None:
            outfile = sys.stdout

        bowtie = await self.async_start_bowtie()
        reads_generator = self.generate_reads(chroms, read_length)
        async for mappings in self.async_mappings_generator(
                reads_generator, bowtie):
            outfile.write(mappings)

    async def async_generate_mappable_regions(
            self, chroms, read_length,
            outfile=None, bowtie_opts=""):

        bowtie = await self.async_start_bowtie(bowtie_opts=bowtie_opts)
        reads_generator = self.generate_reads(chroms, read_length)
        writer = asyncio.Task(
            self.async_write_reads_generator(bowtie.stdin, reads_generator)
        )
        if outfile is None:
            outfile = sys.stdout
        async for mapping in self.async_mappable_regions_generator(
                bowtie.stdout):
            outfile.write(str(mapping))
            outfile.write('\n')
        await bowtie.wait()
        await writer

    async def async_mappable_regions_generator(self, infile):
        prev = None
        state = MappableState.OUT

        while True:
            line = await infile.readline()
            if not line:
                break
            line = line.decode()
            if line[0] == '@':
                # comment
                continue

            mapping = Mapping.parse_sam(line)

            if state == MappableState.OUT:
                if mapping.flag == 0:
                    prev = MappableRegion(mapping)
                    state = MappableState.IN
            else:
                if mapping.flag == 0:
                    if mapping.chrom == prev.chrom:
                        prev.extend(mapping.start)
                    else:
                        yield prev
                        prev = MappableRegion(mapping)
                else:
                    yield prev
                    state = MappableState.OUT

        if state == MappableState.IN:
            yield prev

    def run_once(self, chrom):
        event_loop = asyncio.get_event_loop()

        # LOG.info('enabling debugging')
        # Enable debugging
        # event_loop.set_debug(True)

        outfilename = self.config.mappable_regions_filename(chrom)
        with open(outfilename, "w") as outfile:
            event_loop.run_until_complete(
                self.async_generate_mappable_regions(
                    [chrom],
                    self.config.mappable_regions.length,
                    outfile=outfile,
                    bowtie_opts=self.config.mappable_regions.bowtie_opts)
            )

    def concatenate_all_chroms(self):
        dst = self.config.mappable_regions_filename()
        if os.path.exists(dst) and not self.config.force:
            print(colored(
                "destination mappable regions file already exists"
                "use --force to overwrite", "red"))
            raise ValueError("destination file exists... use --force")

        if not self.config.dry_run:
            with open(dst, 'wb') as output:
                for chrom in self.hg.version.CHROMS:
                    src = self.config.mappable_regions_filename(chrom)
                    print(colored(
                        "appending {} to {}".format(src, dst),
                        "green"))
                    with open(src, 'rb') as src:
                        if not self.config.dry_run:
                            shutil.copyfileobj(src, output, 1024 * 1024 * 10)

    def run(self):
        outfilename = self.config.mappable_regions_filename()
        print(colored(
            "going to generate mappable regions with length {} "
            "from genome {} into {}".format(
                self.config.mappable_regions.length,
                self.config.genome.work_dir,
                outfilename
            ),
            "green"))

        if os.path.exists(outfilename) and not self.config.force:
            print(colored(
                "output file {} already exists; "
                "use --force to overwrite".format(outfilename),
                "red"))
            raise ValueError("output file already exists")

        if not self.config.genome_index_filename_exists():
            print(colored(
                "genome index file {} not found".format(
                    self.config.genome_index_filename()),
                "red"))
            raise ValueError("genome index file not found")

        if self.config.dry_run:
            return

        if not os.path.exists(self.config.mappable_regions.work_dir):
            os.makedirs(self.config.mappable_regions.work_dir)

        pool = multiprocessing.Pool(processes=self.config.parallel)
        pool.map(self.run_once, self.hg.version.CHROMS)

        self.concatenate_all_chroms()
