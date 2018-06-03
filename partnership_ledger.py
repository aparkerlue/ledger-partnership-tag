#!/usr/bin/env python3

from collections import OrderedDict
import os
import re


class Posting:
    def __init__(self, account, value):
        self.account = account
        self.value = value

    def __str__(self):
        return '    {}  $ {:.2f}'.format(self.account, self.value)


class RealPosting(Posting):
    def __init__(self, account, value, partnership_spec):
        super().__init__(account, value)
        self.partnership_spec = partnership_spec

    def __str__(self):
        s = [super().__str__()]
        if (self.partnership_spec is not None
                and len(self.partnership_spec) > 0):
            s.append("    ; {}".format(dict(self.partnership_spec)))
            partnership_postings = self.generate_partnership_postings()
            if (partnership_postings is not None
                    and len(partnership_postings) > 0):
                for p in partnership_postings:
                    s.append(str(p))
        return '\n'.join(s)

    def print_partnership_postings(self):
        partnership_postings = self.generate_partnership_postings()
        if partnership_postings is not None:
            for p in partnership_postings:
                if p.value != 0:
                    print(p)

    def partnership_postings(self):
        partnership_postings = self.generate_partnership_postings()
        if partnership_postings is not None:
            p = [str(p) for p in partnership_postings if p.value != 0]
        else:
            p = []
        return p

    def generate_partnership_postings(self):
        if self.partnership_spec is None:
            return
        if not self.has_complete_partnership_spec():
            self.resolve_elided_partnership_value()
        partnership_postings = []
        keys = list(self.partnership_spec.keys())
        if len(keys) == 0:
            return
        elif len(keys) == 1:
            k_last = keys[0]
        else:
            # Calculate values for all but last partner
            for k in keys[:-1]:
                account = "[{}:{}]".format(k, self.account)
                value = round(1e-2 * self.partnership_spec[k] * self.value, 2)
                p = Posting(account, value)
                partnership_postings.append(p)
            k_last = keys[-1]
        # Set last partner's value to residual
        account = "[{}:{}]".format(k_last, self.account)
        value = self.value - sum([p.value for p in partnership_postings])
        p = Posting(account, value)
        partnership_postings.append(p)
        return partnership_postings

    def has_complete_partnership_spec(self):
        return not bool([v for v in self.partnership_spec.values()
                         if v is None])

    def resolve_elided_partnership_value(self):
        valueless_partners = [k for k, v in self.partnership_spec.items()
                              if v is None]
        if len(valueless_partners) == 0:
            pass
        elif len(valueless_partners) == 1:
            k = valueless_partners[0]
            explicit_total = sum([v for k, v in self.partnership_spec.items()
                                  if v is not None])
            elided_value = 100 - explicit_total
            self.partnership_spec[k] = elided_value
        else:
            raise Exception(
                'Multiple partners do not have values: {}'.format(
                    valueless_partners))


class Xact:
    def __init__(self, lines=None):
        # Raw transaction lines
        self.lines = []
        # List of real `Posting`s
        self.real_postings = []
        # OrderedDict of partners and values
        self.partnership_spec = OrderedDict()

        if lines is not None:
            self.add_lines(lines)

    def clear(self):
        del self.lines[:]
        del self.real_postings[:]
        self.partnership_spec.clear()

    def add_posting(self, account, value):
        if type(value) is str:
            value = Xact.interpret_value(value)
        p = RealPosting(account, value, self.partnership_spec)
        self.real_postings.append(p)

    def add_partnership(self, partnership_spec):
        s = Xact.interpret_partnership_spec(partnership_spec)
        if s is not None:
            self.partnership_spec.update(s)

    def resolve_elided_posting_value(self):
        '''Determine and assign elided posting values.

        :return: None
        '''
        i_valueless = [i for i, v in
                       zip(range(len(self.real_postings)), self.real_postings)
                       if v.value is None]
        if len(i_valueless) == 0:
            pass
        elif len(i_valueless) == 1:
            v = -sum([Xact.interpret_value(p.value) for p in self.real_postings
                      if p.value is not None])
            i = i_valueless[0]
            self.real_postings[i].value = v
        else:
            raise Exception(
                'Multiple postings do not have values: {}, {}'.format(
                    i_valueless, self.real_postings))

    @staticmethod
    def interpret_partnership_spec(spec):
        '''Interpret a partnership specification.

        :return: Ordered dictionary of partnership values.
        '''
        if spec.strip() != "None":
            partnership_spec = OrderedDict()
            components = [tuple(s.strip().split(" ", maxsplit=1))
                          for s in spec.split(',')]
            for c in components:
                k = c[0]
                try:
                    v = float(c[1])
                except IndexError:
                    v = None
                partnership_spec[k] = v
            if all([v is None for v in partnership_spec.values()]):
                n = len(partnership_spec)
                if n > 1:
                    v = round(100 / n, 2)
                    keys = list(partnership_spec.keys())
                    for k in keys[:-1]:
                        partnership_spec[k] = v
            return partnership_spec

    @staticmethod
    def interpret_value(value):
        if type(value) is str:
            v = float(value.translate({ord(c): None for c in '$,'}))
        else:
            v = value
        return v

    def print_partnership_postings(self):
        '''Print partnership postings for this transaction.
        '''
        self.resolve_elided_posting_value()
        for p in self.real_postings:
            p.print_partnership_postings()

    def partnership_postings(self):
        '''Generate partnership postings for this transaction.

        :return: List of postings
        '''
        self.resolve_elided_posting_value()
        p = [q for p in self.real_postings for q in p.partnership_postings()]
        return p

    def get_all_lines(self):
        '''Get all lines of this transaction.

        :return: List of transaction lines
        '''
        xact_lines = self.lines + self.partnership_postings()
        return xact_lines

    def has_partnership_spec(self):
        '''Return whether the transaction has a partnership specification.
        '''
        for line in self.lines:
            if self.shkeypat.search(line):
                return True
        return False

    def add_line(self, line):
        '''Add line to transaction.

        :return: None
        '''
        self.lines.append(line)
        m_rpost = self.rpostpat.match(line)
        if m_rpost:
            self.add_posting(
                m_rpost.group('account'),
                m_rpost.group('value')
            )
        m_shkey = self.shkeypat.search(line)
        if m_shkey:
            partnership = m_shkey.group(1).strip()
            self.add_partnership(partnership)

    def add_lines(self, lines):
        for line in lines:
            self.add_line(line)

    # Real posting pattern
    rpostpat = re.compile(
        r'^\s+(?P<account>[\w\-,\'()、]+(\s?[\w\-,\'()、:]+)*)'
        r'(\s{2,}(?P<value>-?\$?\s*-?[\d]+(,\d+)*(\.\d+)?))?'
    )
    # Partnership key pattern
    shkeypat = re.compile(r';\s*Partnership\s*:\s*(.*)')


