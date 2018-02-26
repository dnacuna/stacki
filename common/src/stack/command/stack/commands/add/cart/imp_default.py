# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import os
import grp
import stat
import stack.file
import stack.commands
from stack.exception import ArgRequired, ArgUnique, CommandError


class Implementation(stack.commands.Implementation):
	"""
	Add a brand new cart.
	"""		
	def createFiles(self, name, path):

		# write the graph file

		graph = open(os.path.join(path, 'graph', 'cart-%s.xml' % name), 'w')
		graph.write('<graph>\n\n')
		graph.write('\t<description>\n\t%s cart\n\t</description>\n\n' % name)
		graph.write('\t<order head="backend" tail="cart-%s-backend"/>\n' % name)
		graph.write('\t<edge  from="backend"   to="cart-%s-backend"/>\n\n' % name)
		graph.write('</graph>\n')
		graph.close()

		# write the node file
		node = open(os.path.join(path, 'nodes', 'cart-%s-backend.xml' % name), 'w')
		node.write('<stack:stack>\n\n')
		node.write('\t<stack:description>\n')
		node.write('\t%s cart backend appliance extensions\n' % name)
		node.write('\t</stack:description>\n\n')
		node.write('\t<stack:package><!-- add packages here --></stack:package>\n\n')
		node.write('<stack:script stack:stage="install-post">\n')
		node.write('<!-- add shell code for post install configuration -->\n')
		node.write('</stack:script>\n\n')
		node.write('</stack:stack>\n')
		node.close()
		

	def run(self, args):
		cart = args

		for row in self.db.select("""
			* from carts where name = '%s'
			""" % cart):
			raise CommandError(self, '"%s" cart exists' % cart)

		# If the directory does not exist create it along with
		# a skeleton template.

		tree = stack.file.Tree('/export/stack/carts')
		if cart not in tree.getDirs():
			for dir in [ 'RPMS', 'nodes', 'graph' ]:
				os.makedirs(os.path.join(tree.getRoot(), cart, dir))

			cartpath = os.path.join(tree.getRoot(), cart)
			args = [ cart, cartpath ]
			self.createFiles(cart, cartpath)

		# Files were already on disk either manually created or by the
		# simple template above.
		# Add the cart to the database so we can enable it for a box

		self.db.execute("""
			insert into carts(name) values ('%s')
			""" % cart)
