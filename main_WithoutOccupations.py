import os, inspect
import json
import pandas as pd
import datetime
import isodate

from route_graph import *
from validate_solution import *

import itertools

# FILE_NAME = "02_a_little_less_dummy.json"
FILE_NAME = "01_dummy.json"
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
scenario = os.path.join(currentdir,'problem_instances',FILE_NAME)

def best_solution(all_scores, combinations_matrix, problem_instance_label, problem_instance_hash, hash):
	idx = all_scores.index(min(all_scores))
	best = combinations_matrix[idx]
	train_runs = []
	for j in range(len(best)):
		train_runs.append(list_of_solutions[j]['train_runs_possible'][best[j]])

	my_solution = {
			'problem_instance_label': problem_instance_label,
			'problem_instance_hash': problem_instance_hash,
			'hash': hash,
			'train_runs': train_runs
		}
	return my_solution

def test_all_solutions(list_of_solutions, problem_instance_label, problem_instance_hash,hash, scenario_content):
	
	combinations = [[] for i in range(len(list_of_solutions))]
	for i in range(len(combinations)):
		for j in range(len(list_of_solutions[i]['train_runs_possible'])):
			combinations[i].append(j)

	combinations_matrix = list(itertools.product(*combinations))

	all_scores = []
	for i in range(len(combinations_matrix)):
		solution_tested = combinations_matrix[i]
		train_runs = []
		for j in range(len(solution_tested)):
			train_runs.append(list_of_solutions[j]['train_runs_possible'][solution_tested[j]])
		my_solution = {
			'problem_instance_label': problem_instance_label,
			'problem_instance_hash': problem_instance_hash,
			'hash': hash,
			'train_runs': train_runs
		}
		validation_result = do_loesung_validation(scenario_content, my_solution)
		warnings = [x for x in validation_result["business_rules_violations"] if x["severity"] == "warning"]
		errors = [x for x in validation_result["business_rules_violations"] if x["severity"] == "error"]
		if len(errors) == 0:
			score = objective_function(scenario_content, my_solution)
		else:
			score = -1
		all_scores.append(score)
		print("THE SCORE IS :" + str(score))

		return combinations_matrix, all_scores

def objective_function(scenario_content, my_solution):

	sumsum = 0
	penalty = 0
	for service in scenario_content["service_intentions"]:
		# print("SERVICE ID ::: " +str(service["id"]))
		for ser in my_solution["train_runs"]:
			if ser["service_intention_id"] == service["id"]:
				train_run_sol = ser["train_run_sections"]
		for section_sol in train_run_sol:
			sequence_number = (section_sol["sequence_number"])
			for route in scenario_content["routes"]:
				if route["id"] == service["id"]:
					for sec1 in route["route_paths"]:
						for sec in sec1["route_sections"]:
							if sec["penalty"] is not None:
								penalty += sec["penalty"]

		for requirement in service["section_requirements"]:
			# print("REQUIREMENT ::: " + str(requirement["section_marker"]))
			for run_section in train_run_sol:
				if run_section["section_requirement"] == requirement["section_marker"]:
					selected_section_sol = run_section

			# print("SOLUTION ::: " + str(selected_section_sol))

			try:
				entry_delay_weight_sr = requirement["entry_delay_weight"]
			except:
				entry_delay_weight_sr = 0
			# print(entry_delay_weight_sr)

			t_entry = selected_section_sol["entry_time"]
			t_entry = datetime.datetime.strptime(t_entry, "%H:%M:%S")
			# print(t_entry)
			try:
				entry_latest_sr = datetime.datetime.strptime(requirement["entry_latest"], "%H:%M:%S")

				if t_entry > entry_latest_sr:
					MAXA = (t_entry - entry_latest_sr).seconds
				else:
					MAXA = 0

			except:
				MAXA = 0

			try:
				exit_delay_weight_sr = requirement["exit_delay_weight"]
			except:
				exit_delay_weight_sr = 0
			# print(exit_delay_weight_sr)
			t_exit = selected_section_sol["exit_time"]
			t_exit = datetime.datetime.strptime(t_exit, "%H:%M:%S")
			# print(t_exit)
			try:
				exit_latest_sr = datetime.datetime.strptime(requirement["exit_latest"], "%H:%M:%S")

				if t_exit > exit_latest_sr:
					MAXB = (t_exit - exit_latest_sr).seconds
				else:
					MAXB = 0

			except:
				MAXB = 0
			A = entry_delay_weight_sr * MAXA
			B = exit_delay_weight_sr * MAXB
			sumsum += (A+B)

	print("RESPECT THE REQUIREMENTS : " + str(sumsum))
	print("USE PENALTY PATHS : " + str(penalty))
	return sumsum + penalty


