

class main_config:
	MARKET_PRICE_API = "https://api.eve-marketdata.com/api/item_prices2.xml?char_name={}&solarsystem_ids={}&buysell={}"
	ANOMALY_FACTOR = 0.2 # Percent diff
	SHORTEN_PRICES = False



class station_trading_config:
	FUZZWORK_API = "https://market.fuzzwork.co.uk/aggregates/?region={}&types={}"
	IDS_PER_REQUEST = 1000
	PROCESS_COUNT = 8
	REQUEST_RETRY_COUNT = 3
	DATAPOINT_MAX = 10

	LOAD_DATAPOINTS = False
	LOAD_ITEMS_FROM_DATAPOINTS = False
