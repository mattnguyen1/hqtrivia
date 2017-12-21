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
import threading

from PIL import Image, ImageEnhance

SCREEN_DIR = "/Users/mnguyen/Desktop"
IDENTIFIER = "Screen Shot"

tokenizer = RegexpTokenizer(r'\w+')

stopword_list = [u'i', u'me', u'my', u'myself', u'we', u'our', u'ours', u'ourselves', u'you', u'your', u'yours', u'yourself', u'yourselves', u'he', u'him', u'his', u'himself', u'she', u'her', u'hers', u'herself', u'it', u'its', u'itself', u'they', u'them', u'their', u'theirs', u'themselves', u'what', u'which', u'who', u'whom', u'this', u'that', u'these', u'those', u'am', u'is', u'are', u'was', u'were', u'be', u'been', u'being', u'have', u'has', u'had', u'having', u'do', u'does', u'did', u'doing', u'a', u'an', u'the', u'and', u'but', u'if', u'or', u'because', u'as', u'until', u'while', u'of', u'at', u'by', u'for', u'with', u'about', u'against', u'between', u'into', u'through', u'during', u'before', u'after', u'above', u'below', u'to', u'from', u'up', u'down', u'in', u'out', u'on', u'off', u'over', u'under', u'again', u'further', u'then', u'once', u'here', u'there', u'when', u'where', u'why', u'how', u'all', u'any', u'both', u'each', u'other', u'some', u'such', u'no', u'nor', u'not', u'only', u'own', u'same', u'so', u'than', u'too', u'very', u's', u't', u'can', u'will', u'just', u'don', u'should', u'now', u'd', u'll', u'm', u'o', u're', u've', u'y', u'ain', u'aren', u'couldn', u'didn', u'doesn', u'hadn', u'hasn', u'haven', u'isn', u'ma', u'mightn', u'mustn', u'needn', u'shan', u'shouldn', u'wasn', u'weren', u'won', u'wouldn']

stop = set(stopword_list)

def get_google_result(q, result_map):
	# Form search url
	google_url = get_google_search_url(q)

	# Parse text of result page
	print(google_url)
	google_search_results = google.get_page(google_url)
	google_search_soup = BeautifulSoup(google_search_results, "html.parser")
	google_text_search_results = google_search_soup.get_text().encode("utf-8").lower()


	result_map["content"] = google_text_search_results
	result_map["words"] = google_text_search_results.split(" ")

	# Return text
	return google_text_search_results

def get_google_search_url(q):
	return "https://www.google.com/search?q=" + "+".join(q.split(" "))


def parse_ocr_result(ocr_result):
	# Split up newlines until we have our question and answers
	parts = [x for x in ocr_result.split("\n") if not x is u'']

	# Get question
	question = parts.pop(0).replace("\n", " ")

	# Loop until quesiton mark exists
	while question.count("?") == 0:
		question += " " + parts.pop(0).replace("\n", " ")

	question = question.replace("?", "").encode("utf-8").lower()
	q_terms = tokenizer.tokenize(question)
	q_terms = list(filter(lambda t: t not in stop, q_terms))
	q_terms = set(q_terms)

	return (question, q_terms, parts)

while True:
	screen_shots = list(filter(
		lambda p: IDENTIFIER in p, os.listdir(SCREEN_DIR)))

	if len(screen_shots) == 0:
		time.sleep(0.1)
	else:
		os.system("clear")
		# Pause while loop while processing image
		file_path = os.path.join(SCREEN_DIR, screen_shots[0])

		# Open screen shot
		try:
			screen = Image.open(file_path)
		except:
			continue

		# Get tesseract result from filtered screen
		result = pytesseract.image_to_string(
			screen, config="load_system_dawg=0 load_freq_dawg=0")

		print(result)

		# Get parsed results
		(question, q_terms, parts) = parse_ocr_result(result)

		# create question url
		question_query_url = get_google_search_url(question)

		# open question query in browser
		webbrowser.open(question_query_url, 0, True)

		# Encode the different parts
		parts = "\n".join(parts).encode("utf-8").lower()
		parts = parts.split("\n")

		answers = list(filter(lambda p: len(p) > 0, parts))

		# Display question and answers
		print("\n\n{}\n\n{}\n\n".format(
			crayons.blue(question),
			crayons.blue(", ".join(answers))
		))

		# OCR Sanitization
		for i, a in enumerate(answers):
			answers[i] = a.replace("|", "l")
			answers[i] = a.replace("\xef\xac\x82", "fl")

		answer_results = {}

		threads = []
		for answer in answers:
			answer_results[answer] = {}
			q_terms_with_answer = question + " " + answer
			answer_query_thread = threading.Thread(target=get_google_result, args=(q_terms_with_answer, answer_results[answer],))
			threads.append(answer_query_thread)
			answer_query_thread.start()

		question_results = {}
		question_query_thread = threading.Thread(target=get_google_result, args=(question, question_results,))
		threads.append(question_query_thread)
		question_query_thread.start()

		for t in threads:
			t.join()

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
					# Exclude stopwords in the terms
					if other_answer_term in stop:
						continue

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

		low_a = 9999999999
		low_a_key = None

		# Maximize
		for a in answer_results:
			combined_score += answer_results[a]["score"]
			if answer_results[a]["score"] > max_a:
				max_a_key = a
				max_a = max(answer_results[a]["score"], max_a)

			if answer_results[a]["score"] < low_a:
				low_a_key = a
				low_a = min(answer_results[a]["score"], low_a)

		percentage = max_a * 100 / (combined_score + 1)
		percentage_low = low_a * 100 / (combined_score + 1)
		print(crayons.green(max_a_key))
		print("%d%%" % percentage)
		print(crayons.red(low_a_key))
		print("%d%%" % percentage_low)

		try:
			os.remove(file_path)
			print("deleted file")
		except:
			print("couldn't delete")

	time.sleep(0.1)
