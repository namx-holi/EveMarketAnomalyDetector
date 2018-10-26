
"""
enter a location

look up location id

use some api like

https://api.eve-marketdata.com/api/item_prices2.xml?
char_name=Oriella%20Trikassi&
solarsystem_ids=30002187&
buysell=b

to get prices at location

store this in a file somewhere
(maybe keep last 30 or so)

find anomalies

look up typeids and display
"""


import requests
import xmltodict
import json

from id_dictionaries import typeIDDictionary, solarsystemIDDictionary



# cfg.MARKET_PRICE_API = "https://api.eve-marketdata.com/api/item_prices2.xml?char_name={}&solarsystem_ids={}&buysell={}"
# cfg.ANOMALY_FACTOR = 0.2 # Percent diff
# cfg.SHORTEN_PRICES = False



class Market:

	def __init__(self, solarsystem_id, name=""):
		self._solarsystem_id = solarsystem_id
		self._name = name if name else str(solarsystem_id)
		self._items = {}


	def get_items(self):
		return self._items


	def get_id(self):
		return self._solarsystem_id


	def get_name(self):
		return self._name


	def _request_prices(self, buysell):
		"""returns a dictionary of all pricess for buy or sell

		buysell        : either "s" or "b". prices of buy or sell avg
		"""

		char_name = "none"
		url = cfg.MARKET_PRICE_API.format(char_name, self._solarsystem_id, buysell)
		headers = {'accept': 'application/xml;q=0.9, */*;q=0.8'}
		response = requests.get(url=url, headers=headers)

		# turn into a dict and return the prices
		rows = self._parse_xml(response.text)
		return rows


	def _request_buy_prices(self):
		"""wrapper of request_prices for buy prices
		"""

		print("Collecting buy orders for {}".format(self._name))
		return self._request_prices("b")


	def _request_sell_prices(self):
		"""wrapper of request_prices for sell prices
		"""

		print("Collecting sell orders for {}".format(self._name))
		return self._request_prices("s")

	@staticmethod
	def _parse_xml(xml):
		"""helps parse all xml responses
		"""

		xml_as_dict = xmltodict.parse(xml)
		rows = xml_as_dict['emd']['result']['rowset']['row']
		return rows


	def update_item_prices(self):
		buy_prices = self._request_buy_prices()
		for row in buy_prices:
			typeID = int(row['@typeID'])
			price = float(row['@price'])
			updated = row['@updated']

			if price == 0:
				continue

			if typeID not in self._items.keys():
				self._items[typeID] = dict(
					buy=price,
					sell=None,
					updated=updated)
			else:
				self._items[typeID]['buy'] = price
				self._items[typeID]['updated'] = updated

		sell_prices = self._request_sell_prices()
		for row in sell_prices:
			typeID = int(row['@typeID'])
			price = float(row['@price'])
			updated = row['@updated']

			if price == 0:
				continue

			if typeID not in self._items.keys():
				self._items[typeID] = dict(
					buy=None,
					sell=price,
					updated=updated)
			else:
				self._items[typeID]['sell'] = price
				self._items[typeID]['updated'] = updated


	def get_prices_for_typeID(self, typeID):
		if typeID in self._items.keys():
			return self._items[typeID]
		else:
			return {}


	def find_anomalies(self, market):
		items_1 = self._items
		items_2 = market.get_items()

		# Find items that can match up to compare
		matched_items = []
		for item_key in items_1:
			if item_key in items_2.keys():
				matched_items.append((item_key, items_1[item_key], items_2[item_key]))

		# Anomalies for between this and the other market and the other market and this
		anomalies = []
		# anomalies = dict(import_items=[], export_items=[], export_to=market.get_id())
		for typeID, item1, item2 in matched_items:
			anomaly = {}

			if item2["buy"] is not None and item1["sell"] is not None:
				if item2["buy"] / item1["sell"] - 1 >= cfg.ANOMALY_FACTOR:
					anomaly = dict(typeID=typeID)

					# Inverted buy/sell than the top condition because
					# this is what we'll be buying and selling rather
					# than what the market is buying/selling
					anomaly["buy_system"]  = self._solarsystem_id
					anomaly["buy_price"]   = item1["sell"]

					anomaly["sell_system"] = market.get_id()
					anomaly["sell_price"]  = item2["buy"]

					anomalies.append(anomaly)

			if item1["buy"] is not None and item2["sell"] is not None:
				if item1["buy"] / item2["sell"] - 1 >= cfg.ANOMALY_FACTOR:
					anomaly = dict(typeID=typeID)

					# Inverted buy/sell than the top condition because
					# this is what we'll be buying and selling rather
					# than what the market is buying/selling
					anomaly["buy_system"]  = market.get_id()
					anomaly["buy_price"]   = item2["sell"]

					anomaly["sell_system"] = self._solarsystem_id
					anomaly["sell_price"]  = item1["buy"]

					anomalies.append(anomaly)


		return anomalies