def adjoin_partnership_postings(filepath):
    # Transaction begin pattern
    trbegpat = re.compile(r'^\d')
    # Transaction end pattern
    trendpat = re.compile(r'(^[^\s]|^[\s]*$)')

    journal = []
    xact_linenos = []
    partnershipless_xact_lines = []

    xact = Xact()
    bInXact = False
    lineno = 0
    with open(os.path.expanduser(filepath), 'r') as f:
        for line in f:
            lineno += 1
            if not bInXact:
                if trbegpat.match(line):
                    bInXact = True
                    xact_linenos.append(lineno)
                    xact.clear()
                    xact.add_line(line.rstrip('\n\r'))
                else:
                    journal.append(line.rstrip('\n\r'))
            else:
                if trbegpat.match(line) or trendpat.match(line):
                    if not xact.has_partnership_spec():
                        partnershipless_xact_lines.append(xact_linenos[-1])
                    journal.extend(xact.get_all_lines() + [''])
                    bInXact = False
                    if trbegpat.match(line):
                        bInXact = True
                        xact_linenos.append(lineno)
                        xact.clear()
                        xact.add_line(line.rstrip('\n\r'))
                else:
                    xact.add_line(line.rstrip('\n\r'))

    return (journal, partnershipless_xact_lines)


def infer_filepaths(args):
    if args.file is None and args.path is None:
        return read_file_args_from_ledgerrc()

    filepaths = []
    if args.file is not None:
        filepaths.extend(args.file)
    if args.path is not None:
        path = args.path[0]
        x = [os.path.join(path, f) for f in os.listdir(path)
             if os.path.isfile(os.path.join(path, f))]
        filepaths.extend(x)
    return filepaths


def read_file_args_from_ledgerrc():
    '''Read file arguments from `~/.ledgerrc`.

    :return: List of filepaths.
    '''
    try:
        with open(os.path.expanduser('~/.ledgerrc')) as f:
            ledger_files = [
                line.split(maxsplit=1)[1].strip()
                for line in f
                if (line.split(maxsplit=1)
                    and line.split(maxsplit=1)[0] == '--file')
            ]
    except (FileNotFoundError, IndexError):
        return None
    return ledger_files


if __name__ == "__main__":
    import argparse
    import subprocess
    import sys

    parser = argparse.ArgumentParser(
        description=(
            'Generate virtual partnership postings for journal '
            'and run Ledger.'
        )
    )
    parser.add_argument('-f', '--file', metavar='FILE', nargs='+',
                        help='read journal data from FILE')
    parser.add_argument('--path', metavar='PATH', nargs=1,
                        help='read journal files in PATH')
    parser.add_argument(
        '-N',
        '--just-print',
        action='store_true',
        help='print journal with partnership postings and exit'
    )
    (args, ledger_args) = parser.parse_known_args()
    filepaths = infer_filepaths(args)
    just_print = args.just_print

    if filepaths is None:
        if just_print:
            print("Error: No journal file specified", file=sys.stderr)
            sys.exit(1)
        else:
            subprocess.run(['ledger'] + ledger_args)
    else:
        journal = []
        for f in filepaths:
            (j, partnershipless_xact_lines) = adjoin_partnership_postings(f)
            n = len(partnershipless_xact_lines)
            if n > 0:
                print(
                    "Error: Found {} transactions in {} "
                    "that do not have partnership tags; "
                    "see lines: {}"
                    .format(n, f, partnershipless_xact_lines),
                    file=sys.stderr
                )
                sys.exit(1)
            journal.extend(j)
        if just_print:
            for line in journal:
                print(line)
        elif len(ledger_args) == 0:
            print("Error: No ledger arguments provided", file=sys.stderr)
            sys.exit(1)
        else:
            journal_string = '\n'.join(journal) + '\n'
            encoded_journal_string = journal_string.encode('utf-8')
            subprocess.run(['ledger', '-f', '-'] + ledger_args,
                           input=encoded_journal_string)
