import json
import subprocess
import os
import sys

def add_users_to_group(group_name, namespace):
    # Run the `oc get` command, capture the JSON output, and load the data
    oc_get_output = subprocess.run(["oc", "get", "-o", "json", "rolebinding", "edit", "-n", namespace], capture_output=True, text=True)

    # Check if the command was successful and load the JSON data
    if oc_get_output.returncode == 0:
        data = json.loads(oc_get_output.stdout)

        # Extract subjects
        subjects = data.get("subjects", [])

        try:
            # Try to get the current members of the OCP group
            oc_get_output = subprocess.run(["oc", "get", "group", group_name, "-o", "json"], capture_output=True, text=True)
            group_info = json.loads(oc_get_output.stdout)
            current_members = group_info.get("users", [])
        except json.JSONDecodeError as e:
            # Handle the case where JSON decoding fails (an empty group)
            print(f"Error decoding JSON: {e}")
            current_members = []

        # Add usernames to the OCP group if not already members
        for subject in subjects:
            username = subject.get("name")
            
            if username not in current_members:
                # Add the username to the OCP group
                subprocess.run(["oc", "adm", "groups", "add-users", group_name, username])
                print(f"Added user {username} to OCP group.")
            else:
                print(f"User {username} is already a member of OCP group.")
    else:
        # Print an error message if the command failed
        print(f"Error: {oc_get_output.stderr}")

if __name__ == "__main__":
    # Use environment variables for group name and namespace
    group_name = os.environ.get('GROUP_NAME')
    namespace = os.environ.get('NAMESPACE')

    # Check if the required environment variables are present
    if not group_name or not namespace:
        print("Error: GROUP_NAME and NAMESPACE environment variables are required.")
        sys.exit(1)

    add_users_to_group(group_name, namespace)
