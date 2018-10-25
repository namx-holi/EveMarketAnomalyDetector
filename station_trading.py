
import json
import requests
from multiprocessing import Pool
import tqdm
from sys import stdout


from id_dictionaries import typeIDDictionary



trade_hubs = {
	"Jita": 60003760,
	"Amarr": 60008494,
	"Dodixie": 60011866,
	"Rens":60004588,
	"Hek": 60005686 
}

FUZZWORK_API = "https://market.fuzzwork.co.uk/aggregates/?region={}&types={}"
IDS_PER_REQUEST = 1000
PROCESS_COUNT = 8
REQUEST_RETRY_COUNT = 3
DATAPOINT_MAX = 10

# REQUEST_DEBUG = True
REQUEST_DEBUG = False
if REQUEST_DEBUG:IDS_PER_REQUEST=2


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


	def _request_prices(self, typeID_chunk, retry_count=0):
		typeIDs = ",".join([str(typeID) for typeID in typeID_chunk])
		url = FUZZWORK_API.format(self._location_id, typeIDs)
		response = requests.get(url=url)
		
		try:
			return json.loads(response.text)
		except json.JSONDecodeError:
			if retry_count > 3:
				return []
			else:
				return self._request_prices(typeID_chunk, retry_count=retry_count+1)


	def update_prices(self):
		typeID_list = self._typeID_dict.get_id_list()

		# Break the typeID_list into chunks
		typeID_chunk_list = [
			typeID_list[i * IDS_PER_REQUEST:(i + 1) * IDS_PER_REQUEST]
			for i in range(
				(len(typeID_list) + IDS_PER_REQUEST - 1) // IDS_PER_REQUEST
			)]

		if REQUEST_DEBUG:
			typeID_chunk_list=[typeID_chunk_list[i] for i in range(5)]

		# Make requests concurrently so it's faster
		pool = Pool(processes=PROCESS_COUNT)
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

		# prune items with 0 market volume
		pruned_items = {}
		for typeID in items.keys():
			buy  = items[typeID]["buy"]
			sell = items[typeID]["sell"]
			if (buy["volume"] != 0 or sell["volume"] != 0):
				pruned_items[typeID] = items[typeID]

		print("Collected valid price data for {} items".format(len(pruned_items)))
		self._items = pruned_items


	def load_datapoints(self, datapoint_file):
		print("Loading datapoints...", end="")
		with open(datapoint_file, "r") as stream:
			self._datapoints = json.load(stream)
		print("\rLoaded datapoints    ")


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
				while len(self._datapoints[typeID]) >= DATAPOINT_MAX:
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


	def calculate_volatility(self):
		pass
		# for typeID in tqdm.tqdm(self._items):


LOAD_DATAPOINTS = True
LOAD_ITEMS_FROM_DATAPOINTS = False


if __name__ == "__main__":
	# Initialise dictionaries
	typeID_dict = typeIDDictionary("data/typeIDs.json")

	# create the margin market
	hub = "Jita"
	hub_id = trade_hubs[hub]
	market = StationMarket(typeID_dict, hub_id, hub)

	# Load in datapoints if need be
	datapoint_file = "saves/datapoints1.save"
	if LOAD_DATAPOINTS or LOAD_ITEMS_FROM_DATAPOINTS:
		market.load_datapoints(datapoint_file)

	if LOAD_ITEMS_FROM_DATAPOINTS:
		market.populate_items_from_datapoints()
	else:
		market.update_prices()

	# Add our current data to datapoints and save
	market.add_current_to_datapoint()
	market.save_datapoints(datapoint_file)
