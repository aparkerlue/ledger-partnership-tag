#!/usr/bin/env python3

import argparse
import ast
import re

class Xact:
    def __init__(self):
        self.postings = []
        self.shadow = None

    def clear(self):
        self.postings = []
        self.shadow = None

    def add_posting(self, posting):
        self.postings.append(posting)

    def add_shadow(self, shadow):
        self.shadow = shadow

    def print(self):
        if self.shadow:
            print('    ; {}: {}'.format(type(shadow), shadow))
        for p in self.postings:
            print('    [{}]'.format(p))

# Transaction begin pattern
trbegpat = re.compile(r'^\d')
# Transaction end pattern
trendpat = re.compile(r'(^[^\s]|^[\s]*$)')
# Real posting pattern
rpostpat = re.compile(r'^\s+([\w\-]+(\s?[\w\-:]+)*)(\s{2,}[\d]+(\.\d+)?)?')
# Shadow key pattern
shkeypat = re.compile(r';\s*Shadow\s*:(.*)')

parser = argparse.ArgumentParser(description='Generate shadow postings for Ledger journal.')
parser.add_argument('journal', help='Ledger journal file')
args = parser.parse_args()
filepath = args.journal

xact = Xact()
bInXact = False
with open(filepath) as f:
    for line in f:
        if bInXact:
            if trendpat.match(line):
                xact.print()
                bInXact = False
            else:
                m = rpostpat.match(line)
                if m:
                    xact.add_posting(m.group(1))
                else:
                    m = shkeypat.search(line)
                    if m:
                        shadow = ast.literal_eval(m.group(1).strip())
                        xact.add_shadow(shadow)

        if not bInXact and trbegpat.match(line):
            bInXact = True
            xact.clear()
            m = shkeypat.search(line)
            if m:
                shadow = ast.literal_eval(m.group(1).strip())
                xact.add_shadow(shadow)

        print(line, end='')

if bInXact:
    xact.print()
    bInXact = False
