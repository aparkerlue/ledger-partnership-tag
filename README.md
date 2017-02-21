# ledger-partnership-tag #

`partnership_ledger.py` is a Python script that facilitates
[partnership accounting](https://en.wikipedia.org/wiki/Partnership_accounting)
in [Ledger](http://www.ledger-cli.org/) using a `Partnership` tag. This
enables you to track equity ownership stakes in a book of accounts,
which is useful for any situation that involves multiple stakeholders:
households, joint ventures, and investment clubs for example.

## Invocation ##

Invoke `partnership_ledger.py` in lieu of `ledger`. A few examples using
`Example.ledger`.

    $ partnership_ledger.py -f Example.ledger bal --real
                $1240.00  Assets:Cash:Checking
                $1045.00  Expenses
                 $960.00    Rent
                  $85.00    Utilities
               $-2200.00  Income:Salary
                 $-85.00  Liabilities:Credit:Visa
    --------------------
                       0
    $ partnership_ledger.py -f Example.ledger bal ^Partner1
                       0  Partner1
                 $520.00    Assets:Cash:Checking
                 $522.50    Expenses
                 $480.00      Rent
                  $42.50      Utilities
               $-1000.00    Income:Salary
                 $-42.50    Liabilities:Credit:Visa
    --------------------
                       0
    $ partnership_ledger.py -f Example.ledger bal ^Partner2
                       0  Partner2
                 $720.00    Assets:Cash:Checking
                 $522.50    Expenses
                 $480.00      Rent
                  $42.50      Utilities
               $-1200.00    Income:Salary
                 $-42.50    Liabilities:Credit:Visa
    --------------------
                       0

## Partnership accounting with `partnership_ledger.py` ##

To track partnership stakes:

1. Include a `Partnership` tag with each transaction in your Ledger
   journal
2. Run `partnership_ledger.py` in lieu of `ledger`

For example, a transaction involving two partners might look like this:

    2016-12-31 Bank
        ; Partnership: Partner1 60, Partner2 40
	    Assets:Cash:Checking                    $1000.00
	    Assets:Cash:Savings

This transaction represents a transfer of $1,000 from the partners'
savings account to their checking account; Partner1's share of the
transfer is $600, and Partner2's share of the transfer is $400.
`partnership_ledger.py` processes this transaction using virtual
postings:

    2016-12-31 Bank
        ; Partnership: Partner1 60, Partner2 40
	    Assets:Cash:Checking                    $1000.00
	    Assets:Cash:Savings
	    [Partner1:Assets:Cash:Checking]          $600.00
	    [Partner1:Assets:Cash:Savings]          $-600.00
	    [Partner2:Assets:Cash:Checking]          $400.00
	    [Partner2:Assets:Cash:Savings]          $-400.00

## Additional notes ##

In order to fully implement partnership accounting in a journal, every
transaction should have a `Partnership` tag that reveals the share of
partnership stakes. Transactions that are not meant to include
partnership stakes should include an explicit tag:

        ; Partnership: None

`partnership_ledger.py` is a stopgap:

- A robust solution would use Ledger's Python facilities, but I just
  couldn't figure them out with Python 3.
- It only works with U.S. dollar posting values.

It would be great if Ledger included built-in support for a
`Partnership` tag. :)

## To do ##

- [x] 2017-02-18 Process `、` correctly
- [ ] 2017-02-12 Print all partnership postings for each partner
  together
- [ ] 2017-02-12 Error checking: For each real posting, check that sum
  of virtual partnership postings equals real posting value
- [ ] 2017-02-09 First run Ledger to make sure that the journal file
  does not have errors
- [ ] 2017-02-07 Modify code to just delete the Xact and start over
  (instead of clearing the Xact)
- [x] 2017-02-05 Add stub to indicate that this transaction is not
  supposed to have a partnership tag
- [x] 2017-01-26 `Partnership: X` allocates 100% to X
- [x] 2017-01-23 Add way to check which transactions do not have
  Partnership tags