# Depth First Search algorithm (pour trouver tous les paths possibles dans le réseau) 
def myDFS(trans_dict,start,done,paths,path=[]): 
	path=path+[start] 
	# if len(path)==length:
	# 	paths.append(path) 
	# else:
	# if len(trans_dict[start]) == 0:
	# 	paths.append(path) 
	if start not in trans_dict.keys():
		paths.append(path)
	else:
		# if len(trans_dict[start]) == 0:
		# 	done = True
		# else:
		for node in trans_dict[start]:
			a = node['node']
			myDFS(trans_dict,a,done,paths,path)

## Fonction retourne la section avec le temps de parcours minimum
def le_plus_court(sections):
	result = sections[0]
	min_time = isodate.parse_duration(sections[0]['minimum_running_time'])
	for section in sections:
		if (isodate.parse_duration(section['minimum_running_time']) < (min_time)):
					result = section
					min_time = isodate.parse_duration(section['minimum_running_time'])
	return result

## Fonction qui retourne un dict avec le 'entry_time' et le 'exit_time' pour la section selectionnée
def compute_time(section_requirements, entry_time, section):
	minimum_running_time = isodate.parse_duration(section['minimum_running_time'])
	# print(entry_time)
	# print(minimum_running_time)
	exit_time = entry_time +  minimum_running_time
	# print(section_requirements)
	if section_requirements != None:
		## First check if there are any time requirement 
		if "entry_latest" in section_requirements.keys():
			entry_latest = datetime.datetime.strptime(section_requirements["entry_latest"], "%H:%M:%S")
			if entry_time > entry_latest:
				# print("The entry time of the train in station " + str(section_requirements["section_marker"]) + " is to late.")
				pass
			else:
				# print("The entry_latest requirement is respected.")
				pass

		if "entry_earliest" in section_requirements.keys():
			entry_earliest = datetime.datetime.strptime(section_requirements["entry_earliest"], "%H:%M:%S")
			if entry_time < entry_earliest:
				# print("The entry time of the train in station " + str(section_requirements["section_marker"]) + " is to early.")
				pass
			else:
				# print("The entry_earliest requirement is respected.")
				pass

		if "min_stopping_time" in section_requirements.keys():
			exit_time += isodate.parse_duration(section_requirements['min_stopping_time'])
			# print("The min_stopping_time of the train in station " + str(section_requirements["section_marker"]) + " is respected.")


		if "exit_earliest" in section_requirements.keys():
			exit_earliest = datetime.datetime.strptime(section_requirements["exit_earliest"], "%H:%M:%S")
			if exit_time < exit_earliest:
				exit_time = exit_earliest
			# print("The exit_earliest of the train in station " + str(section_requirements["section_marker"]) + " is respected.")


		if "exit_latest" in section_requirements.keys():
			exit_latest = datetime.datetime.strptime(section_requirements["exit_latest"], "%H:%M:%S")
			if exit_time > exit_latest:
				# print("The exit_latest in station " + str(section_requirements["section_marker"]) + " cannot be respected.")
				pass
			else:
				# print("The exit_latest in station " + str(section_requirements["section_marker"]) + " is respected.")
				pass
	time = {
		"entry_time": entry_time.strftime("%H:%M:%S"),
		"exit_time": exit_time.strftime("%H:%M:%S")
	}

	return time

