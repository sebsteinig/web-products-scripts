#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime

def load_history():
    """Load deployment history from JSON file."""
    try:
        with open('deployment_history.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("No deployment history found")
        return []

def list_all_deployments(history):
    """List all deployments ordered by deployment date."""
    print("\nAll Deployments:")
    print("-" * 80)
    for d in history:
        print(f"Version: {d['version']}")
        print(f"Environment: {d['environment']}")
        print(f"Deployed by: {d['deployed_by']}")
        print(f"Deployed at: {d['deployed_at']}")
        print(f"Commit: {d['commit']}")
        print("-" * 80)

def list_production_deployments(history):
    """List only production deployments."""
    prod_deployments = [d for d in history if d['environment'] == 'production']
    print("\nProduction Deployments:")
    print("-" * 80)
    for d in prod_deployments:
        print(f"Version: {d['version']}")
        print(f"Deployed by: {d['deployed_by']}")
        print(f"Deployed at: {d['deployed_at']}")
        print(f"Commit: {d['commit']}")
        print("-" * 80)

def get_current_production_version(history):
    """Get the latest production deployment."""
    prod_deployments = [d for d in history if d['environment'] == 'production']
    if prod_deployments:
        d = prod_deployments[0]  # First one is most recent
        print("\nCurrent Production Version:")
        print("-" * 80)
        print(f"Version: {d['version']}")
        print(f"Deployed by: {d['deployed_by']}")
        print(f"Deployed at: {d['deployed_at']}")
        print(f"Commit: {d['commit']}")
        print("-" * 80)
    else:
        print("\nNo production deployments found")

def get_version_history(history, version):
    """Get deployment history for a specific version."""
    version_deployments = [d for d in history if d['version'] == version]
    print(f"\nDeployment History for Version {version}:")
    print("-" * 80)
    if version_deployments:
        for d in version_deployments:
            print(f"Environment: {d['environment']}")
            print(f"Deployed by: {d['deployed_by']}")
            print(f"Deployed at: {d['deployed_at']}")
            print(f"Commit: {d['commit']}")
            print("-" * 80)
    else:
        print(f"No deployments found for version {version}")

def get_user_deployments(history, username):
    """Get deployment history for a specific user."""
    user_deployments = [d for d in history if d['deployed_by'] == username]
    print(f"\nDeployments by {username}:")
    print("-" * 80)
    if user_deployments:
        for d in user_deployments:
            print(f"Version: {d['version']}")
            print(f"Environment: {d['environment']}")
            print(f"Deployed at: {d['deployed_at']}")
            print(f"Commit: {d['commit']}")
            print("-" * 80)
    else:
        print(f"No deployments found for user {username}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  list_deployments.py all              - List all deployments")
        print("  list_deployments.py prod             - List production deployments")
        print("  list_deployments.py current          - Show current production version")
        print("  list_deployments.py version v1.0.0   - Show history for specific version")
        print("  list_deployments.py user username    - Show deployments by specific user")
        sys.exit(1)

    history = load_history()
    command = sys.argv[1]

    if command == "all":
        list_all_deployments(history)
    elif command == "prod":
        list_production_deployments(history)
    elif command == "current":
        get_current_production_version(history)
    elif command == "version" and len(sys.argv) == 3:
        get_version_history(history, sys.argv[2])
    elif command == "user" and len(sys.argv) == 3:
        get_user_deployments(history, sys.argv[2])
    else:
        print("Invalid command. Use --help for usage information.")

if __name__ == "__main__":
    main() 