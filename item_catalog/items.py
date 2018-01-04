from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Item, Base

engine = create_engine('sqlite:///itemscatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Items for the catalog
# First Item
item1 = Item(name="Black Beard's dagger", description="The famous pirate used to use this relict in his adventures", price="$4000")

session.add(item1)
session.commit()

# Second Item
item1 = Item(name="Elves light", description="This bottle is filled with elves light, which will be brigth and does not require charge", price="$5000")

session.add(item1)
session.commit()

# Third Item
item1 = Item(name="Bewitched Talisman", description="This will bring you luck over everyone else", price="$3500")

session.add(item1)
session.commit()

# Forth Item
item1 = Item(name="Water of youth", description="Doesn't require much of a description. This water will bring back about 10-20 years of your life back", price="$500,000")

session.add(item1)
session.commit()

print "added menu items!"
