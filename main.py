import os, inspect
import json
import pandas as pd
import datetime
import isodate

from route_graph import *

## Depth First Search algorithm (pour trouver tous les paths possibles dans le réseau) 
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
				print("The entry time of the train in station " + str(section_requirements["section_marker"]) + " is to late.")
				pass
			else:
				print("The entry_latest requirement is respected.")

		if "entry_earliest" in section_requirements.keys():
			entry_earliest = datetime.datetime.strptime(section_requirements["entry_earliest"], "%H:%M:%S")
			if entry_time < entry_earliest:
				print("The entry time of the train in station " + str(section_requirements["section_marker"]) + " is to early.")
				pass
			else:
				print("The entry_earliest requirement is respected.")

		if "min_stopping_time" in section_requirements.keys():
			exit_time += isodate.parse_duration(section_requirements['min_stopping_time'])
			print("The min_stopping_time of the train in station " + str(section_requirements["section_marker"]) + " is respected.")


		if "exit_earliest" in section_requirements.keys():
			exit_earliest = datetime.datetime.strptime(section_requirements["exit_earliest"], "%H:%M:%S")
			if exit_time < exit_earliest:
				exit_time = exit_earliest
			print("The exit_earliest of the train in station " + str(section_requirements["section_marker"]) + " is respected.")


		if "exit_latest" in section_requirements.keys():
			exit_latest = datetime.datetime.strptime(section_requirements["exit_latest"], "%H:%M:%S")
			if exit_time > exit_latest:
				print("The exit_latest in station " + str(section_requirements["section_marker"]) + " cannot be respected.")
				pass
			else:
				print("The exit_latest in station " + str(section_requirements["section_marker"]) + " is respected.")

	time = {
		"entry_time": entry_time.strftime("%H:%M:%S"),
		"exit_time": exit_time.strftime("%H:%M:%S")
	}

	return time

## Représente le réseau de noeuds sous la forme d'un dict
def generate_paths_dict(scenario_content):
	result = {}
	for route in scenario_content["routes"]:
		for path in route["route_paths"]:
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
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
scenario = os.path.join(currentdir,'sample_files',"sample_scenario.json")
with open(scenario) as fp:
	scenario_content = json.load(fp)

print("Je créé le réseau de routes et je liste les chemins possibles.")
## Créé le réseau de routes
the_route_net = generate_paths_dict(scenario_content)

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

	for chemin in final_paths:
		print("Chemin testé : "+str(chemin))
		## Initialise les listes qui construiront la solution finale 
		train_run_sections = []
		sections = []
		time = []
		for (idx, seq_nb) in enumerate(chemin):
			section = extract_section(selected_route, seq_nb)

			if idx == 0 :
				if "entry_earliest" not in start_section.keys():
					print("Je ne connais pas l'heure du départ pour la première séquence.")
				else:
					exit = datetime.datetime.strptime(start_section['entry_earliest'], "%H:%M:%S") +  \
					isodate.parse_duration(section['minimum_running_time'])
					new_time = {
						"entry_time": start_section['entry_earliest'],
						"exit_time": exit.strftime("%H:%M:%S")
					}
			else:
				section_requirements = None
				if "section_marker" in section.keys():
					for r in train["section_requirements"]:
						if r["section_marker"] == section["section_marker"][0]:
							section_requirements = r

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

## On prends une solutions parmis les solutioons possibles pour chaque service_intention_id
train_runs= [list_of_solutions[0]['train_runs_possible'][3],\
	list_of_solutions[1]['train_runs_possible'][3]]
	
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
