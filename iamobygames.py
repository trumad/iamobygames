from internetarchive import search_items
from internetarchive import modify_metadata
from internetarchive import ArchiveSession
from internetarchive import get_item
import json
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

ia = ArchiveSession()

#collection:(softwarelibrary_msdos) AND mobygames:(www.mobygames.com)
#(mobygames:*) AND collection:(softwarelibrary_msdos)
#(agt_wraith OR agt_the-game OR agt_sos) AND collection:(softwarelibrary_msdos) AND mobygames:(http)
#collection:(softwarelibrary_msdos) AND mobygames:(www.mobygames.com)


search = search_items('(agt_wraith OR agt_the-game OR agt_sos) AND collection:(softwarelibrary_msdos) AND mobygames:(http)')
log_time = datetime.now().strftime("%y_%m_%d_%H_%M")
logfile = open("log_{}.txt".format(log_time),"w+")

#def mobygames_api_search(title):
#	parameters = {"api_key": mobygames_api_key, "platform": 2, "title": title, "format": "brief"} # platform 2 is DOS. Title runs a basic title search. format brief just grabs me the id of the game & url.
#	response = requests.get("https://api.mobygames.com/v1/games", params=parameters)
#	return response.json() # url will not be returned in the same format as IA, sadly.

def mobygames_html_scrape(the_url,ia_item,existing_item_description):
    """Gets data from Moby Games"""
    if "mobygames.com" not in the_url:
   		return "This is not a mobygames URL: {}".format(the_url)
   		logfile.write("Error: For item {}, This is not a mobygames URL: {}\n".format(ia_item,the_url))
    #print("The url: {}".format(the_url))
    url_page_content = get_url_content(the_url)
    #print(url_page_content)
    if url_page_content == "404":
    	print("This URL returned a 404: {}".format(the_url))
    	logfile.write("Error: For item {}, This mobygames URL returned a status code other than 200: {}".format(ia_item,the_url))
    	return
    description = re.search("<h2>Description</h2>([\s\S]+)<div class=\"sideBarLinks\">[\s\S]+edit description",url_page_content)
    if description:
    	description = description.groups()[0]
    else:
    	description = "No description"
    	logfile.write("Error: For item {}, No mobygames description was found at this URL: {}".format(ia_item,the_url))
    	#print("Description:\n\n{}".format(description.groups()[0]))
    soup = BeautifulSoup(url_page_content, "html.parser")
    core_release_data = get_the_data(soup, "coreGameRelease")
    core_genre_data = get_the_data(soup, "coreGameGenre")
    if len(core_release_data.items()) < 1 or len(core_genre_data.items()) < 1:
    	logfile.write("Error: For item {}, no mobygames genre/release data was found here: {}".format(ia_item,the_url))
    	return
    build_description(core_release_data,core_genre_data,description,the_url,ia_item,existing_item_description)

