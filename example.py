from stock_reposting import repost

def milk_scenario():
	return [
		{
			"name": "opening",
			"kind": "receipt",
			"posting_at": "2026-01-01T09:00:00",
			"item": "Milk",
			"warehouse": "Raw Materials",
			"qty": 100,
			"rate": 50,
		},
		{
			"name": "purchase-10",
			"kind": "receipt",
			"posting_at": "2026-01-10T09:00:00",
			"item": "Milk",
			"warehouse": "Raw Materials",
			"qty": 50,
			"rate": 60,
		},
		{
			"name": "delivery-15",
			"kind": "issue",
			"posting_at": "2026-01-15T09:00:00",
			"item": "Milk",
			"warehouse": "Raw Materials",
			"qty": 80,
		},
		{
			"name": "purchase-20",
			"kind": "receipt",
			"posting_at": "2026-01-20T09:00:00",
			"item": "Milk",
			"warehouse": "Raw Materials",
			"qty": 50,
			"rate": 60,
		},
		{
			"name": "manufacture-21",
			"kind": "manufacture",
			"posting_at": "2026-01-21T09:00:00",
			"inputs": [{"item": "Milk", "warehouse": "Raw Materials", "qty": 100}],
			"output": {"item": "Milk Powder", "warehouse": "Finished Goods", "qty": 10},
		},
		{
			"name": "powder-delivery-25",
			"kind": "issue",
			"posting_at": "2026-01-25T09:00:00",
			"item": "Milk Powder",
			"warehouse": "Finished Goods",
			"qty": 10,
		},
	]


def main():
	result = repost(milk_scenario(), "purchase-10", 80)
	print("Amounts in INR. Negative movements are stock issues.")
	print("Ledger row | Old movement | New movement | Qty after | Value after")
	for name, row in result["after"].items():
		print(
			f"{name} | {result['before'][name]['stock_value_difference']:.2f} | "
			f"{row['stock_value_difference']:.2f} | {row['qty_after_transaction']} | "
			f"{row['stock_value']:.2f}"
		)

	print("\nMilk queue after manufacturing:")
	for quantity, rate in result["after"]["manufacture-21/input-1"]["stock_queue"]:
		print(f"{quantity} L at {rate:.2f} INR/L")
	print("\nChanged rows:")
	for name in result["changed_rows"]:
		print(name)


main()
