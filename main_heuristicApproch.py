import os, inspect
import json
import pandas as pd
import datetime
import isodate
import numpy as np
import random

from route_graph import *
from validate_solution import *

import itertools

# from algo1 import *
# 
# FILE_NAME = "01_dummy.json"
# FILE_NAME = "01_dummy.json"
# FILE_NAME = "02_a_little_less_dummy.json"
# FILE_LIST = ["01_dummy.json", "02_a_little_less_dummy.json", "03_FWA_0.125.json"]
FILE_LIST = ["02_a_little_less_dummy.json"]
REPEAT_STEP = 5
# FILE_LIST = ["04_V1.02_FWA_without_obstruction.json", "05_V1.02_FWA_with_obstruction.json"]

# FILE_NAME = "03_FWA_0.125.json"
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


RESET_LIST = []
def convert_duree(time):
	return isodate.parse_duration(time)
def convert_time(time):
	return datetime.datetime.strptime(time, "%H:%M:%S")
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

def format_solution_file(scenario, solution, problem_instance_label, problem_instance_hash, hash):
	d_list = []
	for i in range(len(solution)):
		train_run_sections = []
		for j in range(len(solution[i])):
			for k in range(len(scenario["service_intentions"])):
				if (scenario["service_intentions"][k]["id"] == solution[i][j]['service_intention_id']):
					section_requirements = scenario["service_intentions"][k]["section_requirements"]
			
			marker_to_go = []
			for r in section_requirements :
				marker_to_go.append(r["section_marker"])

			try :
				marker = solution[i][j]["section_marker"][0]
				if marker not in marker_to_go:
					marker = None
			except:
				marker = None

			tmp = {
			"entry_time": solution[i][j]["entry_time"].strftime("%H:%M:%S"),
			"exit_time": solution[i][j]["exit_time"].strftime("%H:%M:%S"),
			"route": solution[i][j]['service_intention_id'],
			"route_section_id": str(solution[i][j]['service_intention_id']) +"#"+str(solution[i][j]["sequence_number"]),
			"sequence_number": j+1,
			"route_path": solution[i][j]["route_id"],
			"section_requirement": marker,
			}
			train_run_sections.append(tmp)

		d = {
			"service_intention_id": solution[i][0]['service_intention_id'],
			"train_run_sections": train_run_sections
		}
		d_list.append(d)

	result = {
	"problem_instance_label": problem_instance_label,
	"problem_instance_hash": problem_instance_hash,
	"hash": hash,
	"train_runs": d_list
	}
	return result

def test_all_solutions(list_of_solutions, scenario_content):
	all_scores = []
	for i in range(len(list_of_solutions)):
		# validation_result = do_loesung_validation(scenario_content, list_of_solutions[i])

		score = objective_function(scenario_content, list_of_solutions[i])
		all_scores.append(score)
		print("THE SCORE IS :" + str(score))

		return all_scores


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

def reset_time_from_step(solution, train, from_step):
	for step in range(from_step, len(solution[train])):
		if step == 0:
			solution[train][0]['entry_time'] = solution[train][0]['entry_earliest']
		else:
			solution[train][step]['entry_time'] = solution[train][step-1]['exit_time']

		solution[train][step]['exit_time'] = solution[train][step]['entry_time'] +  solution[train][step]['minimum_running_time']
		## First check if there are any time requirement 
		if solution[train][step]['entry_latest'] != None:
			if solution[train][step]['entry_time'] > solution[train][step]['entry_latest']:
				# print("This solution is not feasible (1).")
				return reset_time(solution, train)

		if solution[train][step]['entry_earliest'] != None:
			if solution[train][step]['entry_time'] < solution[train][step]['entry_earliest']:
				solution[train][step-1]['exit_time'] = solution[train][step]['entry_earliest']
				solution[train][step]['entry_time'] = solution[train][step]['entry_earliest']

		if solution[train][step]['min_stopping_time'] != None:
			if (solution[train][step]['exit_time'] - (solution[train][step]['entry_time']+  solution[train][step]['minimum_running_time'])) < solution[train][step]['min_stopping_time']:
				solution[train][step]['exit_time'] = solution[train][step]['entry_time'] +  solution[train][step]['minimum_running_time'] + solution[train][step]['min_stopping_time']

		if solution[train][step]['exit_earliest'] != None:
			if solution[train][step]['exit_time'] < solution[train][step]['exit_earliest']:
				solution[train][step]['exit_time'] = solution[train][step]['exit_earliest']
				# print("This solution is not feasible (2).")

		# if solution[train][step]['exit_latest'] != None:
		# 	if solution[train][step]['exit_time'] > solution[train][step]['exit_latest']:
				# print("This solution is not feasible (2).")

	return solution