def build_description(core_release_data,core_genre_data,description,the_url,ia_item,existing_item_description):
	ia_release_data = ""
	ia_genre_data = ""
	def create_metadata_urls(k,v):
		mobygames_prepend = "mobygames_"+k.lower.replace(" ","_")
	for k,v in core_release_data.items():
		line = "<b>{}</b><br><a href=\"https://archive.org/search.php?query={}%3A({})\" rel=\"nofollow\">{}</a><br>".format(k,"mobygames_"+k.lower().replace(" ","_"),v.replace("/",""),v)
		ia_release_data = ia_release_data + line
	for k,v in core_genre_data.items():
		line = "<b>{}</b><br><a href=\"https://archive.org/search.php?query={}%3A({})\" rel=\"nofollow\">{}</a><br>".format(k,"mobygames_"+k.lower().replace(" ","_"),v.replace("/",""),v)
		ia_genre_data = ia_genre_data + line
	ia_description_mobygames_section = "<br><div class=\"mobygames_description\"><p>{}</p><p>{}</p><p><b>Description</b></p><p>{}</p><p>From Mobygames.com. <a href=\"{}\" rel=\"nofollow\">Original Entry</a></p></div><div class=\"end_mobygames_description\"></div><br><div></div>".format(ia_release_data,ia_genre_data,description,the_url)
	description_without_existing_mobygames_section = remove_existing_mobygames_description(existing_item_description)
	#print(description_without_existing_mobygames_section)
	if description_without_existing_mobygames_section is not "cancel_update":
		if len(description_without_existing_mobygames_section) > 4:
			logfile.write("{} had some description text which will prepend our mobygames section: {}\n".format(ia_item,description_without_existing_mobygames_section))
		final_description = description_without_existing_mobygames_section + ia_description_mobygames_section
		ia_remove_metadata(ia_item)
		ia_edit_metadata(final_description,ia_item,core_release_data,core_genre_data)
	elif description_without_existing_mobygames_section is "cancel_update":
		print ("Error: {} needs a manual check. The url \"www.mobygames.com\" was seen but I couldn't find the mobygames data. Existing Description:\r\n{}\r\nMobygames description to insert:\r\n{}".format(ia_item,existing_item_description,ia_description_mobygames_section))
		logfile.write("Error: {} needs a manual check. The url \"www.mobygames.com\" was seen but I couldn't find the mobygames data. Existing Description:\r\n{}\r\nMobygames description to insert:\r\n{}".format(ia_item,existing_item_description,ia_description_mobygames_section))
def ia_remove_metadata(ia_item):
	all_metadata = ia.get_metadata(ia_item)
	#print (all_metadata['metadata'])
	mobygames_metadata_only = {k: v  for k, v in all_metadata['metadata'].items() if k.startswith('mobygames_')}
	print(mobygames_metadata_only)
	if len(mobygames_metadata_only) == 0:
		print ("no existing mobygames metadata to reset/wipe")
		logfile.write("No existing mobygames metadata to reset/wipe")
		return
	final_overwrite_metadata = {}
	for k in mobygames_metadata_only:
		final_overwrite_metadata[k] = 'REMOVE_TAG'
	print (final_overwrite_metadata)
	print("wiping existing mobygames metadata...")
	logfile.write("wiping existing mobygames metadata...")
	metadata_wiped = modify_metadata(ia_item,final_overwrite_metadata)
	#print (metadata_wiped.text)
def ia_edit_metadata(final_description,ia_item,core_release_data,core_genre_data):
	#print (dict(description=final_description))
	def rename_keys(input_dict):
		mobygames_prepended_dict = {}
		if type(input_dict) is dict:
			for k in input_dict:
				mobygames_prepended_dict['mobygames_' + k.lower().replace(" ","_")] = input_dict[k]
		return mobygames_prepended_dict
	moby_underscore_release_data = rename_keys(core_release_data)
	moby_underscore_genre_data = rename_keys(core_genre_data)
	final_metadata = dict(description=final_description)
	for k in moby_underscore_release_data:
		final_metadata[k] = moby_underscore_release_data[k]
	for k in moby_underscore_genre_data:
		final_metadata[k] = moby_underscore_genre_data[k]
	print(final_metadata)
	#print (rename_keys(core_release_data))
	#print (rename_keys(core_genre_data))
	print("updating IA item with final metadata...")
	update_log = modify_metadata(ia_item,metadata=final_metadata)
	#print (update_log.text)
	#print("final description:")
	#print (final_description)
	#print ("data not modified (but would've been)")
	logfile.write(update_log.text)
	logfile.write("\nCompleted item: {}\n".format(ia_item))

