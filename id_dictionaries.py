
import json



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

	def get_id_list(self):
		return list(self._data.keys())



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

	def get_id_list(self):
		return list(self._data.keys())
