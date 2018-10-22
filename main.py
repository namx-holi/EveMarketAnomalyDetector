
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


MARKET_PRICE_API = "https://api.eve-marketdata.com/api/item_prices2.xml?char_name={}&solarsystem_ids={}&buysell={}"
ANOMALY_FACTOR = 0.2 # Percent diff
SHORTEN_PRICES = False

class Market:

	def __init__(self, solarsystem_id):
		self._solarsystem_id = solarsystem_id
		self._items = {}


	def get_items(self):
		return self._items


	def get_id(self):
		return self._solarsystem_id


	def _request_prices(self, buysell):
		"""returns a dictionary of all pricess for buy or sell

		buysell        : either "s" or "b". prices of buy or sell avg
		"""

		print("Making {} request for solar system {}".format(buysell, self._solarsystem_id))
		char_name = "none"
		url = MARKET_PRICE_API.format(char_name, self._solarsystem_id, buysell)
		headers = {'accept': 'application/xml;q=0.9, */*;q=0.8'}
		response = requests.get(url=url, headers=headers)

		# turn into a dict and return the prices
		rows = self._parse_xml(response.text)
		return rows


	def _request_buy_prices(self):
		"""wrapper of request_prices for buy prices
		"""

		return self._request_prices("b")


	def _request_sell_prices(self):
		"""wrapper of request_prices for sell prices
		"""

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
				if item2["buy"] / item1["sell"] - 1 >= ANOMALY_FACTOR:
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
				if item1["buy"] / item2["sell"] - 1 >= ANOMALY_FACTOR:
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

			if SHORTEN_PRICES:
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

			if SHORTEN_PRICES:
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

			if SHORTEN_PRICES:
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
				" or {0:.2f} / m^3".format(profit / item_vol))

			anomaly_lines.append((profit/item_vol, [item_text, buy_text, sell_text, profit_text]))

		# Sort the lines so that higher profit/vol are at the bottom
		anomaly_lines.sort(key=lambda x: x[0], reverse=False)

		# Remove the profit/vol part of the lines and return just the display text
		anomaly_lines = [anom[1] for anom in anomaly_lines]

		return anomaly_lines









class typeIDDictionary:
	def __init__(self, typeid_filepath):
		print("Loading in typeIDs")
		with open(typeid_filepath, "r") as stream:
			self._data = json.load(stream)

	def id2name(self, typeID):
		try:
			return self._data[str(typeID)]["name"]
		except KeyError:
			return ""
		except ValueError:
			return ""

	def name2id(self, name):
		for typeID in self._data.keys():
			try:
				if self._data[typeID]["name"].lower() == name.lower():
					return int(typeID)
			except KeyError:
				continue
		return -1

	def id2vol(self, typeID):
		try:
			return self._data[str(typeID)]["volume"]
		except KeyError:
			return 1.0
		except ValueError:
			return 1.0

	def name2vol(self, name):
		name = self.name2id(name)
		return id2vol(name)



class solarsystemIDDictionary:
	def __init__(self, systemid_filepath):
		print("Loading in solarsystemIDs")
		with open(systemid_filepath, "r") as stream:
			self._data = json.load(stream)

	def id2name(self, solarsystemID):
		try:
			return self._data[str(solarsystemID)]
		except KeyError:
			return ""

	def name2id(self, name):
		for solarsystemID in self._data.keys():
			if self._data[solarsystemID].lower() == name.lower():
				return int(solarsystemID)
		return -1



if __name__ == "__main__":
	# Initialise dictionaries
	typeID_dict = typeIDDictionary("data/typeIDs.json")
	solarsystemID_dict = solarsystemIDDictionary("data/solarsystemIDs.json")

	# Initialise anomaly parser
	anomaly_parser = AnomalyParser(typeID_dict, solarsystemID_dict)

	# Create markets
	sys1_name   = "Jita"
	sys2_name   = "Amarr"
	sys1_id     = solarsystemID_dict.name2id(sys1_name)
	sys2_id     = solarsystemID_dict.name2id(sys2_name)
	sys1_market = Market(sys1_id)
	sys2_market = Market(sys2_id)

	# Update the market prices
	sys1_market.update_item_prices()
	sys2_market.update_item_prices()

	# # Get a type_id of an item
	# item_name = "Plagioclase"
	# type_id = typeID_dict.name2id(item_name)

	# sys1_price = sys1_market.get_prices_for_typeID(type_id)
	# sys2_price = sys2_market.get_prices_for_typeID(type_id)
	# print(sys1_price)
	# print(sys2_price)

	# Find anomalies
	anomalies = sys1_market.find_anomalies(sys2_market)
	results = anomaly_parser.parse(anomalies)

	for result in results:
		print("\n".join(result))
		print()