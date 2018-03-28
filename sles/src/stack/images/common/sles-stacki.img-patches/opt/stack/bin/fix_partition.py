#!/opt/stack/bin/python3 -E
"""Fixes the autoyast partitioning if nukedisks=False
Replaces UUID with LABEL and applies label to relevant partition
"""
import sys
import subprocess

try:
	sys.path.append('/tmp')
	from fstab_info import partitions_to_label
except ModuleNotFoundError:
	# If the file isn't there to import then we didn't do a nukedisks=false with labels
	sys.exit(0)
except ImportError:
	# If the variable isn't there to import then we didn't do a nukedisks=false with labels
	sys.exit(0)



def label_partition(partition):
	"""Determine the filesystem type and take appropriate steps to add a label.
	Assumes the partition being input has the following keys containing data similar to below:
	['device'] = "LABEL=VARBE1"
	['new_uuid'] = "UUID=FFFFFFFFFFFFFFFFFFFF"
	['fstype'] = "ext3"
	['mountpoint'] = "/var"

	Only handles xfs and ext formats.
	The btrfs will remain with it's UUID mount reference
	"""
	return_code = 0
	label = partition['device'].split('=')[1]
	#In sles 11 it uses the /dev/disk/by-id/
	new_id = partition['new_uuid']
	#In sles 12 it uses the uuid=, we need to add the /dev/disk/by-uuid onto the string
	if 'uuid=' in  partition['new_uuid'].lower():
		new_id = partition['new_uuid'].split('=')[1]
		new_id = '/dev/disk/by-uuid/%s' % new_id
	if 'ext' in partition['fstype'].lower():
		return_code = subprocess.call(['e2label', new_id, '%s' % label])
	if 'xfs' in partition['fstype'].lower():
		# This better be unmount or we will have issues.
		# edit the partition
		return_code = subprocess.call(['xfs_admin', '-L', '%s' % label, new_id])
	return return_code


for each_partition in partitions_to_label:
	if len(each_partition) == 5:
		label_partition(each_partition)
