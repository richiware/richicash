# Copyright 2019 Ricardo González
# Licensed under the Apache License, Version 2.0

import argparse
import datetime
import csv
import logging
import os
import subprocess
import sys
from enum import Enum
from pathlib import Path

from .defaults import Defaults
from .transactional_accounts import TransactionalAccounts


defaults = Defaults()
transactional_accounts = TransactionalAccounts(defaults)


class Origin(Enum):
    ACCOUNT = 1
    CARD = 2


logger = None
type_operation = Origin.ACCOUNT
defaults = None


def arg_parser(
        args):
    """Parse the arguments"""

    global logger
    global type_operation

    parser = argparse.ArgumentParser(
            prog='richicash',
            description='Utility to transform my expenses to a Gnucash format.'
            )
    parser.add_argument(
            '--debug',
            action='store_true',
            help='Print debug info.'
            )
    parser.add_argument(
            '-c', '--card',
            action='store_true',
            help='A card is the origin of the transactions.'
            )
    parser.add_argument(
            '-a', '--account',
            action='store_true',
            help='An account is the origin of the transactions. By default.'
            )
    parser.add_argument(
            'file',
            nargs=1,
            help='XLS file with the transactions.'
            )

    verb = parser.parse_args(args)
    # Set log level
    if verb.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if verb.card and verb.account:
        logger.error('Not permitted selection of card origin and account origin at the same time')
        sys.exit(-1)

    if verb.card:
        type_operation = Origin.CARD

    return verb.file[0]


def remove_strange_chars(
        text):
    return str.replace(text, '\xa0', ' ').strip()


def parse_date(
        original_date):
    """Parse a date coming from my bank to a supported one by gnucash"""

    try:
        aux_datetime = datetime.datetime.strptime(original_date, "%d/%m/%Y")
    except Exception:
        aux_datetime = datetime.datetime.strptime(original_date, "%Y/%m/%d")

    return aux_datetime.strftime("%d-%m-%Y")


def account_csv_to_gnucash_csv(
        tmp_csv_file,
        csv_file):
    """
    Converts a generated CSV by 'sscovert' to a supported by gnucash.

    Format of the generated CSV:
    - Date
    - Description
    - Annotations
    - Deposit
    - Transactional account
    """
    global transactional_accounts

    with open(csv_file, 'w') as csv_file_descriptor:
        csv_writer = csv.writer(csv_file_descriptor)
        with open(tmp_csv_file) as tmp_csv_file_descriptor:
            csv_reader = csv.reader(tmp_csv_file_descriptor)

            for row in csv_reader:
                if row[4] != "":
                    date = parse_date(row[4])
                    incoming = row[6]
                    if incoming == "":
                        incoming = "-" + row[7]
                    card_ref = str.strip(row[13])
                    description =  str.strip(row[14])
                    csv_writer.writerow([date, description, str.strip(row[15] + " " + row[16] + " " + row[17] + " " +
                        row[18] + " " + row[19] + " " + row[20] + " " + row[21] + " " + row[22] + " " + row[23]),
                        incoming,
                        transactional_accounts.deduce(description, card_ref)])
        return

def card_csv_to_gnucash_csv(
        tmp_csv_file,
        csv_file):
    """
    Converts a generated CSV by 'sscovert' to a supported by gnucash.

    Format of the generated CSV:
    - Date
    - Description
    - Reduction
    - Transactional account
    - Card account
    """
    global transactional_accounts

    with open(csv_file, 'w') as csv_file_descriptor:
        csv_writer = csv.writer(csv_file_descriptor)
        with open(tmp_csv_file) as tmp_csv_file_descriptor:
            csv_reader = csv.reader(tmp_csv_file_descriptor)

            for row in csv_reader:
                if row[0] != "":
                    date = parse_date(remove_strange_chars(row[0]))
                    incoming = remove_strange_chars(row[3]).replace('EUR', '').strip()
                    card_ref = remove_strange_chars(row[1]).replace(' ', '')
                    description = remove_strange_chars(row[2])
                    csv_writer.writerow([date, description,
                        incoming,
                        transactional_accounts.deduce(description, card_ref),
                        transactional_accounts.get_card_account(card_ref)])
        return


def xls_convert_to_csv(
        xls_file):
    """
    Convert XLS file provided by my bank to a CSV file.
    'ssconvert' is used for this kind of excel.
    """

    tmp_csv_file = '/tmp/{}.csv'.format(Path(xls_file).stem)
    csv_file = '{}.csv'.format(Path(xls_file).stem)
    pid = os.getpid()
    command = 'ssconvert "{}" /tmp/movimientos_{}.tmp.csv && tail -n +4 /tmp/movimientos_{}.tmp.csv &> "{}"'.format(
            xls_file, pid, pid, tmp_csv_file)
    logger.debug("Running command '{}'".format(command))
    execution = subprocess.run(command, shell=True)

    if 0 != execution.returncode:
        logger.error('Error executing ssconvert application: {}'.format(execution.stderr))
        sys.exit(-1)

    if Origin.ACCOUNT == type_operation:
        account_csv_to_gnucash_csv(tmp_csv_file, csv_file)
    else:
        card_csv_to_gnucash_csv(tmp_csv_file, csv_file)


def main(argv=None):
    """
    Starting point of the command.

    Logic
    -----

    - Get arguments
    - Convert XLS file to a CSV file.
    - Transform CSV to a valid Gnucash CSV.
    """

    # Create a custom logger
    global logger
    logger = logging.getLogger(__name__)
    # - Create handlers
    c_handler = logging.StreamHandler()
    # - Create formatters and add it to handlers
    c_format = '[%(asctime)s][richicash][%(levelname)s] %(message)s'
    c_format = logging.Formatter(c_format)
    c_handler.setFormatter(c_format)
    # - Add handlers to the logger
    logger.addHandler(c_handler)

    xls_file = arg_parser(argv)

    xls_convert_to_csv(xls_file)
