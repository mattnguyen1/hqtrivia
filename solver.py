import os
import time
import crayons
from mediawiki import MediaWiki
wikipedia = MediaWiki()
from bs4 import BeautifulSoup
import google
import nltk
import pytesseract
import webbrowser
from nltk.tokenize import RegexpTokenizer

from PIL import Image, ImageEnhance

SCREEN_DIR = "/Users/mattnguy/Desktop" # Mine was "/Users/davidhariri/Desktop"
IDENTIFIER = "Screen Shot"
CROP_AREA = (78, 208, 986, 1161) # Mine was "/Users/davidhariri/Desktop"
DEBUG = False

tokenizer = RegexpTokenizer(r'\w+')

stop = set(nltk.corpus.stopwords.words("english"))

def get_google_result(q):
	google_url = "https://www.google.com/search?q="
	google_url += q
	print(google_url)
	google_search_results = google.get_page(google_url)
	google_search_soup = BeautifulSoup(google_search_results, "html.parser")
	google_text_search_results = google_search_soup.get_text().encode("utf-8").lower()
	return google_text_search_results

while True:
	screen_shots = list(filter(
		lambda p: IDENTIFIER in p, os.listdir(SCREEN_DIR)))

	if len(screen_shots) == 0:
		time.sleep(0.1)
	else:
		os.system("clear")
		# Pause while loop while processing image
		file_path = os.path.join(SCREEN_DIR, screen_shots[-1])

		# Open screen shot
		screen = Image.open(file_path)

		# Get tesseract result from filtered screen
		# TODO: Round font training
		result = pytesseract.image_to_string(
			screen, config="load_system_dawg=0 load_freq_dawg=0")

		# Split up newlines until we have our question and answers
		parts = result.split("\n\n")

		# Get question
		question = parts.pop(0).replace("\n", " ")
		while question.count("?") == 0:
			question += " " + parts.pop(0).replace("\n", " ")
		question = question.replace("?", "").encode("utf-8").lower()
		q_terms = tokenizer.tokenize(question)
		q_terms = list(filter(lambda t: t not in stop, q_terms))
		q_terms = set(q_terms)

		# create question url
		question_as_url_query = "+".join(question.split(" "))

		# open question query in browser
		question_query_url = "https://www.google.com/search?q=" + question_as_url_query
		webbrowser.open(question_query_url, 0, True)

		# Encode the different parts
		parts = "\n".join(parts).encode("utf-8").lower()
		parts = parts.split("\n")

		answers = list(filter(lambda p: len(p) > 0, parts))

		print("\n\n{}\n\n{}\n\n".format(
			crayons.blue(question),
			crayons.blue(", ".join(answers))
		))

		for i, a in enumerate(answers):
			answers[i] = a.replace("|", "l")
			answers[i] = a.replace("\xef\xac\x82", "fl")

		answer_results = {}

		for answer in answers:
			q_terms_with_answer = "+".join(question.split(" ")) + "+" + "+".join(answer.split(" "))
			answer_text_results = get_google_result(q_terms_with_answer)
			# solo_text_results = get_google_result("+".join(answer.split(" ")))

			answer_results[answer] = {
				"content": answer_text_results,
				"words": answer_text_results.split(" ") #+ solo_text_results.split(" ")
			}

		
		question_text_results = get_google_result(question_as_url_query)
		question_results = {
			"content": question_text_results,
			"words": question_text_results.split(" ")
		}


		for a in answer_results:
			word_len = len(answer_results[a]["words"])

			answer_terms = tokenizer.tokenize(a)
			total_term_count = 0
			extra_term_count = 0
			other_term_count = 0
			answer_in_question_term_count = 0

			print(crayons.blue(a))
			print('==================')

			# Count the terms in the question that show up in the answer's query
			for t in q_terms:
				term_count = (answer_results[a]["words"].count(t[:-1]) + answer_results[a]["words"].count(t)) / 2.0
				total_term_count += term_count
				print("++", t, float(term_count) * 10000 / word_len)

			# Iterate over the terms of the answer
			for t in answer_terms:
				# Exclude stopwords in the terms
				if t in stop:
					continue

				# Count the terms in the answer that show up in teh results of the question query
				term_count = (question_results["words"].count(t[:-1]) + question_results["words"].count(t)) / 2.0
				answer_in_question_term_count += term_count
				print("+++", t, float(term_count) * 10000 / word_len)

				# Count the terms in the answer that show up in the answer's query
				term_count = (answer_results[a]["words"].count(t[:-1]) + answer_results[a]["words"].count(t)) / 2.0
				extra_term_count += term_count
				print("+", t, float(term_count) * 10000 / word_len)

			for other_answer in answer_results:
				if other_answer is a:
					continue

				other_answer_terms = tokenizer.tokenize(other_answer)
				for other_answer_term in other_answer_terms:
					term_count = (answer_results[a]["words"].count(other_answer_term[:-1]) + answer_results[a]["words"].count(other_answer_term)) / 2.0
					other_term_count += term_count
					print("-", other_answer_term, float(term_count) * 10000 / word_len)



			tc = float(total_term_count) / word_len
			etc = float(extra_term_count) / word_len
			aqtc = float(answer_in_question_term_count) / word_len
			oaqtc = float(other_term_count) / word_len
			print(tc, etc)
			tcp = round(aqtc * 50000 + tc * 10000 + etc * 5000 - (oaqtc * 2500), 2)

			answer_results[a]["score"] = tcp
			print(crayons.magenta(tcp/10000))
			print("\n\n")

		max_a = 0
		max_a_key = None
		combined_score = 0

		# Maximize
		for a in answer_results:
			combined_score += answer_results[a]["score"]
			if answer_results[a]["score"] > max_a:
				max_a_key = a
				max_a = max(answer_results[a]["score"], max_a)

		percentage = max_a * 100 / combined_score
		print(crayons.green(max_a_key))
		print("%d%%" % percentage)

		try:
			os.remove(file_path)
			print("deleted file")
		except:
			print("couldn't delete")

	time.sleep(0.1)
