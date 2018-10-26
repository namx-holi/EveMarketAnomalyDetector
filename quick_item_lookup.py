
from id_dictionaries import typeIDDictionary

# Initialise dictionary
typeID_dict = typeIDDictionary("data/typeIDs.json")

while True:
	try:
		name = input("Item Name> ")
	except KeyboardInterrupt:
		print()
		break

	matches = typeID_dict.name2closematchid(name)
	matches.sort(key=lambda x: int(x))

	if len(matches):
		for match in matches:
			print("{:>5} : {}".format(match, typeID_dict.id2name(match)))
	else:
		print("No matches")
	print()