def reset_time(solution, train):
	
	for step in range(len(solution[train])):
		if step == 0:
			solution[train][0]['entry_time'] = solution[train][0]['entry_earliest']
		else:
			solution[train][step]['entry_time'] = solution[train][step-1]['exit_time']

		solution[train][step]['exit_time'] = solution[train][step]['entry_time'] +  solution[train][step]['minimum_running_time']
		## First check if there are any time requirement 
		if solution[train][step]['entry_latest'] != None:
			if solution[train][step]['entry_time'] > solution[train][step]['entry_latest']:
				print("This solution is not feasible (1).")

		if solution[train][step]['entry_earliest'] != None:
			if solution[train][step]['entry_time'] < solution[train][step]['entry_earliest']:
				solution[train][step-1]['exit_time'] = solution[train][step]['entry_earliest']
				solution[train][step]['entry_time'] = solution[train][step]['entry_earliest']

		if solution[train][step]['min_stopping_time'] != None:
			if (solution[train][step]['exit_time'] - (solution[train][step]['entry_time']+  solution[train][step]['minimum_running_time'])) < solution[train][step]['min_stopping_time']:
				solution[train][step]['exit_time'] = solution[train][step]['entry_time'] +  solution[train][step]['minimum_running_time'] + solution[train][step]['min_stopping_time']

		if solution[train][step]['exit_earliest'] != None:
			if solution[train][step]['exit_time'] < solution[train][step]['exit_earliest']:
				solution[train][step]['exit_time'] = solution[train][step]['exit_earliest']
				# print("This solution is not feasible (2).")

		if solution[train][step]['exit_latest'] != None:
			if solution[train][step]['exit_time'] > solution[train][step]['exit_latest']:
				print("This solution is not feasible (3).")

	return solution

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

def update_time(selected_solution, train_idx, step, field_modified, permit_reset):
	if step != 0:
		if (selected_solution[train_idx][step]['entry_time']) > selected_solution[train_idx][step-1]['exit_time']:
			if (selected_solution[train_idx][step-1]['exit_latest'] is None) or ((selected_solution[train_idx][step-1]['exit_latest'] is not None) and \
						 (selected_solution[train_idx][step]['entry_time'] < selected_solution[train_idx][step-1]['exit_latest'])):
				selected_solution[train_idx][step-1]['exit_time'] = selected_solution[train_idx][step]['entry_time']
				selected_solution = reset_time_from_step(selected_solution, train_idx, step)
			else:
				# print("Le train ne peut pas partir plus tard de la gare précédente. Il est reset.")
				if (permit_reset):
					selected_solution = reset_time(selected_solution, train_idx)
		else:
			print("Le changement d'horaire a avancé le train au lieu de le retarder ...")
	else:
		selected_solution = reset_time_from_step(selected_solution, train_idx, step+1)

	return selected_solution

def train_must_wait(selected_solution, train_waiting, step_for_waiting, wait_time, permit_reset):

	if (selected_solution[train_waiting][step_for_waiting]['exit_latest'] is None):
		# print("SOLUTION SIMPLE")
		
		selected_solution[train_waiting][step_for_waiting]['entry_time'] = wait_time 
		selected_solution = update_time(selected_solution, train_waiting, step_for_waiting, 'entry_time', permit_reset)
	elif( (selected_solution[train_waiting][step_for_waiting]['exit_latest'] is not None) and \
			(wait_time < selected_solution[train_waiting][step_for_waiting]['exit_latest'])):
		# print("SOLUTION PRESQUE AUSSI SIMPLE")
		selected_solution[train_waiting][step_for_waiting]['entry_time'] = wait_time 
		selected_solution = update_time(selected_solution, train_idx[idx], step_for_waiting, 'entry_time', permit_reset)
		
	else:
		print("Ooooh non pas de solution")

	return selected_solution

