
import subprocess

#updating the list of english entries
python_files=["main.py", "toolbox.py", "settings.py", "gnugo_analysis.py", "leela_analysis.py", "leela_zero_analysis.py", "aq_analysis.py", "ray_analysis.py", "dual_view.py", "live_analysis.py", "gtp_terminal.py", "r2sgf.py", "r2csv.py", "tabbed.py"]


cmd="xgettext --no-wrap -E --keyword=_ --language=python -o en.po --sort-by-file "
output = subprocess.check_output(cmd.split()+["../"+f for f in python_files])

def get_sentences_old(lang,check_for_double=False):

	data_file_url=lang+".po"
	print "Loading translation file:",data_file_url
	
	data_file = open(data_file_url,"r")
	translation_data=data_file.read()
	data_file.close()
	
	sentences=[]
	translated_sentences=[]
	for line in translation_data.split('\n'):
		key="msgid"
		if line[:len(key)+2]==key+' "':
			entry=line[len(key)+2:-1]
			if check_for_double:
				if entry in sentences:
					print "[Warning] double entries for:",entry
			sentences.append(entry)
		
		key="msgstr"
		if line[:len(key)+2]==key+' "':
			translation=line[len(key)+2:-1]
			translation=translation.replace("\\\"","\"")
			translated_sentences.append(translation)
		
	return sentences,translated_sentences

def get_translations(lang,check_for_double=False):
	translations={}

	data_file_url=lang+".po"
	print "Loading translation file:",data_file_url

	data_file = open(data_file_url,"r")
	translation_data=data_file.read()
	data_file.close()

	entry=""
	translation=""

	for line in translation_data.split('\n'):

		key="msgid"
		if line[:len(key)+2]==key+' "':
			entry=line[len(key)+2:-1]
			translation=""

		key="msgstr"
		if line[:len(key)+2]==key+' "':
			translation=line[len(key)+2:-1]
			translation=translation.replace("\\\"","\"")
			if len(entry)>0:
				if check_for_double:
					if entry in translations:
						print "[Warning] double entries for:",entry
				translations[entry]=translation
				
			
			entry=""
			translation=""
	return translations

print
print "================================================================"
print "================================================================"
print "================================================================"
print

english=get_translations("en",True)

available_translations=["fr","de","kr","zh","pl","new_translation"]

from sys import argv
if len(argv)==2:
	if argv[1] in available_translations:
		print "Selection of lang=",argv[1]
		available_translations=[argv[1]]

statistics={}

for lang in available_translations:
	print
	print "============= Checking language="+lang,"============="
	translations=get_translations(lang)
	statistics[lang]={"total":len(translations.keys()),"missing":0,"empty":0,"extra":0}
	print
	print "==== English sentences missing in",lang+".po ===="
	found=False
	for sentence in english.keys():
		if sentence not in translations.keys():
			print 'msgid "'+sentence+'"'
			print 'msgstr ""'
			print
			found=True
			statistics[lang]["missing"]+=1
	if not found:
		print "(none)"
	
	if lang!="new_translation":
		print
		print "==== Empty translations in",lang+".po ===="
		found=False
		for sentence,translation in translations.iteritems():
			if not translation:
				print 'msgid "'+sentence+'"'
				print 'msgstr ""'
				print
				found=True
				statistics[lang]["empty"]+=1
		if not found:
			print "(none)"
	

	print
	print "==== Extra sentences in",lang+".po ===="
	found=False
	for sentence,translation in translations.iteritems():
		if sentence not in english.keys():
			print "msgid", '"'+sentence+'"'
			print "msgstr", '"'+translation+'"'
			print
			found=True
			statistics[lang]["extra"]+=1
	if not found:
		print "(none)"
	

print
print
print "========================"
for lang in statistics.keys():
	print "language: "+lang+":"
	print "\ttotal:",statistics[lang]["total"]
	print "\tmissing:",statistics[lang]["missing"]
	print "\tempty:",statistics[lang]["empty"]
	print "\textra:",statistics[lang]["extra"]
	print