def generate_paths_dict(route_paths):
	result = {}
	for path in route_paths:
		for (i, route_section) in enumerate(path["route_sections"]):
			from_node = from_node_id(path, route_section, i)[1:-1]
			to_node = to_node_id(path, route_section, i)[1:-1]
			sn = route_section['sequence_number']

			if from_node not in result.keys():
				result[from_node] = []

			doublon = False
			for k in range(len(result[from_node])):
				if result[from_node][k] == {'node': to_node, 'seq_nb': sn}:
					doublon = True
			if not doublon:
				result[from_node].append({'node': to_node, 'seq_nb': sn})

				# print("Adding Edge from {} to {} with sequence number {}".format(from_node_id(path, route_section, i), to_node_id(path, route_section, i), sn))
	# print(result)
	return result

## Converti le chemin de nodes en chemin de seq
def convert_paths(paths, the_route_net):
	result = []
	for path in paths:
		new_path = []
		for (i, node) in enumerate(path):
			if node in the_route_net.keys():
				# print(the_route_net[node])
				if len(the_route_net[node]) == 1:
					new_path.append(the_route_net[node][0]['seq_nb'])
				else:
					for k in range(len(the_route_net[node])):
						if the_route_net[node][k]['node']== path[i+1]:
							new_path.append(the_route_net[node][k]['seq_nb'])
					# print(path[i+1])
		result.append(new_path)
	return result

## Extrait une section du scenario basée sur son numéro
def extract_section(selected_route, seq_nb):
	for route in selected_route["route_paths"]:
		id = route['id']
		for section in route["route_sections"]:
			if section["sequence_number"] == seq_nb:
				result = section
				result["id"] = id
				return result 


print("Je télécharge le scenario.")
## Upload le scenario
# 

# scenario = os.path.join(currentdir,'sample_files',"sample_scenario.json")
with open(scenario) as fp:
	scenario_content = json.load(fp)

# print("Je créé le réseau de routes et je liste les chemins possibles.")
# ## Créé le réseau de routes
# the_route_net = generate_paths_dict(scenario_content)

# ## Liste tous les chamins possibles
# paths = []
# for node in the_route_net:
# 	myDFS(the_route_net,node,False,paths)
# final_paths = []
# for path in paths:
# 	if path[0][-9:] == 'beginning':
# 		final_paths.append(path)

# print("==> Il y a " + str(len(final_paths)) + " chemins possibles.")

# final_paths = convert_paths(final_paths, the_route_net)


## Extraction des paramètres globaux du scenario
problem_instance_label = scenario_content['label']
problem_instance_hash = scenario_content['hash']
hash = -516528637
train_runs = []

nb_of_trains = len(scenario_content['service_intentions'])

print("==> Il y a " + str(nb_of_trains) + " services différents à proposer.")

