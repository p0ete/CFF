import os, inspect
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# os.path.join(currentdir,'my_solution', file)

submission = []
for file in os.listdir("./my_solution"):
	print(file)
	with open(os.path.join(currentdir,'my_solution', file)) as fp:
		solution_tmp = json.load(fp)
	submission.append(solution_tmp)


with open("my_submission.json", 'w') as fp:
	json.dump(submission, fp, indent=4)
