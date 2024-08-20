# BU-RHOAI

This repository is a collection of useful scripts and tools for TAs and professors to manage students workloads.

## Cronjobs

### group-sync

This cronjob runs once every hours at the top of the hour, adding all users with the edit rolebinding in the specified namespace to the specified group.
This offers us a way to keep class users added to course namespaces via ColdFront in sync with the in cluster OCP course group. To run this cronjob:

1. Ensure you are logged in to your OpenShift account via the CLI and you have access to rhods-notebooks namespace.
2. Switch to your course namespace:
    ```
    oc project <namespace>
    ```

3. Update the `GROUP_NAME` and `NAMESPACE` env variables in cronjobs/group-sync/cronjob.yaml
4. From cronjobs/group-sync/ directory run:
    ```
    oc apply -k . --as system:admin
    ```

This will deploy all the necessary resources for the cronjob to run on the specified schedule.(Every hour by default)

Alternatively, to run the script immediately:

1. Ensure you followed the steps above
2. Verify the cronjob `group-sync` exists
    ```
    oc get cronjob group-sync
    ```

3. Run:
    ```
    kubectl create -n rhods-notebooks job --from=cronjob/group-sync group-sync
    ```

### nb-culler

This cronjob runs once every hours at the top of the hour, exclusively applied to notebooks associated with specific user group  and will not impact other notebooks within the rhods-notebooks namespace. The cronjob performs the following actions:

1. **Shuts down notebooks exceeding X hours of runtime**: any notebook found to have been running for more than X hours will be gracefully shut down to conserve resources. PVCs persist the shutdown process.
2. **Deletes notebooks with wrong images**: students are allowed to launch notebook instances with their class image. Notebooks that are running images that are not approved for use will be deleted along with their associated PVCs.
3. **Deletes notebooks with wrong container size**: notebooks that are configured with container sizes other than **X Small** will be deleted, including their PVCs.

To add resources to the rhods-notebooks namespace:

1. Ensure you are logged in to your OpenShift account via the CLI and you have access to rhods-notebooks namespace.
2. Switch to rhods-notebooks namespace:
    ```
    oc project rhods-notebooks
    ```

3. Ensure the environment variables for `GROUP_NAME`, `CUTOFF_TIME` (seconds), `IMAGE_NAME` are correctly set.

4. From cronjobs/nb-culler/ directory run:
    ```
    oc apply -k . --as system:admin
    ```

This will deploy all the necessary resources for the cronjob to run on the specified schedule.

Alternatively, to run the script immediately:

1. Ensure you followed the steps above
2. Verify the cronjob `nb-culler` exists
    ```
    oc get cronjob nb-culler
    ```

3. Run:
    ```
    kubectl create -n rhods-notebooks job --from=cronjob/nb-culler nb-culler
    ```

This will trigger the cronjob to spawn a job manually.


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