class AnomalyParser:
	def __init__(self, typeID_dict, solarsystemID_dict):
		self._typeID_dict = typeID_dict
		self._solarsystemID_dict = solarsystemID_dict

	def parse(self, anomaly_list):
		anomaly_lines = []
		for anomaly in anomaly_list:
			buy_system_name  = self._solarsystemID_dict.id2name(anomaly["buy_system"])
			sell_system_name = self._solarsystemID_dict.id2name(anomaly["sell_system"])
			buy_price        = anomaly["buy_price"]
			sell_price       = anomaly["sell_price"]
			profit           = sell_price - buy_price

			item_vol         = self._typeID_dict.id2vol(anomaly["typeID"])
			profit_fraction  = (sell_price / buy_price) - 1

			if cfg.SHORTEN_PRICES:
				if buy_price/1e12 > 1:
					buy_price_formatted = "{0:.2f}T ISK".format(buy_price/1e12)
				elif buy_price/1e9 > 1:
					buy_price_formatted = "{0:.2f}B ISK".format(buy_price/1e9)
				elif buy_price/1e6 > 1:
					buy_price_formatted = "{0:.2f}M ISK".format(buy_price/1e6)
				elif buy_price/1e3 > 1:
					buy_price_formatted = "{0:.2f}K ISK".format(buy_price/1e3)
				else:
					buy_price_formatted = "{0:.2f} ISK".format(buy_price)
			else:
				buy_price_formatted = "{0:,.2f} ISK".format(buy_price)

			if cfg.SHORTEN_PRICES:
				if sell_price/1e12 > 1:
					sell_price_formatted = "{0:.2f}T ISK".format(sell_price/1e12)
				elif sell_price/1e9 > 1:
					sell_price_formatted = "{0:.2f}B ISK".format(sell_price/1e9)
				elif sell_price/1e6 > 1:
					sell_price_formatted = "{0:.2f}M ISK".format(sell_price/1e6)
				elif sell_price/1e3 > 1:
					sell_price_formatted = "{0:.2f}K ISK".format(sell_price/1e3)
				else:
					sell_price_formatted = "{0:.2f} ISK".format(sell_price)
			else:
				sell_price_formatted = "{0:,.2f} ISK".format(sell_price)

			if cfg.SHORTEN_PRICES:
				if profit/1e12 > 1:
					profit_formatted = "{0:.2f}T ISK".format(profit/1e12)
				elif profit/1e9 > 1:
					profit_formatted = "{0:.2f}B ISK".format(profit/1e9)
				elif profit/1e6 > 1:
					profit_formatted = "{0:.2f}M ISK".format(profit/1e6)
				elif profit/1e3 > 1:
					profit_formatted = "{0:.2f}K ISK".format(profit/1e3)
				else:
					profit_formatted = "{0:.2f} ISK".format(profit)
			else:
				profit_formatted = "{0:,.2f} ISK".format(profit)


			item_text = typeID_dict.id2name(anomaly["typeID"])
			buy_text  = "Buy in {} for {}".format(buy_system_name, buy_price_formatted)
			sell_text = "Sell in {} for {}".format(sell_system_name, sell_price_formatted)

			profit_text = (
				"You will make {} per item".format(profit_formatted) +
				" ({0:.2%} per item)".format(profit_fraction) +
				"\n or {0:,.2f} / m^3".format(profit / item_vol))

			anomaly_lines.append((profit/item_vol, [item_text, buy_text, sell_text, profit_text]))

		# Sort the lines so that higher profit/vol are at the bottom
		anomaly_lines.sort(key=lambda x: x[0], reverse=False)

		# Remove the profit/vol part of the lines and return just the display text
		anomaly_lines = [anom[1] for anom in anomaly_lines]

		return anomaly_lines



if __name__ == "__main__":
	# Initialise dictionaries
	typeID_dict = typeIDDictionary("data/typeIDs.json")
	solarsystemID_dict = solarsystemIDDictionary("data/solarsystemIDs.json")

	# Initialise anomaly parser
	anomaly_parser = AnomalyParser(typeID_dict, solarsystemID_dict)

	print("")
	print("Major trade hubs: Jita, Amarr, Rens, Dodixie, Hek")
	print("Secondary trade hubs: Oursulaert, Tash-Murkon Prime, Agil")

	sys1_id = -1
	while sys1_id == -1:
		sys1_name = input("Input first  system: ")
		sys1_id = solarsystemID_dict.name2id(sys1_name)

	sys2_id = -1
	while sys2_id == -1 or sys1_id == sys2_id:
		sys2_name = input("Input second system: ")
		sys2_id = solarsystemID_dict.name2id(sys2_name)

	print("")

	# Create markets
	sys1_market = Market(sys1_id, name=sys1_name.title())
	sys2_market = Market(sys2_id, name=sys2_name.title())

	# Update the market prices
	sys1_market.update_item_prices()
	sys2_market.update_item_prices()

	# Find anomalies
	anomalies = sys1_market.find_anomalies(sys2_market)
	results = anomaly_parser.parse(anomalies)

	print("")
	for result in results:
		print("\n".join(result))
		print()