def generate_solutions(scenario_content):

	nb_of_trains = len(scenario_content['service_intentions'])

	print("==> Il y a " + str(nb_of_trains) + " services différents à proposer.")

	print("Je génère les solutions possibles ...")
	list_of_solutions = []
	for k in range(nb_of_trains):
		train = scenario_content['service_intentions'][k]
		service_intention_id = train['id']
		start_section = train["section_requirements"][0]
		train_runs_possible = []

		## Extrait la route correspondant au scenario
		for route in scenario_content['routes']:
			if route['id'] == service_intention_id:
				selected_route = route 
		
		the_route_net = generate_paths_dict(selected_route["route_paths"])
		## Liste tous les chemins possibles
		paths = []
		for node in the_route_net:
			myDFS(the_route_net,node,False,paths)
		final_paths = []
		for path in paths:
			if path[0][-9:] == 'beginning':
				final_paths.append(path)

		final_paths = convert_paths(final_paths, the_route_net)

		for chemin in final_paths:
			train_run_sections = []
			sections = []
			time = []
			raw_sol = []
			for (idx, seq_nb) in enumerate(chemin):
				section = extract_section(selected_route, seq_nb)

				if section == None:
					print("Ce chemin n'existe pas !")
					break

				section_requirements = None

				if ("section_marker" in section.keys()) and( len(section["section_marker"]) > 0):
					for r in train["section_requirements"]:
						if r["section_marker"] == section["section_marker"][0]:
							section_requirements = r

				section_marker = None
				resource_occupations = None
				entry_latest = None
				entry_earliest = None
				min_stopping_time = None
				exit_earliest = None
				exit_latest = None

				if section_requirements != None:
					if "entry_earliest" in section_requirements.keys():
						entry_earliest = datetime.datetime.strptime(section_requirements["entry_earliest"], "%H:%M:%S")
					if "entry_latest" in section_requirements.keys():
						entry_latest = datetime.datetime.strptime(section_requirements["entry_latest"], "%H:%M:%S")
					if "min_stopping_time" in section_requirements.keys():
						min_stopping_time = isodate.parse_duration(section_requirements['min_stopping_time'])
					if "exit_earliest" in section_requirements.keys():
						exit_earliest = datetime.datetime.strptime(section_requirements["exit_earliest"], "%H:%M:%S")
					if "exit_latest" in section_requirements.keys():
						exit_latest = datetime.datetime.strptime(section_requirements["exit_latest"], "%H:%M:%S")

				if ('resource_occupations' in section) and (len(section['resource_occupations']) > 0):  
					resource_occupations = [elem['resource'] for elem in section['resource_occupations']]
				if ('section_marker' in section) and (len(section['section_marker']) > 0):  
					section_marker = section['section_marker']
				
				sol = {
				'service_intention_id': service_intention_id,
				'route_id': section["id"],
				'sequence_number': section['sequence_number'],
				'section_marker': section_marker,
				'entry_time': None,
				'exit_time': None,
				'resource_occupations': resource_occupations,
				'penalty':section['penalty'],
				'minimum_running_time': convert_duree(section['minimum_running_time']),
				'entry_earliest': entry_earliest,
				'entry_latest': entry_latest,
				'min_stopping_time': min_stopping_time,
				'exit_earliest': exit_earliest,
				'exit_latest': exit_latest
				}
				raw_sol.append(sol)						sections.append(section)
			train_runs_possible.append(raw_sol)
		list_of_solutions.append(train_runs_possible)
	return list_of_solutions

def generate_combinations_matrix(list_of_solutions):
	combinations = [[] for i in range(len(list_of_solutions))]
	for i in range(len(combinations)):
		for j in range(len(list_of_solutions[ii])):
			combinations[i].append(j)
	combinations_matrix = list(itertools.product(*combinations))
	return combinations_matrix

