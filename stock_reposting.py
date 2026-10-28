from collections import deque
from copy import deepcopy
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def repost(transactions, receipt_name, new_rate):
	"""Recalculate stock without changing the original transactions."""
	corrected = deepcopy(transactions)
	receipt = next((row for row in corrected if row["name"] == receipt_name), None)
	if receipt is None or receipt["kind"] != "receipt":
		raise ValueError("The correction must reference an existing receipt")

	receipt["rate"] = to_decimal(new_rate)
	if receipt["rate"] < 0:
		raise ValueError("Incoming rate cannot be negative")

	before = replay(transactions)
	after = replay(corrected)
	return {
		"transactions": corrected,
		"before": before,
		"after": after,
		"changed_rows": [name for name in after if before[name] != after[name]],
	}


def replay(transactions):
	"""Rebuild the ledger using fixed YYYY-MM-DDTHH:MM:SS posting dates."""
	queues = {}
	rows = {}
	names = set()

	for transaction in sorted(
		transactions, key=lambda row: (row["posting_at"], row.get("sequence", 0), row["name"])
	):
		name = transaction["name"]
		if not name or name in names:
			raise ValueError("Transaction names must be nonempty and unique")
		names.add(name)

		if transaction["kind"] == "receipt":
			rate = to_decimal(transaction["rate"])
			if rate < 0:
				raise ValueError("Incoming rate cannot be negative")
			value = to_decimal(transaction["qty"]) * rate
			post_movement(queues, rows, transaction, transaction, "receipt", value)
		elif transaction["kind"] == "issue":
			post_movement(queues, rows, transaction, transaction, "issue")
		elif transaction["kind"] == "manufacture":
			if not transaction["inputs"]:
				raise ValueError("Manufacturing requires at least one input")
			cost = to_decimal(transaction.get("additional_cost", 0))
			if cost < 0:
				raise ValueError("Additional cost cannot be negative")
			for index, item in enumerate(transaction["inputs"], start=1):
				row = post_movement(queues, rows, transaction, item, f"input-{index}")
				cost -= row["stock_value_difference"]
			post_movement(queues, rows, transaction, transaction["output"], "output", cost)
		else:
			raise ValueError(f"Unsupported transaction kind: {transaction['kind']}")

	return rows


class FIFOQueue:
	"""Store receipt layers as [remaining quantity, remaining value]."""

	def __init__(self):
		self.layers = deque()

	def receive(self, quantity, value):
		quantity = to_decimal(quantity)
		value = to_decimal(value)
		if quantity <= 0 or value < 0:
			raise ValueError("Receipt quantity must be positive and value nonnegative")
		self.layers.append([quantity, value.quantize(CENT, rounding=ROUND_HALF_UP)])

	def issue(self, quantity):
		quantity = to_decimal(quantity)
		if quantity <= 0:
			raise ValueError("Issue quantity must be positive")
		if quantity > self.quantity():
			raise ValueError("Insufficient stock; negative stock is not supported")

		cost = Decimal(0)
		while quantity:
			layer_quantity, layer_value = self.layers[0]
			consumed_qty = min(quantity, layer_quantity)
			if consumed_qty == layer_quantity:
				value = layer_value
				self.layers.popleft()
			else:
				value = (layer_value * consumed_qty / layer_quantity).quantize(CENT, rounding=ROUND_HALF_UP)
				# Keep any rounding remainder in the remaining stock.
				self.layers[0] = [layer_quantity - consumed_qty, layer_value - value]
			cost += value
			quantity -= consumed_qty
		return cost

	def quantity(self):
		return sum((quantity for quantity, value in self.layers), Decimal(0))

	def value(self):
		return sum((value for quantity, value in self.layers), Decimal(0))

	def snapshot(self):
		return [[quantity, value / quantity] for quantity, value in self.layers]


def post_movement(queues, rows, transaction, item, leg, incoming_value=None):
	key = (item["item"], item["warehouse"])
	if not all(key):
		raise ValueError("Item and warehouse are required")
	if key not in queues:
		queues[key] = FIFOQueue()
	queue = queues[key]
	previous_value = queue.value()
	quantity = to_decimal(item["qty"])

	if incoming_value is None:
		queue.issue(quantity)
		quantity = -quantity
	else:
		queue.receive(quantity, incoming_value)

	stock_qty = queue.quantity()
	stock_value = queue.value()
	name = f"{transaction['name']}/{leg}"
	rows[name] = {
		"voucher": transaction["name"],
		"posting_at": transaction["posting_at"],
		"item": item["item"],
		"warehouse": item["warehouse"],
		"actual_qty": quantity,
		"stock_value_difference": stock_value - previous_value,
		"qty_after_transaction": stock_qty,
		"stock_value": stock_value,
		"valuation_rate": stock_value / stock_qty if stock_qty else None,
		"stock_queue": queue.snapshot(),
	}
	return rows[name]


def to_decimal(value):
	value = Decimal(str(value))
	if not value.is_finite():
		raise ValueError("Quantity and cost must be finite numbers")
	return value
