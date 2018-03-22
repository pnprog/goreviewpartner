
import subprocess

#updating the list of english entries
python_files=["main.py", "toolbox.py", "settings.py", "gnugo_analysis.py", "leela_analysis.py", "leela_zero_analysis.py", "aq_analysis.py", "ray_analysis.py", "dual_view.py", "live_analysis.py", "gtp_terminal.py", "r2sgf.py"]


cmd="xgettext --no-wrap -E --keyword=_ --language=python -o en.po --sort-by-file "
output = subprocess.check_output(cmd.split()+["../"+f for f in python_files])

def get_sentences(lang,check_for_double=False):

	data_file_url=lang+".po"
	print "Loading translation file:",data_file_url
	
	data_file = open(data_file_url,"r")
	translation_data=data_file.read()
	data_file.close()
	
	sentences=[]

	for line in translation_data.split('\n'):
		key="msgid"

		if line[:len(key)+2]==key+' "':
			entry=line[len(key)+2:-1]
			if check_for_double:
				if entry in sentences:
					print "[Warning] double entries for:",entry
			sentences.append(entry)
	return sentences

print
print "================================================================"
print "================================================================"
print "================================================================"
print

english_sentences=get_sentences("en",True)

available_translations=["fr","de"]

from sys import argv
if len(argv)==2:
	if argv[1] in available_translations:
		print "Selection of lang=",argv[1]
		available_translations=[argv[1]]

for lang in available_translations:
	print
	print "============= Checking language="+lang,"============="
	translations=get_sentences(lang)
	print
	print "==== English sentences missing in",lang+".po ===="
	found=False
	for sentence in english_sentences:
		if sentence:
			if sentence not in translations:
				print 'msgid "'+sentence+'"'
				print 'msgstr ""'
				print
				found=True
	if not found:
		print "(none)"
	
	print
	print "==== Extra sentences in",lang+".po ===="
	found=False
	for sentence in translations:
		if sentence:
			if sentence not in english_sentences:
				print sentence
				found=True
	if not found:
		print "(none)"
	
