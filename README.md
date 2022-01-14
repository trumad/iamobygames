# iamobygames
Given an internet archive search, this script:

* grabs the url from the mobygames field of each item, 
* scrapes the mobygames page for data, 
* pastes that data into the item description, 
* and adds several more fields to the item so that games can be cross referenced using IA searches in-browser.

Supply the search string near the top of the script. Run with python3.

Existing item descriptions - 

* if it detects Jason's old bash script version of the mobygames info, it removes it before adding the updated version. 
* If it detects the new python version of the mobygames info, it removes it before adding the updated version. 
* If it doesn't detect any mobygames related stuff in the description, but there is other info there, it keeps the original description and appends the new mobygames info to the end of the description.
