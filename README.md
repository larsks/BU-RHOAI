# BU-RHOAI

This repository is a collection of useful scripts and tools for TAs and professors to manage students workloads.

## Cronjobs

### group-sync

This cronjob runs once every hour hours at the top of the hour, adding all users with the edit rolebinding in the specified namespace to the specified group. 
This offers us a way to keep class users added to course namespaces via ColdFront in sync with the in cluster OCP course group. To run this cronjob:

1. Ensure you are logged in to your OpenShift account via the CLI and you have access to rhods-notebooks namespace.
2. Switch to your course namespace:
```
	oc project <namespace>
```

3. Update the group_name and namespace env variables in cronjobs/group-sync/cronjob.yaml
4. From cronjobs/group-sync/ directory run:
```
	oc apply -k .
```

	This will deploy all the necessary resources for the cronjob to run on the specified schedule.(Every hour by default)

Alternatively, to run the script immediately: 

1. Ensure you followed the steps above
2. Verify the cronjob ope-notebook-culler exists
```
	oc get cronjob group-sync
```

3. Run:
```
	kubectl create -n rhods-notebooks job --from=cronjob/group-sync group-sync
```

## Scripts

### get_url.py

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