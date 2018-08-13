import os, inspect
import json
import pandas as pd
import datetime
import isodate

from route_graph import *
# import utils.translate as translate
# from utils.validate_solution import *


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
def compute_time(old_time, next_section):
	exit = datetime.datetime.strptime(old_time['exit_time'], "%H:%M:%S") + \
	 isodate.parse_duration(next_section['minimum_running_time'])
	
	time = {
		"entry_time": datetime.datetime.strptime(old_time['exit_time'], "%H:%M:%S").strftime("%H:%M:%S"),
		"exit_time": exit.strftime("%H:%M:%S")
	}
	return time

## Upload le scenario
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
scenario = os.path.join(currentdir,'sample_files',"sample_scenario.json")

with open(scenario) as fp:
	scenario_content = json.load(fp)

nb_routes = len(scenario_content['routes'])

## Extraction des paramètres globaux du scenario
problem_instance_label = scenario_content['label']
problem_instance_hash = scenario_content['hash']
hash = 42
train_runs = []
nb_of_trains = len(scenario_content['service_intentions'])

## Boucle pour chaque train du scenario
for k in range(nb_of_trains):
	train = scenario_content['service_intentions'][k]
	service_intention_id = train['id']

	## Initialise les listes qui construiront la solution finale 
	train_run_sections = []
	sections = []
	time = []
	print("#################################")
	print("service_intention_id ::: " + str(service_intention_id))
	

	#################################
	##### IMPLEMENT SOLUTION ########
	#################################

	## Extrait les requirements de la première section du scenario
	for j in range(len(train['section_requirements']) ):
		if train['section_requirements'][j]['sequence_number'] == 1:
			start_section = train['section_requirements'][j]

	departs_possibles = []
	intersections = {}

	## Extrait la route correspondant au scenario
	for route in scenario_content['routes']:
		if route['id'] == service_intention_id:
			selected_route = route 

	## Loop à travers les sections de cette route
	for path in selected_route["route_paths"]:
		for (i, route_section) in enumerate(path["route_sections"]):
			sn = route_section['sequence_number']

			## Est-ce que cette section est un départ ?
			if from_node_id(path, route_section, i)[-10:] == 'beginning)':
				departs_possibles.append(route_section)

			## Est-ce que cette section est suivi d'une intersection ? 
			################ VERIFIER CE CODE #######################
			# from_node ou to_node ?
			elif from_node_id(path, route_section, i)[:2] == '(M':
				if str(from_node_id(path, route_section, i)[1:-1]) not in intersections.keys():
					intersections[str(from_node_id(path, route_section, i)[1:-1])] = []

				intersections[str(from_node_id(path, route_section, i)[1:-1])].append(route_section)
			#########################################################

	## Choisir le meilleurs depart
	for ii in range(len(departs_possibles)):
		# Verifier aue c'est le bon section marker (A, B, ...)
		if departs_possibles[ii]['section_marker'][0] != start_section['section_marker']:
			print("Ce n'est pas le bon section_marker pour le point de depart !! ")
			del departs_possibles[ii]

	## Prendre le trajet le plus rapide
	selected_depart = le_plus_court(departs_possibles)

	## Ajouter la section selectionnée à la liste
	sections.append(selected_depart)

	## Ajouter les temps d'arrivée et de sortie de la gare
	################ VERIFIER CE CODE #######################
	# Pour la première le entry et exit devrait être le même en fait....
	exit = datetime.datetime.strptime(start_section['entry_earliest'], "%H:%M:%S") +  \
	isodate.parse_duration(selected_depart['minimum_running_time'])
	time.append({
		"entry_time": start_section['entry_earliest'],
		"exit_time": exit.strftime("%H:%M:%S")
	})
	#########################################################

	## Loop pour les sections suivantes
	done = False
	while not done:
		## La dernière section selectionnée
		current_section = sections[len(sections)-1]

		## Est ce  que c'est section mène à une intersection ?
		if "route_alternative_marker_at_exit" in current_section.keys() and \
				route_section["route_alternative_marker_at_exit"] is not None:
			possible_paths= intersections[route_section["route_alternative_marker_at_exit"][0]]
			
			if len(possible_paths) > 0:
				# On choisit le temps de trajet le plus court
				next_section = le_plus_court(possible_paths)
			else:
				# Il n'y a qu'un choix possible et pis c'est tout
				next_section = possible_paths

			## Ajouter la section selectionnée à la liste
			sections.append(next_section)

			## Ajouter les temps d'arrivée et de sortie de la gare
			new_time = compute_time(time[len(time)-1], next_section)
			time.append(new_time)
			print(next_section)

		else:
			################ CODER LA PARTIE OU IL N'Y A PAS D'INTERSECTION #######################
			done = True
			#######################################################################################
		
	
	## On fait un joli dict pour chaque section
	idx = 0
	for section in sections:
		sol = {
			"entry_time": time[idx]["entry_time"],
			"exit_time": time[idx]["exit_time"],
			"route": service_intention_id,
			"route_section_id": str(service_intention_id) +"#"+str(section["sequence_number"]),
			"sequence_number": section["sequence_number"],
			"route_path": 3,
			"section_requirement": section["section_marker"]
		}

		
		train_run_sections.append(sol)

		# on ajoute le joli dict à la liste
		result = {'service_intention_id': service_intention_id, 'train_run_sections': train_run_sections}
		train_runs.append(result)
		idx += 1

# le json final ! Ouhouuu !
my_solution = {
	'problem_instance_label': problem_instance_label,
	'problem_instance_hash': problem_instance_hash,
	'hash': hash,
	'train_runs': train_runs
}

# enregistré !!
with open('my_solution.json', 'w') as fp:
	json.dump(my_solution, fp, indent=4)

################ ADAPTER VALIDATE_SOLUTION DE UTILS #######################
###########################################################################