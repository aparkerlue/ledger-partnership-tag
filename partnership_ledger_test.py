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

if __name__ == '__main__':
    unittest.main()

