
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


	def compare_market(market):
		items_1 = this._items
		items_2 = market.get_items()



class typeIDDictionary:
	def __init__(self, typeid_filepath):
		print("Loading in typeIDs")
		with open(typeid_filepath, "r") as stream:
			self._data = json.load(stream)

	def id2name(self, typeID):
		try:
			return self._data[int(typeID)]["name"]
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



class solarsystemIDDictionary:
	def __init__(self, systemid_filepath):
		print("Loading in solarsystemIDs")
		with open(systemid_filepath, "r") as stream:
			self._data = json.load(stream)

	def id2name(self, solarsystemID):
		try:
			return self._data[int(solarsystemID)]
		except KeyError:
			return ""

	def name2id(self, name):
		for solarsystemID in self._data.keys():
			if self._data[solarsystemID].lower() == name.lower():
				return int(solarsystemID)
		return -1



if __name__ == "__main__":
	# Initialise dictionaries
	typeid_dict = typeIDDictionary("data/typeIDs.json")
	solarsystemid_dict = solarsystemIDDictionary("data/solarsystemIDs.json")

	# Create markets
	sys1_name   = "Jita"
	sys2_name   = "Amarr"
	sys1_id     = solarsystemid_dict.name2id(sys1_name)
	sys2_id     = solarsystemid_dict.name2id(sys2_name)
	sys1_market = Market(sys1_id)
	sys2_market = Market(sys2_id)

	# Update the market prices
	sys1_market.update_item_prices()
	sys2_market.update_item_prices()

	# Get a type_id of an item
	item_name = "Plagioclase"
	type_id = typeid_dict.name2id(item_name)

	sys1_price = sys1_market.get_prices_for_typeID(type_id)
	sys2_price = sys2_market.get_prices_for_typeID(type_id)
	print(sys1_price)
	print(sys2_price)
