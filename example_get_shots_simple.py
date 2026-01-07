#!/usr/bin/env python
"""
Simple example using the module-level API to get shots from runmanager.

This is the simplest way to interact with the runmanager remote server.
"""

from runmanager.remote import get_shots, n_shots, say_hello

def main():
    # Verify connection
    print("Connecting to runmanager server...")
    response = say_hello()
    print(f"Server response: {response}\n")
    
    # Get the number of shots
    print(f"Number of shots: {n_shots()}\n")
    
    # Get all shots as a list of dictionaries
    shots = get_shots()
    
    print("All shots:")
    for i, shot in enumerate(shots, 1):
        print(f"\nShot {i}:")
        for variable_name, value in shot.items():
            print(f"  {variable_name}: {value}")

if __name__ == '__main__':
    main()
