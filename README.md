# BU-RHOAI

This repository is a collection of useful scripts and tools for TAs and professors to manage students workloads.

## get_url.py

This script is used to retrieve the URL for a particular notebook associated with one student. To execute this script:

1. Ensure you are logged in to your OpenShift account via the CLI and you have access to rhods-notebooks namespace.
2. TAs can list all notebooks under rhods-notebooks namespace via the CLI
	```
	oc get notebooks -n rhods-notebooks
	```
3. Before running this script, ensure that pyyaml is installed in your Python environment:
	```
	pip install pyyaml
	```
4. Run the script:
	```
	python get_url.py
	```
	It prompts the user to enter the notebook name. Output will look something like:
	```
	Enter the notebook name: xxx
	URL for notebook xxx: xxx
	```