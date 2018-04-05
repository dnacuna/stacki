#!/opt/stack/bin/python3 -E
#
# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
"""
Gathers data for use in fix_partitions.py
"""
import sys
import os
try:
	sys.path.append('/tmp')
	from fstab_info import old_fstab
except ModuleNotFoundError:
	# If the file isn't there to import then we didn't do a nukedisks=false with labels
	sys.exit(0)
except ImportError:
	sys.exit(0)

new_fstab_file = '/mnt/etc/fstab'
copy_new_fstab_file = '/tmp/fstab_info/copy_new_fstab'

def get_host_fstab():
	"""Get contents of /mnt/etc/fstab
	"""
	host_fstab = []
	if os.path.exists(new_fstab_file):
		file = open(new_fstab_file)

		for line in file.readlines():
			entry = {}

			split_line = line.split()
			if len(split_line) < 3:
				continue

			entry['device'] = split_line[0].strip()
			entry['mountpoint'] = split_line[1].strip()
			entry['fstype'] = split_line[2].strip()

			host_fstab.append(entry)

		file.close()

	return host_fstab


def get_existing_labels(yast_fstab, existing_fstab):
	"""Compare the two fstab inputs to determine which didn't have their LABEL= applied from autoyast.
	Returns a new list of dictionaries that contains the new identifier and the fstype"""
	no_labels = []
	existing_labels = []
	new_data = {}

	for mount in yast_fstab:
		if 'label' not in mount['device'].lower():
			# Create list to check against old_fstab
			no_labels.append(mount['mountpoint'])
			# Capture new data based on mountpoint key
			new_data[mount['mountpoint']] = [mount['device'], mount['fstype']]

	for mount in existing_fstab:
		if 'label' in mount['device'].lower() and mount['mountpoint'] in no_labels:
			if mount['fstype'] != new_data[mount['mountpoint']][1]:
				print("fstype changed during reinstall!")
			else:
				mount['new_uuid'] = new_data[mount['mountpoint']][0]
				mount['new_fstype'] = new_data[mount['mountpoint']][1]
				existing_labels.append(mount)

	return existing_labels


def main():
	"""Main function."""
	new_fstab = get_host_fstab()
	partitions_to_label = get_existing_labels(new_fstab, old_fstab)
	# Need output of the partitions_to_label to be utilized for post autoyast script.
	if not os.path.exists('/tmp/fstab_info'):
		os.makedirs('/tmp/fstab_info')
	with open('/tmp/fstab_info/__init__.py', 'a') as fstab_info:
		fstab_info.write('partitions_to_label = %s\n\n' % partitions_to_label)
	shutil.copy(new_fstab_file, copy_new_fstab_file)


main()
