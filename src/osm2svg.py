# -*- coding: utf-8 -*-
'''
Created on 2019-08-30

@author: Martin Haseneyer
'''

# imports
import re										# regular expressions
from sre_constants import SRE_FLAG_IGNORECASE	# regular expressions
import sys										# command  argument handling
from urllib.request import urlopen				# downloading a file from the web 
import xml.etree.ElementTree as ET				# XML processing

from math import ceil

# constants

MATCHER_OSM_URL = '^https?:\/\/www.openstreetmap\.org\/(relation|node|way)\/([0-9]+)(#.*)?$'  ##'^https?://www.openstreetmap.org/(relation|node|way)/([0-9]+)(#|$)'
MATCHER_FILE_XML = '.*\.xml'
MATCHER_FILE_SVG = '.*\.svg'
OVERPASS_URL = 'http://overpass-api.de/api/interpreter?data=%28{type}%28{id}%29%3B%3E%3B%29%3Bout%3B'

SVG_FACTOR = 10 ** 2



# Initialisations
source_url = None
path_xml = None
path_svg = None
osm_id = None
osm_type = None
proceed = False
min_lat = None
min_lon = None
max_lat = None
max_lon = None



# Definitions
def handle_temp(input_list, output_nodes, output_lines, output_areas):
	# Python is call-by-object-reference. This means, at the end we want to clear
	# the input list, but do not have the elements deleted in the target/output
	# lists. So we need a copy first.
	work_list = list(input_list)
	# Now, distribute the input to the output lists.
	if (len(work_list) == 1):
		output_nodes.append(work_list)
	elif (len(work_list) > 1):
		if (work_list[0] == work_list[-1]):
			del work_list[-1]
			output_areas.append(work_list)
		else:
			output_lines.append(work_list)
	# Now, clear the input list.
	del input_list[:]

# These weird-looking correction numbers are taken from <https://www.kompf.de/gps/distcalc.html>
# and indeed make the output quite pretty.
def lon_to_x(lon, min_lon):
	return round((lon - min_lon) * SVG_FACTOR * 71.5, 3)

def lat_to_y(lat, max_lat):
	return round((max_lat - lat) * SVG_FACTOR * 111.3, 3)

def lat_to_height(min_lat, max_lat):
	return ceil(SVG_FACTOR * (max_lat - min_lat) * 111.3)

def lon_to_width(min_lon, max_lon):
	return ceil(SVG_FACTOR * (max_lon - min_lon) * 71.5)



# Check command  arguments
for current_index in range(1, len(sys.argv)):
	current_arg = sys.argv[current_index]
	# Is the argument a valid OSM url?
	arg_match = re.match(MATCHER_OSM_URL, current_arg, SRE_FLAG_IGNORECASE)
	if (arg_match):
		source_url = current_arg
		osm_type = arg_match.group(1)
		osm_id = arg_match.group(2)
	# Is the argument a valid XML file path?
	else:
		arg_match = re.match(MATCHER_FILE_XML, current_arg, SRE_FLAG_IGNORECASE)
		if (arg_match):
			path_xml = current_arg
		# Is the argument a valid SVG file path?
		else:
			arg_match = re.match(MATCHER_FILE_SVG, current_arg, SRE_FLAG_IGNORECASE)
			if (arg_match):
				path_svg = current_arg

# now we have the input arguments handled

# Let's get on with input, process, output.
# IPO: Input
xml_root = None
if (source_url != None and osm_id != None and osm_type != None and (path_xml != None or path_svg != None)):
	proceed = True
	print('Downloading {type} {id} from OpenStreetMap...'.format(id = osm_id, type = osm_type), end = '')
	download_url = OVERPASS_URL.format(id = osm_id, type = 'rel' if osm_type == 'relation' else osm_type)
	source_content = urlopen(download_url).read().decode('utf-8')
	if (path_xml != None):
		file_xml = open(path_xml, 'wb')
		file_xml.write(source_content.encode('utf-8'))
		file_xml.close()
		print('successful, written to {file}.'.format(file = path_xml))
	else:
		print('successful.')
	if (path_svg != None):
		xml_root = ET.fromstring(source_content)
