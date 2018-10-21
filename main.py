


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


API_FORMAT = "https://api.eve-marketdata.com/api/item_prices2.xml?char_name={}&solarsystem_ids={}&buysell={}"


class Market:

	def __init__(self, solarsystem_id):
		self._solarsystem_id = solarsystem_id
		self._items = {}


	def get_items(self):
		return self._items


	def _request_prices(self, buysell):
		"""returns a dictionary of all pricess for buy or sell

		buysell        : either "s" or "b". prices of buy or sell avg
		"""

		print("Making {} request for solar system {}".format(buysell, self._solarsystem_id))
		char_name = "none"
		url = API_FORMAT.format(char_name, self._solarsystem_id, buysell)
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





if __name__ == "__main__":
	solarsystem_id = 30002187 # jita
	jita_market = Market(solarsystem_id)

	jita_market.update_item_prices()

	prices = jita_market.get_prices_for_typeID(34169)
	print(prices)

	# prices = get_buy_prices(solarsystem_id)
	# print(prices[0])