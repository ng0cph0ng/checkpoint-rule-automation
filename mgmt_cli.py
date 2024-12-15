import csv

# Function to modify the last octet of an IP address
def modify_network_address(network):
    parts = network.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)

# Input the network card interface name from the user
card_interface = input("Enter the network card interface name: ")

# Read the CSV file
with open('input.csv', mode='r') as file:
    csv_reader = csv.DictReader(file)
    
    # Initialize the position value
    pos = int(input("Enter the position to create rules: "))
    
    # Header part of the script
    script_header = """#!/bin/bash

LOGIN="admin"
PASSWORD="qwer1234"

mgmt_cli login user "$LOGIN" password "$PASSWORD"> id.txt
"""

    # Footer part of the script
    script_footer = """
GWUID=$(mgmt_cli -s id.txt show simple-gateway name "CP_Ph0ng" --format json | jq ' . "uid" ')
mgmt_cli get-interfaces target-uid $GWUID with-topology true use-defined-by-routes false -u $LOGIN -p $PASSWORD

mgmt_cli -s id.txt publish
mgmt_cli -s id.txt logout
"""

    # Create a list to store the parts of the script
    script_parts = [script_header]
    
    # Loop through each row in the CSV file
    for row in csv_reader:
        layer = row['Layer']
        network = row['Network']
        ip = modify_network_address(row['Network'])
        mask_length = row['Mask-length']
        vlan = row['Vlan']
        
        # Create a script for each row
        script = f"""
mgmt_cli -s id.txt add network name "NET-{network}-{mask_length}" subnet "{network}" mask-length "{mask_length}" set-if-exists true ignore-warnings true
mgmt_cli -s id.txt add access-layer name "{layer}-Inbound"
mgmt_cli -s id.txt add access-layer name "{layer}-Outbound"
mgmt_cli -s id.txt add access-rule layer "Network" position {pos} name "{layer}-Inbound" service "Any" source "NET-{network}-{mask_length}" destination "Any" action "Apply Layer" inline-layer "{layer}-Inbound"
mgmt_cli -s id.txt add access-rule layer "Network" position {pos + 1} name "{layer}-Outbound" service "Any" source "Any" destination "NET-{network}-{mask_length}" action "Apply Layer" inline-layer "{layer}-Outbound"
mgmt_cli add vlan-interface id {vlan} parent {card_interface} --version 1.6 --context gaia_api -u $LOGIN -p $PASSWORD
mgmt_cli set vlan-interface name {card_interface}.{vlan} ipv4-address {ip} ipv4-mask-length {mask_length} enabled True --version 1.6 --context gaia_api -u $LOGIN -p $PASSWORD
"""
        
        # Add the script to the list
        script_parts.append(script.strip())
        
        # Add an empty line between the blocks
        script_parts.append("")
        
        # Increment the position value
        pos += 2
    
    # Add the footer part to the list
    script_parts.append(script_footer.strip())
    
    # Combine all parts together
    full_script = "\n".join(script_parts)
    
    # Write the result to an output file
    with open('mgmt_cli.txt', mode='w') as output_file:
        output_file.write(full_script)