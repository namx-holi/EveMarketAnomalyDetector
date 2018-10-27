
import json
import requests
from multiprocessing import Pool
import tqdm
from sys import stdout

from id_dictionaries import typeIDDictionary
from config import station_trading_config as cfg
from finance_equation import calculate_weighting


trade_hubs = {
	"Jita": 60003760,
	"Amarr": 60008494,
	"Dodixie": 60011866,
	"Rens":60004588,
	"Hek": 60005686 
}

# REQUEST_DEBUG = True
REQUEST_DEBUG = False
if REQUEST_DEBUG:cfg.IDS_PER_REQUEST=2


def printf(*args):
	stdout.write(" ".join(map(str, args)))
	stdout.flush()



class StationMarket:

	def __init__(self, typeID_dict, location_id, name=""):
		self._typeID_dict = typeID_dict
		self._location_id = location_id
		self._name = name if name else str(location_id)
		self._items = {}
		self._datapoints = {}

	def get_items(self): return self._items
	def get_id(self):    return self._location_id
	def get_name(self):  return self._name

	@staticmethod
	def _parse_items(items):
		# This is horrible
		for t in items.keys(): # t = typeID
			for bs in items[t]: # bs = buy or sell
				for v in items[t][bs].keys(): # v = value
					items[t][bs][v] = float(items[t][bs][v])

		return items


	def _request_prices(self, typeID_chunk, retry_count=0):
		typeIDs = ",".join([str(typeID) for typeID in typeID_chunk])
		url = cfg.FUZZWORK_API.format(self._location_id, typeIDs)
		response = requests.get(url=url)
		
		try:
			return json.loads(response.text)

		except json.JSONDecodeError:
			if retry_count > cfg.REQUEST_RETRY_COUNT:
				return []
			else:
				return self._request_prices(typeID_chunk, retry_count=retry_count+1)


	def update_prices(self):
		typeID_list = self._typeID_dict.get_id_list()

		# Break the typeID_list into chunks
		typeID_chunk_list = [
			typeID_list[i * cfg.IDS_PER_REQUEST:(i + 1) * cfg.IDS_PER_REQUEST]
			for i in range(
				(len(typeID_list) + cfg.IDS_PER_REQUEST - 1) // cfg.IDS_PER_REQUEST
			)]

		if REQUEST_DEBUG:
			typeID_chunk_list=[typeID_chunk_list[i] for i in range(5)]

		# Make requests concurrently so it's faster
		pool = Pool(processes=cfg.PROCESS_COUNT)
		results = [
			x for x in tqdm.tqdm(
				pool.imap_unordered(self._request_prices, typeID_chunk_list),
				total=len(typeID_chunk_list),
				unit="requests",
				desc="Collecting prices"
			)]
		pool.close()

		# amalgamate data
		items = {}
		for result in results:
			items.update(result)

		# Make sure all the prices are floats
		self._parse_items(items)

		# prune items with 0 market volume
		filtered_items = {}
		for typeID in items.keys():
			buy  = items[typeID]["buy"]
			sell = items[typeID]["sell"]
			if (
				(buy["volume"] != 0 or sell["volume"] != 0) and
				(buy["max"] != 0 and sell["min"] != 0)
			):
				filtered_items[typeID] = items[typeID]

		print("Collected valid price data for {} items".format(len(filtered_items)))
		self._items = filtered_items


	def load_datapoints(self, datapoint_file):
		print("Loading datapoints...", end="")
		with open(datapoint_file, "r") as stream:
			try:
				self._datapoints = json.load(stream)
			except json.decoder.JSONDecodeError:
				self._datapoints = {}
				print("\rFailed to load datapoints")
				return False

		print("\rLoaded datapoints    ")
		return True


	def save_datapoints(self, datapoint_file):
		printf("Saving datapoints...")
		with open(datapoint_file, "w") as stream:
			json.dump(self._datapoints, stream, indent=4, sort_keys=True)
		printf("\rSaved datapoints    \n")


	def add_current_to_datapoint(self):
		printf("Adding current datapoint to datapoints...")
		for typeID in self._items:

			# If the typeID already exists
			if typeID in self._datapoints.keys():

				# Make sure the datapoint count is less than the max
				# we loop it in case the datapoint count has changed
				while len(self._datapoints[typeID]) >= cfg.DATAPOINT_MAX:
					del self._datapoints[typeID][0]
				
				# Append the new one
				self._datapoints[typeID].append(self._items[typeID])

			# If it doesn't exist, just create it
			else:
				self._datapoints[typeID] = [self._items[typeID]]
		printf("\rCurrent datapoint added to datapoints    \n")


	def populate_items_from_datapoints(self):
		items = {}
		for typeID in self._datapoints.keys():
			items[typeID] = self._datapoints[typeID][-1]
		self._items = items


	def find_large_margins(self, brokers_fee=0.028, sales_tax=0.02):
		item_list = []

		for typeID in self._items:
			item_copy = self._items[typeID].copy()
			item_copy.update(dict(typeID=typeID))
			item_list.append(item_copy)

		item_list.sort(key=lambda item: calculate_weighting(
			item, brokers_fee, sales_tax),
			reverse=True)

		return item_list


def display_item(typeID_dict, item):
	print("Item name: {}".format(typeID_dict.id2name(item["typeID"])))
	print("  Buy for {0:,.2f} ISK".format(item["buy"]["max"]))
	print("  Sell for {0:,.2f} ISK".format(item["sell"]["min"]))
	print()
	print("  Buy volume is {0:,.0f}".format(item["buy"]["volume"]))
	print("  Buy order count is {0:,.0f}".format(item["buy"]["orderCount"]))
	print("  Sell volume is {0:,.0f}".format(item["sell"]["volume"]))
	print("  Sell order count is {0:,.0f}".format(item["sell"]["orderCount"]))
	print()


if __name__ == "__main__":
	# Initialise dictionaries
	typeID_dict = typeIDDictionary("data/typeIDs.json")

	# create the margin market
	hub = "Amarr"
	hub_id = trade_hubs[hub]
	market = StationMarket(typeID_dict, hub_id, hub)

	# Load in datapoints if need be
	datapoint_file = "saves/datapoints1.save"
	if cfg.LOAD_DATAPOINTS or cfg.LOAD_ITEMS_FROM_DATAPOINTS:
		if market.load_datapoints(datapoint_file):
			if cfg.LOAD_ITEMS_FROM_DATAPOINTS:
				market.populate_items_from_datapoints()
		else:
			market.update_prices()
	else:
		market.update_prices()

	# Find good things
	good_things = market.find_large_margins(
		brokers_fee=0.028,
		sales_tax=0.02)

	# print top good thing
	display_item(typeID_dict, good_things[0])


	# Add our current data to datapoints and save
	market.add_current_to_datapoint()
	market.save_datapoints(datapoint_file)
