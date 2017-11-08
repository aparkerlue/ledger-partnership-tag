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

### Loans between partners

When one partner lends money to another, two bookkeeping conditions
must hold in order to ensure that the real and virtual parts of the
book remain balanced:

1.  For each account, the sum of the virtual transaction amounts
    across partners must equal the real transaction amount
2.  For each partner, the sum of the virtual transaction amounts
    across accounts must be zero

Suppose `Partner1` lends `Partner2` $100. We can record the
transaction this way:

    2016-12-31 »Partnership Transfer«
        ; Partnership: Partner2
        Assets:Cash:Partner2                    $ 100.00
        Assets:Cash:Partner1

`partnership-ledger.py` replaces that transaction with this one:

    2016-12-31 »Partnership Transfer«
        ; Partnership: Partner2
        Assets:Cash:Partner2                    $ 100.00
        Assets:Cash:Partner1
        [Partner2:Assets:Cash:Partner2]         $ 100.00
        [Partner2:Assets:Cash:Partner1]        $ -100.00

This transaction moves money around via the real postings and also
keeps track of `Partner2`'s debt to `Partner1` via the virtual
postings. Condition (1) holds since the amount for
`[Partner2:Assets:Cash:Partner2]` equals that for
`Assets:Cash:Partner2`, and the amount for
`[Partner2:Assets:Cash:Partner1]` equals that for
`Assets:Cash:Partner1`. Condition (2) holds since the amounts for
`[Partner2:Assets:Cash:Partner2]` and
`[Partner2:Assets:Cash:Partner1]` sum to zero.

Keeping track of all debts requires reconciling the real and virtual
balances for every account. That process can be cumbersome, so one
solution is to periodically net all debts to an equity account that
keeps a running total of net debt.

    2016-12-31 »Partnership Reconciliation«
        ; Partnership: None
        [Partner2:Assets:Cash:Partner1]         $ 100.00
        [Partner1:Assets:Cash:Partner1]        $ -100.00
        [Partner2:Equity:Transfer Balance]      $ 100.00
        [Partner1:Equity:Transfer Balance]     $ -100.00

To round out the example, `Equity:Transfer Balance` now keeps track of
net debt, so `Partner2` can record the following transaction when
defeasing the liability:

    2016-12-31 »Rebalance Partnership Equity«
        ; Partnership: None
        Assets:Cash:Partner1                    $ 100.00
        Assets:Checking:Partner2
        [Partner1:Assets:Cash:Partner1]         $ 100.00
        [Partner2:Assets:Checking:Partner2]    $ -100.00
        [Partner1:Equity:Transfer Balance]      $ 100.00
        [Partner2:Equity:Transfer Balance]     $ -100.00

Ideally I'd like `partnership_ledger.py` to recognize shortcuts for
the foregoing transactions, but I haven't worked out an acceptable
grammar. I'd like to see something along these lines:

    2016-12-31 »Partnership Reconciliation«
        ; Partnership: Partner2 100, Partner1 -100
        Assets:Cash:Partner1                    $ 100.00
        Equity:Transfer Balance

    2016-12-31 »Partnership Partnership Equity«
        ; Partnership: + Partner1, - Partner2
        Assets:Cash:Partner1                    $ 100.00
        Assets:Checking:Partner2

Note that with more than two partners, you'll need an equity transfer
balance account for each partner in order to keep track of who owes
whom how much. With `n` partners, that means `n` real transfer balance
accounts and `n^2` virtual ones. (You could also have `n` choose 2
transfer balance accounts, which is the situation the foregoing
example describes, but that isn't a very parsimonious setup when you
have more than two partners.)

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

- [ ] 2017-09-02 After each transaction, check that real account value
  equals sum of partner account values
- [ ] 2017-09-02 Check for malformed account names (e.g. `[A:B]C]`)
- [ ] 2017-08-05 Properly handle commodities and commodity values
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