def remove_existing_mobygames_description(existing_item_description):
	python_generated_mobygames_section = re.search("(?:<br\s?/?>)?<div class=\"mobygames_description\">[\s\S]+<div class=\"end_mobygames_description\"></div>(?:<br\s?/?>)?(?:<div></div>)?",existing_item_description)
	bash_generated_mobygames_section = re.search("(?:<p><b>Developed by</b>|<p><b>Published by</b>|<p><b>Released</b>|<p><b>Description|<p><b>Also For</b>|<p><b>Platform</b>)[\s\S]+<a href=\"https?://www\.mobygames\.com.*>Original Entry</a>(?:</p>|<br)",existing_item_description)
	but_mobygames_is_somewhere_right = re.search("http://www.mobygames.com",existing_item_description)
	if python_generated_mobygames_section:
		return re.sub(r"(?:<br\s?/?>)?<div class=\"mobygames_description\">[\s\S]+<div class=\"end_mobygames_description\"></div>(?:<br\s?/?>)?(?:<div></div>)?", "", existing_item_description)
	elif bash_generated_mobygames_section:
		return re.sub(r"(?:<p><b>Developed by</b>|<p><b>Published by</b>|<p><b>Released</b>|<p><b>Description|<p><b>Also For</b>|<p><b>Platform</b>)[\s\S]+<a href=\"https?://www\.mobygames\.com.*>Original Entry</a>(?:</p>|<br)", "", existing_item_description)
	elif but_mobygames_is_somewhere_right:
		print ("Mobygames URL exists in the description but a match for the mobygames section wasn't found. Not updating.")
		return "cancel_update"
	else:
		return existing_item_description + "<br>"

def get_the_data(soup_data, the_id):
	"""Returns a dictionary of data from a div with chosen ID"""
	try:
		current_div = soup_data.find("div", id="{}".format(the_id))
	except:
		return {}
	try:
		specific_data = current_div.find_all("div")
	except:
		specific_data = []
	the_list = []

	for each in specific_data:
		if each.find(text=False, recursive=False):
			if each.find('a', recursive=False):
				the_list.append(each.text.replace(' | Combined\xa0View', '').replace('\xa0', ' '))
		elif each.find(text=True, recursive=False):
			the_list.append(each.text.replace('\xa0', ' '))

	the_dict = dict(zip(the_list[::2], the_list[1::2]))
	return the_dict


def get_url_content(the_url):
    """"""
    #print(repr(the_url))
    the_url = the_url.rstrip() # for those pesky times when the URL has weird characters
    response = requests.get(the_url)
    #print(repr(the_url))
    #print (response.status_code)
    if response.status_code is not 200:
    	return "404"
    return response.text


if __name__ == "__main__":
	""""""


for result in search:
	itemid = result['identifier']
	logfile.write("Starting item:    {}\n".format(itemid))
	try:
		item = get_item(itemid)
	except:
		item = "Error: ia python error while using get_item on item {}. Skipping\n".format(itemid)
		print(item)
		logfile.write(item)
		continue
	try:
		title = item.item_metadata['metadata']['title']
	except:
		print ("Error: "+itemid+" does not seem to exist any more")
		logfile.write("Error: "+itemid+" does not seem to exist any more\n")
		continue
	try:
		mobygames_url = item.item_metadata['metadata']['mobygames']
	except:
		print (itemid+" does not have mobygames metadata")
		logfile.write("Error: "+itemid+" does not have mobygames metadata\n")
		continue
	try:
		existing_item_description = item.item_metadata['metadata']['description']
	except KeyError:
		existing_item_description = ""
	print ("IA Item ID: {}".format(itemid))
	print ("IA Game Title: {}".format(title))
	print("Mobygames URL: {}".format(mobygames_url))
	print ("existing_item_description:")
	print (existing_item_description)
	print ("-"*20)
	#print (mobygames_search(title))
	try:
		mobygames_html_scrape(mobygames_url,itemid,existing_item_description) #This function starts pretty much everything else
	except:
		print ("Error: There was an unidentified issue while attempting to update"+itemid+"")
		logfile.write("Error: There was an unidentified issue while attempting to update"+itemid+"\n")
		continue
	print ("\n------------ Next Item -------------\n")
print ("Process complete! Errors can be viewed in the logfile by searching 'Error:'")
logfile.close()

