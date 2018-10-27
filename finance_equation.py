

def calculate_weighting(item, brokers_fee=0.028, sales_tax=0.02):
	buy_price = item["buy"]["max"] * (1+brokers_fee)
	sell_price = item["sell"]["min"] * (1-brokers_fee) * (1-sales_tax)

	buy_price_median = item["buy"]["median"] * (1+brokers_fee)
	sell_price_median = item["sell"]["median"] * (1-brokers_fee) * (1-sales_tax)

	best_case_ratio = sell_price / buy_price
	median_ratio = sell_price_median / buy_price_median

	# Get rid of absurd things
	if item["sell"]["volume"] < 50:
		return 0
	if item["buy"]["orderCount"] < 5:
		return 0
	if item["sell"]["orderCount"] < 5:
		return 0

	# how saturated the market is with people selling already
	sell_volume_saturation = item["sell"]["volume"] / (
		item["buy"]["volume"] + item["sell"]["volume"])

	sell_order_saturation = item["sell"]["orderCount"] / (
		item["buy"]["orderCount"] + item["sell"]["orderCount"])

	return best_case_ratio