#!/opt/stack/bin/python3 -E
#
# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
"""
Called after autoyast does partition, but before any RPMs are installed to the chroot environment.
Fixes the autoyast partitioning if nukedisks=False
Replaces UUID with LABEL then saves variable 'partitions_to_label' for fix_partition to use later
Merges the old fstab that contains unformatted existing partitions with the new fstab from yast.
Then mounts the old partitions that were not formatted from autoyast so they are available during install.
"""
import sys
import subprocess
import os
import fileinput
import re
import shutil
try:
	sys.path.append('/tmp')
	from fstab_info import partitions_to_label
except ModuleNotFoundError:
	# If the file isn't there to import then we didn't do a nukedisks=false with labels
	sys.exit(0)
except ImportError:
	# If the variable isn't there to import then we didn't do a nukedisks=false with labels
	sys.exit(0)


old_fstab_file = '/tmp/fstab_info/fstab'
new_fstab_file = '/mnt/etc/fstab'
tmp_fstab_file = '/tmp/fstab_info/tmp_fstab'
copy_new_fstab_file = '/tmp/fstab_info/copy_new_fstab'


def get_host_partition_devices(detected_disks):
	"""
	Returns the device names of all the partitions on a specific disk
	"""

	devices = []
	p = subprocess.Popen(
			['lsblk', '-nrio', 'NAME', '/dev/%s' % detected_disks],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
	o = p.communicate()[0]
	out = o.decode()

	for l in out.split('\n'):
		# Ignore empty lines
		if not l.strip():
			continue

		# Skip read-only and removable devices
		arr = l.split()
		diskname = arr[0].strip()

		if diskname != detected_disks:
			devices.append(diskname)

	return devices


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


def edit_new_fstab(partitions_to_label):
	"""Edit the /mnt/etc/fstab to replace the UUID= with LABEL=."""
	for partition in partitions_to_label:
		if len(partition) == 5:
			find = partition['new_uuid']
			replace = partition['device']
			with fileinput.FileInput(old_fstab_file, inplace=True) as fstab:
				for line in fstab:
					if find in line:
						print(line.replace(find, replace), end='')
					# leave the line alone
					else:
						print(line, end='')


def edit_old_fstab(yast_fstab, existing_fstab):
	"""Remove any partitions from the existing fstab if they exist in the yast generated fstab.
	We determine that they already exist by keying off the mount point."""
	new_mount_points = []
	for entry in yast_fstab:
		new_mount_points.append(entry['mountpoint'])
	for entry in existing_fstab:
		if entry['mountpoint'] in new_mount_points:
			remove = r'^' + re.escape(entry['device']) + r'.*' + re.escape(entry['mountpoint']) + r'.*'
			# remove = r'^' + entry['device'] + '.*' + entry['mountpoint'] + '.*'
			with fileinput.FileInput(old_fstab_file, inplace=True) as fstab:
				for line in fstab:
					if not re.search(remove, line):
						print(line, end='')


def merge_fstabs():
	"""After editing the old and new fstab, merge them together to contain all needed data."""
	with open(tmp_fstab_file, 'w+b') as new_file:
		for each_file in [new_fstab_file, old_fstab_file]:
			with open(each_file, 'rb') as old_file:
				shutil.copyfileobj(old_file, new_file)


def umount_partitions():
	"""Mount the old partitions that didn't exist in fstab before."""
	commands = []
	with open(copy_new_fstab_file) as fstab:
		for line in fstab:
			split_line = line.split()
			if '/' not in split_line[1]:
				# Skip partitions we can't actually mount
				continue
			commands.append(['umount', split_line[0], '/mnt%s' % split_line[1]])
	# Sort the commands by the mount point, this will make sure higher up mount is already mounted before a sub-mount
	sorted_cmds = sorted(commands, key=lambda x: x[2])
	# Reversing command sequence since we are un-mounting.
	for cmd in reversed(sorted_cmds):
		if not os.path.exists(cmd[2]):
			os.makedirs(cmd[2])
		subprocess.call(cmd)


def mount_partitions():
	"""Mount the old partitions that didn't exist in fstab before."""
	commands = []
	with open(copy_new_fstab_file) as fstab:
		for line in fstab:
			split_line = line.split()
			if '/' not in split_line[1]:
				# Skip partitions we can't actually mount
				continue
			commands.append(['mount', split_line[0], '/mnt%s' % split_line[1]])
	# Sort the commands by the mount point, this will make sure higher up mount is already mounted before a sub-mount
		sorted_cmds = sorted(commands, key=lambda x: x[2])
	for cmd in sorted_cmds:
		if not os.path.exists(cmd[2]):
			os.makedirs(cmd[2])
		subprocess.call(cmd)


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
	# In sles 11 it uses the /dev/disk/by-id/
	new_id = partition['new_uuid']
	# In sles 12 it uses the uuid=, we need to add the /dev/disk/by-uuid onto the string
	if 'uuid=' in partition['new_uuid'].lower():
		new_id = partition['new_uuid'].split('=')[1]
		new_id = '/dev/disk/by-uuid/%s' % new_id
	if 'ext' in partition['fstype'].lower():
		return_code = subprocess.call(['e2label', new_id, '%s' % label])
	if 'xfs' in partition['fstype'].lower():
		# This better be unmount or we will have issues.
		# edit the partition
		return_code = subprocess.call(['xfs_admin', '-L', '%s' % label, new_id])
	return return_code


def main():
	"""Main function."""
	# We need access to the /mnt filesystem
	mount_partitions()
	new_fstab = get_host_fstab()
	edit_old_fstab(new_fstab, old_fstab)
	edit_new_fstab(partitions_to_label)
	merge_fstabs()
	shutil.copy(tmp_fstab_file, new_fstab_file)
	# We need to unmount everything so we can label partitions
	umount_partitions()
	for each_partition in partitions_to_label:
		if len(each_partition) == 5:
			label_partition(each_partition)


main()
