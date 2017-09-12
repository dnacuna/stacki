# @SI_Copyright@
# Copyright (c) 2006 - 2017 StackIQ Inc.
# All rights reserved. stacki(r) v4.0 stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @SI_Copyright@
#
# @Copyright@
# Copyright (c) 2000 - 2010 The Regents of the University of California
# All rights reserved. Rocks(r) v5.4 www.rocksclusters.org
# https://github.com/Teradata/stacki/blob/master/LICENSE-ROCKS.txt
# @Copyright@


import stack.commands

class Command(stack.commands.remove.command):
	"""
	Remove a global static route.

	<param type='string' name='address' optional='0'>
	The address of the static route to remove.
	</param>

	<example cmd='remove route address=1.2.3.4'>
	Remove the global static route that has the network address '1.2.3.4'.
	</example>
	"""


	def run(self, params, args):

		(address, ) = self.fillParams([ ('address', None, True) ])

		self.db.execute("""delete from global_routes where 
			network = '%s'""" % address)
