#!/usr/bin/env python
"""
Example script showing how to get shots from runmanager remote server.

The shots are returned as a list of dictionaries, each dictionary containing
the values of each variable for that shot.
"""

import runmanager.remote

def main():
    # Create a client connection to the remote runmanager server
    client = runmanager.remote.Client()
    
    # Say hello to verify connection
    print("Connecting to runmanager server...")
    response = client.say_hello()
    print(f"Server response: {response}\n")
    
    # Get the number of shots
    n = client.n_shots()
    print(f"Number of shots: {n}\n")
    
    # Get all shots as a list of dictionaries
    shots = client.get_shots()
    
    print("Shots:")
    for i, shot in enumerate(shots):
        print(f"\nShot {i+1}:")
        for variable_name, value in shot.items():
            print(f"  {variable_name}: {value}")

if __name__ == '__main__':
    main()
