import unittest

from example import milk_scenario
from stock_reposting import replay, repost


class TestStockReposting(unittest.TestCase):
	def test_before_reposting(self):
		rows = replay(milk_scenario())
		self.assertEqual(rows["opening/receipt"]["stock_value"], 5000)
		self.assertEqual(rows["purchase-10/receipt"]["stock_value_difference"], 3000)
		self.assertEqual(rows["delivery-15/issue"]["stock_value_difference"], -4000)
		self.assertEqual(rows["delivery-15/issue"]["stock_value"], 4000)
		self.assertEqual(rows["purchase-20/receipt"]["stock_value"], 7000)
		self.assertEqual(rows["manufacture-21/input-1"]["stock_value_difference"], -5800)
		self.assertEqual(rows["manufacture-21/input-1"]["stock_value"], 1200)
		self.assertEqual(rows["manufacture-21/input-1"]["stock_queue"], [[20, 60]])
		self.assertEqual(rows["manufacture-21/output"]["stock_value_difference"], 5800)
		self.assertEqual(rows["manufacture-21/output"]["valuation_rate"], 580)
		self.assertEqual(rows["powder-delivery-25/issue"]["stock_value_difference"], -5800)
		self.assertEqual(rows["powder-delivery-25/issue"]["qty_after_transaction"], 0)
		self.assertEqual(rows["powder-delivery-25/issue"]["stock_value"], 0)

	def test_successful_reposting(self):
		transactions = milk_scenario()
		result = repost(transactions, "purchase-10", 80)
		rows = result["after"]
		self.assertEqual(rows["opening/receipt"], result["before"]["opening/receipt"])
		self.assertEqual(rows["purchase-10/receipt"]["stock_value_difference"], 4000)
		self.assertEqual(rows["delivery-15/issue"]["stock_value_difference"], -4000)
		self.assertEqual(rows["delivery-15/issue"]["stock_value"], 5000)
		self.assertEqual(rows["delivery-15/issue"]["stock_queue"], [[20, 50], [50, 80]])
		self.assertEqual(rows["purchase-20/receipt"]["stock_value_difference"], 3000)
		self.assertEqual(rows["purchase-20/receipt"]["stock_value"], 8000)
		self.assertEqual(rows["manufacture-21/input-1"]["stock_value_difference"], -6800)
		self.assertEqual(rows["manufacture-21/input-1"]["stock_value"], 1200)
		self.assertEqual(rows["manufacture-21/input-1"]["stock_queue"], [[20, 60]])
		self.assertEqual(rows["manufacture-21/output"]["stock_value_difference"], 6800)
		self.assertEqual(rows["manufacture-21/output"]["valuation_rate"], 680)
		self.assertEqual(rows["powder-delivery-25/issue"]["stock_value_difference"], -6800)
		self.assertEqual(rows["powder-delivery-25/issue"]["qty_after_transaction"], 0)
		self.assertEqual(rows["powder-delivery-25/issue"]["stock_value"], 0)
		self.assertEqual(transactions, milk_scenario())
		self.assertEqual(
			result["changed_rows"],
			[
				"purchase-10/receipt",
				"delivery-15/issue",
				"purchase-20/receipt",
				"manufacture-21/input-1",
				"manufacture-21/output",
				"powder-delivery-25/issue",
			],
		)


if __name__ == "__main__":
	unittest.main()
