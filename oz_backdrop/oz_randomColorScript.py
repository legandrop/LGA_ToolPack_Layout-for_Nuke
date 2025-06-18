import random
n=nuke.thisNode()
r,g,b=[(float(random.randint( 20, 40)))/100,(float(random.randint( 10, 50)))/100,(float(random.randint( 15, 60)))/100]
n['tile_color'].setValue( int('%02x%02x%02x%02x' % (int(r*255),int(g*255),int(b*255),1),16) )