elif (source_url == None and path_xml != None and path_svg != None):
	print('Loading data...', end = '')
	xml_root = root = ET.parse(path_xml).getroot()
	print('done.')

# IPO: Processing
# Transform data from XML to some data structures
source_relations = {}
source_ways = {}
source_nodes = {}
if (path_svg != None and xml_root != None):
	proceed = True
	# process relation
	nodelist = xml_root.findall('relation')
	node_count = len(nodelist)
	print('Processing {count} relation{ending}...'.format(count = node_count, ending = '' if node_count == 1 else 's'), end = '')
	print()
	for current_index in range(0, len(nodelist)):
		current_item = nodelist[current_index]
		new_item = {
			'ways':		[],
			'nodes':	[]
		}
		# The XML element has "member" children with the "type" attribute either being "way" or "node".
		# With XPath we select them directly
		sub_ways = current_item.findall('member[@type=\'way\']')
		sub_nodes = current_item.findall('member[@type="node"]')
		print('- {number}: Relation {id} with {way_count} way{way_ending} and {node_count} node{node_ending}...'.format(
				number = current_index + 1, id = current_item.attrib['id'],
				way_count = len(sub_ways), way_ending = '' if len(sub_ways) == 1 else 's',
				node_count = len(sub_nodes), node_ending = '' if len(sub_nodes) == 1 else 's',
			), end = '')
		for current_subitem in sub_ways:
			new_item['ways'].append(int(current_subitem.attrib['ref']))
		for current_subitem in sub_nodes:
			new_item['nodes'].append(int(current_subitem.attrib['ref']))
		source_relations[int(current_item.attrib['id'])] = new_item
		print('done.')
	# process source_ways
	nodelist = xml_root.findall('way')
	node_count = len(nodelist)
	print('Processing {count} way{ending}...'.format(count = node_count, ending = '' if node_count == 1 else 's'), end = '')
	print()
	for current_index in range(0, len(nodelist)):
		current_item = nodelist[current_index]
		sub_items = []
		source_items = current_item.findall('nd')
		print('- {number}: Way {id} with {count} node{ending}...'.format(number = current_index + 1, id = current_item.attrib['id'], count = len(source_items), ending = '' if len(source_items) == 1 else 's'), end = '')
		for current_subitem in source_items:
			sub_items.append(int(current_subitem.attrib['ref']))
		source_ways[int(current_item.attrib['id'])] = sub_items
		print('done.')
	# process source_nodes
	nodelist = xml_root.findall('node')
	node_count = len(nodelist)
	if (node_count == 0):
		print('No nodes given, but we need nodes. Aborting here, sorry.')
		proceed = False
	else:		
		print('Processing {count} node{ending} with coordinates...'.format(count = node_count, ending = '' if node_count == 1 else 's'), end = '')
		for current_item in nodelist:
			new_item = {
				'lat':	float(current_item.attrib['lat']),
				'lon':	float(current_item.attrib['lon'])
			}
			# Also get minimum and maximum latitude and longitude of the nodes.
			# We will need that later.
			if (min_lat == None or min_lat > new_item['lat']):
				min_lat = new_item['lat']
			if (max_lat == None or max_lat < new_item['lat']):
				max_lat = new_item['lat']
			if (min_lon == None or min_lon > new_item['lon']):
				min_lon = new_item['lon']
			if (max_lon == None or max_lon < new_item['lon']):
				max_lon = new_item['lon']
			source_nodes[int(current_item.attrib['id'])] = new_item
	print('done.')

# Transform data structures to output-ready data
out_areas = []
out_lines = []
out_nodes = []