def resource_conflict_algorithm(selected_solution):

	longueur_chemins = [len(elem) for elem in selected_solution]
	max_steps = max(longueur_chemins)

	
	index_repeat = 0
	done = False
	nb_of_conflicts = 0

	while (not done):
	# for index_repeat in range(2):
		print(done)
		index_repeat += 1
		done = True	
		print("#############################################################")
		print("ITERATION " + str(index_repeat))

		permit_reset = True
		if index_repeat > (REPEAT_STEP):
			permit_reset = False

		for i in range(max_steps):
			# print("STEP ::: " + str(i))

			train_idx = [elem for elem in range(len(selected_solution)) if len(selected_solution[elem]) > i]
			random.shuffle(train_idx)
			for j in range(len(train_idx)):
				if len(selected_solution[train_idx[j]]) > i:
					other_train_resource = []
					for k in range(len(train_idx)):
						if k != j:
							if (len(selected_solution[train_idx[k]]) > i) and (selected_solution[train_idx[k]][i]['resource_occupations'] is not None):
								other_train_resource.append(selected_solution[train_idx[k]][i]['resource_occupations'])
							else:
								other_train_resource.append([])
						else:
							other_train_resource.append([])
					if selected_solution[train_idx[j]][i]['resource_occupations'] is not None:
						for k in range(len(selected_solution[train_idx[j]][i]['resource_occupations'])):
							train_resource = selected_solution[train_idx[j]][i]['resource_occupations'][k]

							for idx in range(len(train_idx)):
								if train_idx[j] != train_idx[idx]:
									for s in range(len(selected_solution[train_idx[idx]])) :
										if train_resource in selected_solution[train_idx[idx]][s]['resource_occupations']:
											step_for_other_train = s
											for r in resources:
													if r['id'] == train_resource:
														release_time = r['release_time']

											if selected_solution[train_idx[j]][i]['entry_time'] < selected_solution[train_idx[idx]][step_for_other_train]['entry_time']:
												wait_time = selected_solution[train_idx[j]][i]['exit_time'] + convert_duree(release_time)


												if (wait_time > selected_solution[train_idx[idx]][step_for_other_train]['entry_time']):
													nb_of_conflicts +=1
													done = False
													selected_solution = train_must_wait(selected_solution, train_idx[idx], step_for_other_train, wait_time, permit_reset)


											else:
												
												wait_time = selected_solution[train_idx[idx]][step_for_other_train]['exit_time'] + convert_duree(release_time)

												if(wait_time > selected_solution[train_idx[j]][i]['entry_time']) :
													nb_of_conflicts +=1
													done = False
													selected_solution = train_must_wait(selected_solution, train_idx[j], i, wait_time, permit_reset)


		print("Conflicts : " + str(nb_of_conflicts))
		nb_of_conflicts = 0
	return selected_solution

for FILE_NAME in FILE_LIST:
	print("Je télécharge le scenario.")
	scenario = os.path.join(currentdir,'problem_instances',FILE_NAME)
	with open(scenario) as fp:
		scenario_content = json.load(fp)

	resources = scenario_content['resources']

	## Extraction des paramètres globaux du scenario
	problem_instance_label = scenario_content['label']
	problem_instance_hash = scenario_content['hash']
	hash = -516528637
	train_runs = []



	list_of_solutions = generate_solutions(scenario_content)

	for ii in range(len(list_of_solutions)):
		print("==> Pour le service " + str(list_of_solutions[ii][0][0]['service_intention_id']) + 
			", il y a " + str(len(list_of_solutions[ii])) +
			" solutions possibles.")



	combinations_matrix = generate_combinations_matrix(list_of_solutions)

	print("Ce qui fait un total de " + str(len(combinations_matrix)) + " combinaison(s) possible(s).")

	for i in range(len(combinations_matrix)):
			solution_tested = combinations_matrix[i]

	list_of_file_solutions = []
	for i in range(len(combinations_matrix)):
		selected_solution_idx = combinations_matrix[i]
		selected_solution = []
		## Save the first solution to file
		for ii in range(len(list_of_solutions)):
			selected_solution.append(list_of_solutions[ii][selected_solution_idx[ii]])

		for train_idx in range(len(selected_solution)):
			selected_solution = reset_time(selected_solution, train_idx)

		print("Il y a " + str(len(selected_solution)) + " services (trains) à planifier.")

		selected_solution = resource_conflict_algorithm(selected_solution)

		file_solution = format_solution_file(scenario_content, selected_solution, problem_instance_label, problem_instance_hash, hash)
		list_of_file_solutions.append(file_solution)

	all_scores = test_all_solutions(list_of_file_solutions, scenario_content)

	print("==> The best score achieved is " + str(min(all_scores)))
	idx = all_scores.index(min(all_scores))
	my_solution = list_of_file_solutions[idx]
	# my_solution = best_solution(all_scores, combinations_matrix, problem_instance_label, problem_instance_hash, hash)

	with open("./my_solution/" +FILE_NAME, 'w') as fp:
		json.dump(my_solution, fp, indent=4)

