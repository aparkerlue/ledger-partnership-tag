#!/usr/bin/env python3

from collections import OrderedDict
import ast
import re

class Posting:
    def __init__(self, account, value):
        self.account = account
        self.value = value

    def __str__(self):
        return '    {}  ${:.2f}'.format(self.account, self.value)

class RealPosting(Posting):
    def __init__(self, account, value, partnership_spec):
        super().__init__(account, value)
        self.partnership_spec = partnership_spec

    def __str__(self):
        s = [ super().__str__() ]
        if self.partnership_spec is not None and len(self.partnership_spec) > 0:
            s.append("    ; {}".format(dict(self.partnership_spec)))
            partnership_postings = self.generate_partnership_postings()
            if partnership_postings is not None and len(partnership_postings) > 0:
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
            p = [ str(p) for p in partnership_postings if p.value != 0 ]
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
        value = self.value - sum([ p.value for p in partnership_postings ])
        p = Posting(account, value)
        partnership_postings.append(p)
        return partnership_postings

    def has_complete_partnership_spec(self):
        return not bool([ v for v in self.partnership_spec.values() if v is None ])

    def resolve_elided_partnership_value(self):
        valueless_partners = [ k for k, v in self.partnership_spec.items()
                               if v is None ]
        if len(valueless_partners) == 0:
            pass
        elif len(valueless_partners) == 1:
            k = valueless_partners[0]
            explicit_total = sum([ v for k, v in self.partnership_spec.items()
                                   if v is not None ])
            elided_value = 100 - explicit_total
            self.partnership_spec[k] = elided_value
        else:
            raise Exception(
                'Multiple partners do not have values: {}'.format(
                    valueless_partners))

class Xact:
    def __init__(self):
        # List of `Posting`s
        self.real_postings = []
        # OrderedDict of partners and values
        self.partnership_spec = OrderedDict()

    def clear(self):
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
        i_valueless = [ i for i, v in
                        zip(range(len(self.real_postings)), self.real_postings)
                        if v.value is None ]
        if len(i_valueless) == 0:
            pass
        elif len(i_valueless) == 1:
            v = -sum([ Xact.interpret_value(p.value) for p in self.real_postings
                       if p.value is not None ])
            i = i_valueless[0]
            self.real_postings[i].value = v
        else:
            raise Exception(
                'Multiple postings do not have values: {}, {}'.format(
                    i_valueless, self.real_postings))

    @staticmethod
    def interpret_partnership_spec(spec):
        try:
            partnership_spec = ast.literal_eval(spec)
        except (SyntaxError, ValueError):
            partnership_spec = OrderedDict()
            components = [ tuple(s.strip().split(" "))
                           for s in spec.split(',') ]
            for c in components:
                k = c[0]
                try:
                    v = float(c[1])
                except IndexError:
                    v = None
                partnership_spec[k] = v
            if all([ v is None for v in partnership_spec.values() ]):
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
            v = float(value.translate({ ord(c): None for c in '$,' }))
        else:
            v = value
        return v

    def print_partnership_postings(self):
        self.resolve_elided_posting_value()
        for p in self.real_postings:
            p.print_partnership_postings()

    def partnership_postings(self):
        self.resolve_elided_posting_value()
        p = [ q for p in self.real_postings for q in p.partnership_postings() ]
        return p

def adjoin_partnership_postings(filepath):
    # Transaction begin pattern
    trbegpat = re.compile(r'^\d')
    # Transaction end pattern
    trendpat = re.compile(r'(^[^\s]|^[\s]*$)')
    # Real posting pattern
    rpostpat = re.compile(r'^\s+(?P<account>[\w\-,\'()、]+(\s?[\w\-,\'()、:]+)*)(\s{2,}(?P<value>-?\$?\s*-?[\d]+(,\d+)*(\.\d+)?))?')
    # Partnership key pattern
    shkeypat = re.compile(r';\s*Partnership\s*:(.*)')

    journal = []
    partnershipless_xact_lines = []

    xact = Xact()
    bInXact = False
    b_found_partnership_tag = False
    lineno = 0
    with open(filepath, 'r') as f:
        for line in f:
            lineno += 1
            if bInXact:
                if trendpat.match(line):
                    # At end of transaction
                    journal.extend(xact.partnership_postings())
                    bInXact = False
                    if b_found_partnership_tag:
                        partnershipless_xact_lines.pop()
                else:
                    m = rpostpat.match(line)
                    if m:
                        xact.add_posting(m.group('account'), m.group('value'))
                    else:
                        m = shkeypat.search(line)
                        if m:
                            b_found_partnership_tag = True
                            partnership = m.group(1).strip()
                            xact.add_partnership(partnership)

            if not bInXact and trbegpat.match(line):
                # At beginning of transaction
                bInXact = True
                partnershipless_xact_lines.append(lineno)
                b_found_partnership_tag = False
                xact.clear()
                m = shkeypat.search(line)
                if m:
                    partnership = ast.literal_eval(m.group(1).strip())
                    xact.add_partnership(partnership)

            journal.append(line.rstrip())

    if bInXact:
        journal.extend(xact.partnership_postings())
        bInXact = False
        if b_found_partnership_tag:
            partnershipless_xact_lines.pop()

    return (journal, partnershipless_xact_lines)

if __name__ == "__main__":
    import argparse
    import subprocess
    import sys

    parser = argparse.ArgumentParser(
        description = 'Generate virtual partnership postings for journal and run Ledger.')
    parser.add_argument('-f', '--file', metavar = 'FILE', nargs = '*',
                        help = 'read journal data from FILE')
    parser.add_argument('-N', '--just-print',
                        action = 'store_true',
                        help = 'print journal with partnership postings and exit')
    (args, ledger_args) = parser.parse_known_args()
    filepaths = args.file
    just_print = args.just_print

    if filepaths is None:
        if just_print:
            print("Error: No journal file specified", file = sys.stderr)
            sys.exit(1)
        else:
            subprocess.run([ 'ledger' ] + ledger_args)
    else:
        journal = []
        for f in filepaths:
            (j, partnershipless_xact_lines) = adjoin_partnership_postings(f)
            n = len(partnershipless_xact_lines)
            if n > 0:
                print("Error: Found {} transactions in {} that do not have partnership tags; see lines: {}".format(n, f, partnershipless_xact_lines),
                      file = sys.stderr)
                sys.exit(1)
            journal.extend(j)
        if just_print:
            for line in journal:
                print(line)
        elif len(ledger_args) == 0:
            print("Error: No ledger arguments provided", file = sys.stderr)
            sys.exit(1)
        else:
            journal_string = '\n'.join(journal) + '\n'
            encoded_journal_string = journal_string.encode('utf-8')
            subprocess.run([ 'ledger', '-f', '-' ] + ledger_args,
                           input = encoded_journal_string)
