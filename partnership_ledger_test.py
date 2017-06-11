import partnership_ledger
import unittest

class ExampleTransactions(unittest.TestCase):
    def test_transaction_1(self):
        transaction = """
2017-01-06 (#1) MTA
    ; Partnership: Partner1
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
""".strip()
        full_transaction = """
2017-01-06 (#1) MTA
    ; Partnership: Partner1
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
    [Partner1:Assets:Cash:Checking]  $ 1000.00
    [Partner1:Income:Salary]  $ -1000.00
""".strip()
        x = partnership_ledger.Xact(transaction.split('\n'))
        result = x.get_all_lines()
        self.assertEqual(full_transaction.split('\n'), result)

    def test_transaction_none(self):
        transaction = """
2017-01-06 (#2) MTA
    ; Partnership: None
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
""".strip()
        full_transaction = """
2017-01-06 (#2) MTA
    ; Partnership: None
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
""".strip()
        x = partnership_ledger.Xact(transaction.split('\n'))
        result = x.get_all_lines()
        self.assertEqual(full_transaction.split('\n'), result)

    def test_transaction_equal_split(self):
        transaction = """
2017-01-06 (#3) MTA
    ; Partnership: A, B
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
""".strip()
        full_transaction = """
2017-01-06 (#3) MTA
    ; Partnership: A, B
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
    [A:Assets:Cash:Checking]  $ 500.00
    [B:Assets:Cash:Checking]  $ 500.00
    [A:Income:Salary]  $ -500.00
    [B:Income:Salary]  $ -500.00
""".strip()
        x = partnership_ledger.Xact(transaction.split('\n'))
        result = x.get_all_lines()
        self.assertEqual(full_transaction.split('\n'), result)

    def test_transaction_arbitrary_split(self):
        transaction = """
2017-01-06 (#4) MTA
    ; Partnership: A 72.1, B
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
""".strip()
        full_transaction = """
2017-01-06 (#4) MTA
    ; Partnership: A 72.1, B
    Assets:Cash:Checking                    $ 1000.00
    Income:Salary
    [A:Assets:Cash:Checking]  $ 721.00
    [B:Assets:Cash:Checking]  $ 279.00
    [A:Income:Salary]  $ -721.00
    [B:Income:Salary]  $ -279.00
""".strip()
        x = partnership_ledger.Xact(transaction.split('\n'))
        result = x.get_all_lines()
        self.assertEqual(full_transaction.split('\n'), result)

if __name__ == '__main__':
    unittest.main()