list_of_solutions = []
for k in range(nb_of_trains):
	train = scenario_content['service_intentions'][k]
	service_intention_id = train['id']
	start_section = train["section_requirements"][0]
	train_runs_possible = []

	print("#################################")
	print("service_intention_id ::: " + str(service_intention_id))

	

	## Extrait la route correspondant au scenario
	for route in scenario_content['routes']:
		if route['id'] == service_intention_id:
			selected_route = route 
	
	the_route_net = generate_paths_dict(selected_route["route_paths"])
	## Liste tous les chamins possibles
	paths = []
	for node in the_route_net:
		myDFS(the_route_net,node,False,paths)
	final_paths = []
	for path in paths:
		if path[0][-9:] == 'beginning':
			final_paths.append(path)

	print("==> Il y a " + str(len(final_paths)) + " chemins possibles.")

	final_paths = convert_paths(final_paths, the_route_net)


	for chemin in final_paths:
		# print("Chemin testé : "+str(chemin))
		## Initialise les listes qui construiront la solution finale 
		train_run_sections = []
		sections = []
		time = []
		for (idx, seq_nb) in enumerate(chemin):
			# print(selected_route)
			section = extract_section(selected_route, seq_nb)

			if section == None:
				print("Ce chemin n'existe pas !")
				break

			section_requirements = None

			if ("section_marker" in section.keys()) and( len(section["section_marker"]) > 0):
				# print(section["section_marker"][0])
				for r in train["section_requirements"]:
					if r["section_marker"] == section["section_marker"][0]:
						section_requirements = r

			if idx == 0 :
				if "entry_earliest" not in start_section.keys():
					print("Je ne connais pas l'heure du départ pour la première séquence.")
				else:
					entry_time = start_section['entry_earliest']
					entry_time = datetime.datetime.strptime(entry_time, "%H:%M:%S") 
					new_time = compute_time(section_requirements, entry_time, section)
					# exit = datetime.datetime.strptime(start_section['entry_earliest'], "%H:%M:%S") +  \
					# isodate.parse_duration(section['minimum_running_time'])
					# new_time = {
					# 	"entry_time": start_section['entry_earliest'],
					# 	"exit_time": exit.strftime("%H:%M:%S")
					# }
			else:
				

				entry_time = time[len(time)-1]["exit_time"]
				entry_time = datetime.datetime.strptime(entry_time, "%H:%M:%S")
				new_time = compute_time(section_requirements, entry_time, section)

			time.append(new_time)
			sections.append(section)

		## On vérifie qu'on passe bien par les gares des requirements
		marker_to_go = []
		for r in train["section_requirements"]:
			marker_to_go.append(r["section_marker"])

		idx = 0
		for ss in sections:
			try :
				marker = ss["section_marker"][0]
				if marker not in marker_to_go:
					marker = None
			except:
				marker = None
			
			## On fait un joli dict pour chaque section
			sol = {
				"entry_time": time[idx]["entry_time"],
				"exit_time": time[idx]["exit_time"],
				"route": service_intention_id,
				"route_section_id": str(service_intention_id) +"#"+str(ss["sequence_number"]),
				"sequence_number": idx+1,
				"route_path": ss['id'],
				"section_requirement": marker
			}

			train_run_sections.append(sol)
			idx += 1

		result = {'service_intention_id': service_intention_id, 'train_run_sections': train_run_sections}

		## La liste de toutes les runs possibles pour ce service_intention_id
		train_runs_possible.append(result)

	## La listes de toutes les solutions possibles
	solution = {
		"service_intention_id": service_intention_id,
		"train_runs_possible": train_runs_possible
	}
	list_of_solutions.append(solution)


for ii in range(len(list_of_solutions)):
	print("==> Pour le service " + str(list_of_solutions[ii]['service_intention_id']) + 
		", il y a " + str(len(list_of_solutions[ii]['train_runs_possible'])) +
		" solutions possibles.")

## TEST ALL SOLUTIONS
combinations_matrix, all_scores = test_all_solutions(list_of_solutions, problem_instance_label, problem_instance_hash,hash, scenario_content)

print("==> The best score achieved is " + str(min(all_scores)))

## Save the first solution to file
# for ii in range(len(list_of_solutions)):
# 	train_runs.append(list_of_solutions[ii]['train_runs_possible'][0])
# my_solution = {
# 	'problem_instance_label': problem_instance_label,
# 	'problem_instance_hash': problem_instance_hash,
# 	'hash': hash,
# 	'train_runs': train_runs
# }
## Save the best solution to file
my_solution = best_solution(all_scores, combinations_matrix, problem_instance_label, problem_instance_hash, hash)


file_solution = my_solution

with open("./my_solution/" +FILE_NAME, 'w') as fp:
	json.dump(file_solution, fp, indent=4)
