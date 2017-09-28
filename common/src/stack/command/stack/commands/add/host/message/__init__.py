# @SI_Copyright@
#			       stacki.com
#				  v4.0
# 
#      Copyright (c) 2006 - 2017 StackIQ Inc. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	 "This product includes software developed by StackIQ" 
#  
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY STACKIQ AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL STACKIQ OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @SI_Copyright@

import socket
import stack.mq
import stack.commands.add.host


class Command(stack.commands.add.host.command):
	"""
	Adds a message to one or most host Message Queues

	<arg type='string' name='host' repeat='1'>
	Zero, one or more host names. If no host names are supplied, the
	message is sent to all hosts.
	</arg>

	<param type='string' name='message' optional='0'>
	Message text
	</param>

	<param type='string' name='channel'>
	Name of the channel
	</param>

	<example cmd='add host message backend-0-0 "hello world" channel=debug'>
	Sends "hello world" over the debug channel using the Message
	Queue on backend-0-0.
	</example>
	
	"""

	def run(self, params, args):

		(channel, message) = self.fillParams([
			('channel', 'debug', False),
			('message', None, True)
			])

		for host in self.getHostnames(args):
			tx  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			msg = stack.mq.Message(channel, message)
			
			if host == self.db.getHostname('localhost'):
				host = 'localhost'

			tx.sendto(msg.dumps(), (host, stack.mq.ports.publish))
			tx.close()
