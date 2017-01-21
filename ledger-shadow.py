#!/usr/bin/env python3

import argparse
import ast
import re

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

bInXact = False
with open(filepath) as f:
    for line in f:
        if bInXact:
            if trendpat.match(line):
                if shadow:
                    print('    ; {}: {}'.format(type(shadow), shadow))
                for p in postings:
                    print('    [{}]'.format(p))
                bInXact = False
            else:
                m = rpostpat.match(line)
                if m:
                    postings.append(m.group(1))
                else:
                    m = shkeypat.search(line)
                    if m:
                        shadow = ast.literal_eval(m.group(1).strip())

        if not bInXact and trbegpat.match(line):
            bInXact = True
            postings = []
            shadow = None
            m = shkeypat.search(line)
            if m:
                shadow = ast.literal_eval(m.group(1).strip())

        print(line, end='')

if bInXact:
    if shadow:
        print('    ; {}: {}'.format(type(shadow), shadow))
    for p in postings:
        print('    [{}]'.format(p))
    bInXact = False