# Now, let's go through the relations (usually we have one relation only) and
# detect what elements we find there. Two types are possible: ways and nodes.
for relation_id in source_relations.keys():
	current_relation = source_relations[relation_id]
	# The single nodes are easy: they are always nodes.
	out_nodes.extend(current_relation['nodes'])
	# Now the more complicated part: the ways. Ways can be connected together
	# (and usually a relation contains multiple ways). The result can be either
	# a line (like, when having a bus or train line), or an area (like, having
	# a city boundary). We now need to check if the ways connect to a "ring"
	# (then we have an area). If they do not connect, we have a line.
	# While the ways are provided in order by OpenStreetMap, it can happen that
	# some need to be reversed. The last node of one way should be the first
	# node of the next way, but sometimes it is not the first, but the last
	# node. In this case, we reverse the way.
	# Also there are some minor cases that may happen, like having a one-node
	# way, that then is indeed a single node. Or a way that is a ring itself,
	# and does not need to connect with others.
	if (len(current_relation['ways']) > 0):
		# This is needed to loop through the ways of a relation
		current_way_index = 0
		# Initialise the temporary storage
		temp_way = []
		while (current_way_index < len(current_relation['ways'])):
			# Short handlers for the current way
			way_id = current_relation['ways'][current_way_index]
			current_way = source_ways[way_id]
			if (len(temp_way) > 0):
				if (temp_way[-1] == current_way[0]):
					# The current way fits to that in the temporary storage. Remove the first
					# node or it would be there twice (one time already in temporary storage,
					# and a second time in the new way).
					del current_way[0]
				elif (temp_way[-1] == current_way[-1]):
					# The current way fits to that in the temporary storage, but needs to be
					# reversed. Also, delete the node which would be used twice.
					del current_way[-1]
					current_way.reverse()
				else:
					# The current way does not fit to that in the tempoary storage. So handle
					# the temporary storage. Then it is empty and the current way is the start of
					# something new.
					handle_temp(temp_way, out_nodes, out_lines, out_areas)
			# Add the current way segment to the temporary storage.
			# Before we do it, we need to check if firstly there is a next way beyond the current
			# way. If there is one, maybe the current way belongs to this upcoming way, but needs
			# to be reversed to fit. Ways are reversed above to fit the way before (in the temporary
			# storage), but in case of the first way, we also need to look up to the next way.
			# If there is no next way, the current way is the last way, and therefore does not need
			# to match to anything that comes later.
			if (len(temp_way) == 0 and current_way_index +  1 < len(current_relation['ways'])):
				next_way = source_ways[current_relation['ways'][current_way_index + 1]]
				if (current_way[0] == next_way[0] or current_way[0] == next_way[-1]):
					current_way.reverse()
			# Now, just put the current way to the temporary storage.
			temp_way.extend(current_way)
			# Update index so "while" will then go to the next way
			current_way_index += 1
		# At the end, also clear the temp storage.	
		handle_temp(temp_way, out_nodes, out_lines, out_areas)



# Now get the dimensions of the structure that we have: first we will get the
# minimum and maximum latitude/longitude, then we will derive the width and
# height of the output.

