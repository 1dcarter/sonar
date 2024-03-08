print(r'''
 ______   ______   __   __   ______   ______    
/\  ___\ /\  __ \ /\ "-.\ \ /\  __ \ /\  == \   
\ \___  \\ \ \/\ \\ \ \-.  \\ \  __ \\ \  __<   
 \/\_____\\ \_____\\ \_\\"\_\\ \_\ \_\\ \_\ \_\ 
  \/_____/ \/_____/ \/_/ \/_/ \/_/\/_/ \/_/ /_/ 
                                               
''')
import os
import subprocess
import ipaddress
import threading
import sys
import time

def get_connected_subnets():
    subnets = []
    if os.name == 'posix':  # Linux/macOS
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        output = result.stdout
        for line in output.splitlines():
            parts = line.split()
            if 'link' in parts:
                subnet = parts[0]
                subnets.append(subnet)
    elif os.name == 'nt':  # Windows
        result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
        output = result.stdout
        for line in output.splitlines():
            if 'IPv4 Address' in line:
                subnet = line.split(':')[1].strip()
                subnets.append(subnet)
    return subnets

def ping_host(ip, result_list):
    response = subprocess.run(['ping', '-c', '1', '-W', '1', ip], capture_output=True, text=True)
    if 'ttl=' in response.stdout.lower():
        result_list.append(ip)

def scan_hosts(subnets):
    print("Sending pulse")
    reachable_hosts = []
    total_hosts = sum([len(list(ipaddress.IPv4Network(subnet, strict=False).hosts())) for subnet in subnets])
    progress_bar_width = 120
    progress_bar_increment = total_hosts // progress_bar_width
    progress_bar_count = 0

    sys.stdout.write("[%s]" % (" " * progress_bar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (progress_bar_width + 1))

    for subnet in subnets:
        network = ipaddress.IPv4Network(subnet, strict=False)
        for ip in network.hosts():
            ip = str(ip)
            ping_thread = threading.Thread(target=ping_host, args=(ip, reachable_hosts))
            ping_thread.start()
            ping_thread.join(timeout=0.1)  # Adjust timeout as needed
            progress_bar_count += 1
            if progress_bar_count % progress_bar_increment == 0:
                sys.stdout.write(")))")
                sys.stdout.flush()
    
    sys.stdout.write("\n")
    print("Pulse Complete.")
    return reachable_hosts

def run_nmap_scan(hosts):
    print("Running port scan...")
    nmap_results = []
    for host in hosts:
        print(f"Scanning {host}...")
        result = subprocess.run(['nmap', '-sV', '-A', '-O', host], capture_output=True, text=True)
        nmap_results.append((host, result.stdout))

    print("Scan completed.")
    return nmap_results

if __name__ == "__main__":
    subnets = get_connected_subnets()
    print("Connected subnets:", subnets)
    reachable_hosts = scan_hosts(subnets)

    print("\nReachable IP addresses:")
    for host in reachable_hosts:
        print(host)

    choice = input("Would you like to port scan the hosts? (yes/no): ").lower()
    if choice == "yes":
        nmap_results = run_nmap_scan(reachable_hosts)

        print("\nNmap results:")
        for host, result in nmap_results:
            print(f"\nResults for {host}:")
            print(result)

        # Write both reachable hosts and nmap results to pulse.txt
        with open('pulse.txt', 'w') as f:
            f.write("Reachable IP addresses:\n")
            for host in reachable_hosts:
                f.write(host + '\n')
            f.write("\nNmap results:\n")
            for host, result in nmap_results:
                f.write(f"\nResults for {host}:\n")
                f.write(result)
        
        print("Pulse complete, writing to pulse.txt.")
    elif choice == "no":
        print("Pulse complete, writing to pulse.txt.")
        with open('pulse.txt', 'w') as f:
            for host in reachable_hosts:
                f.write(host + '\n')
        print("Write complete.")
    else:
        print("Invalid choice. Pulse aborted.")