if (proceed and path_svg != None):
	# Just to remember: height = y = latitude
	# Just to remember: width = x = longitude

	svg_height = lat_to_height(min_lat, max_lat)
	svg_width = lon_to_width(min_lon, max_lon)

	# required rood element
	svg_root = ET.Element('svg')
	svg_root.attrib['xmlns'] ='http://www.w3.org/2000/svg'
	svg_root.attrib['version'] = '1.1'
	svg_root.attrib['height'] = str(svg_height)
	svg_root.attrib['width'] = str(svg_width)

	# group
	svg_group = ET.Element('g')
	svg_group.attrib['id'] = 'osm-' + str(relation_id)
	svg_root.append(svg_group)
	# group title
	svg_group_title = ET.Element('title')
	svg_group_title.text = 'Relation {rel_id} from OpenStreetMap'.format(rel_id = relation_id)
	svg_group.append(svg_group_title)
	# group description
	svg_group_description = ET.Element('desc')
	svg_group_description.text = 'Relation {rel_id} from OpenStreetMap, consisting of: {way_count} way{way_ending}, {node_count} node{node_ending}'.format(
		rel_id = relation_id,
		way_count = len(source_ways),
		way_ending = '' if len(source_ways) == 1 else 's',
		node_count = len(source_nodes),
		node_ending = '' if len(source_nodes) == 1 else 's',
	)
	svg_group.attrib['id'] = 'osm-group-' + str(relation_id)
	svg_group.append(svg_group_description)

	#svg_path for areas
	path_def = 'M'
	path_def_prefix = ''
	svg_path = ET.Element('path')
	for current_area in out_areas:
		for node_id in current_area:
			current_node = source_nodes[node_id]
			path_def += path_def_prefix + str(lon_to_x(float(current_node['lon']), min_lon))
			path_def += ','
			path_def += str(lat_to_y(float(current_node['lat']), max_lat))
			path_def_prefix = ' L'
		path_def += 'Z'
		path_def_prefix = ' M'
	svg_path.attrib['id'] = 'osm-relation-' + str(relation_id)
	svg_path.attrib['d'] = path_def
	svg_path.attrib['fill'] = '#ccc'
	svg_path.attrib['fill-opacity'] = '0.6'
	svg_path.attrib['stroke'] = '#999'
	svg_path.attrib['stroke-width'] = '2'
	svg_group.append(svg_path)

	#svg_path for lines
	for current_line in out_lines:
		path_def = 'M'
		path_def_prefix = ''
		svg_path = ET.Element('path')
		for node_id in current_line:
			current_node = source_nodes[node_id]
			path_def += path_def_prefix + str(lon_to_x(float(current_node['lon']), min_lon))
			path_def += ','
			path_def += str(lat_to_y(float(current_node['lat']), max_lat))
			path_def_prefix = ' L'
		path_def_prefix = ' M'
		svg_path.attrib['d'] = path_def
		svg_path.attrib['fill'] = 'none'
		svg_path.attrib['stroke'] = '#999'
		svg_path.attrib['stroke-width'] = '2'
		svg_group.append(svg_path)

	#svg_circle for nodes
	for node_id in out_nodes:
		current_node = source_nodes[node_id]
		svg_circle = ET.Element('circle')
		svg_circle.attrib['id'] = 'osm-node-' + str(node_id)
		svg_circle.attrib['cx'] = str(lon_to_x(current_node['lon'], min_lon))
		svg_circle.attrib['cy'] = str(lat_to_y(current_node['lat'], max_lat))
		svg_circle.attrib['r'] = '10'
		svg_circle.attrib['fill'] = '#999'
		svg_circle.attrib['stroke'] = '#666'
		svg_circle.attrib['stroke-width'] = '2'
		# circle title
		svg_circle_title = ET.Element('title')
		svg_circle_title.text = 'Node {node_id} from OpenStreetMap'.format(node_id = node_id)
		svg_circle.append(svg_circle_title)
		# append
		svg_group.append(svg_circle)

	# output
	svg_tree = ET.ElementTree(svg_root)
	svg_tree.write(path_svg)
	print('SVG file written to \'{path_svg}\'.'.format(path_svg = path_svg))

# Command  arguments have not been useful? Output open feedback
if (not proceed):
	print('No useful parameters found. Nothing done.')
	print('Please provide the following parameters:')
	print()
	print('- a URL of the OpenStreetMap element you want to download, and')
	print('- a path and filename where to write the SVG image file')
	print('to download data from OpenStreetMap and create an SVG file')
	print()
	print('Or:')
	print('- a path and filename where to find a local XML file with OpenStreetMap data')
	print('- a path and filename where to write the SVG image file')
	print('to use a pre-downloaded XML file and create an SVG file')
	print()
	print('Or:')
	print('- a URL of the OpenStreetMap element you want to download, and')
	print('- a path and filename where to write an XML file with OpenStreetMap data')
	print('in case the OpenStreetMap data should be downloaded only')
	print()
	print('Or: all three of them, to download the data from OpenStreetMap, store it locally and create an SVG file')


