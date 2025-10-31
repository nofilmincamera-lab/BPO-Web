#!/usr/bin/env python3
"""
Docker Network Management for BPO Project
"""
import subprocess
import json
import sys
from typing import Dict, List

class DockerNetworkManager:
    def __init__(self):
        self.networks = {
            "bpo-main-network": {
                "subnet": "172.30.0.0/16",
                "ip_range": "172.30.240.0/20",
                "gateway": "172.30.0.1",
                "description": "Main BPO network for all services"
            },
            "bpo-gpu-network": {
                "subnet": "172.31.0.0/16",
                "ip_range": "172.31.240.0/20",
                "gateway": "172.31.0.1",
                "description": "GPU-enabled network for ML/AI containers"
            },
            "bpo-db-network": {
                "subnet": "172.32.0.0/16",
                "ip_range": "172.32.240.0/20",
                "gateway": "172.32.0.1",
                "description": "Database network for data services"
            },
            "bpo-monitoring-network": {
                "subnet": "172.33.0.0/16",
                "ip_range": "172.33.240.0/20",
                "gateway": "172.33.0.1",
                "description": "Monitoring network for observability"
            },
            "bpo-external-network": {
                "subnet": "172.34.0.0/16",
                "ip_range": "172.34.240.0/20",
                "gateway": "172.34.0.1",
                "description": "External network for public-facing services"
            }
        }

    def run_command(self, command: List[str]) -> tuple:
        """Run a Docker command and return (success, output, error)"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr

    def list_networks(self) -> List[Dict]:
        """List all Docker networks"""
        success, output, error = self.run_command(["docker", "network", "ls", "--format", "json"])
        if not success:
            print(f"Error listing networks: {error}")
            return []
        
        networks = []
        for line in output.strip().split('\n'):
            if line:
                try:
                    networks.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return networks

    def network_exists(self, name: str) -> bool:
        """Check if a network exists"""
        networks = self.list_networks()
        return any(net['Name'] == name for net in networks)

    def create_network(self, name: str) -> bool:
        """Create a network if it doesn't exist"""
        if self.network_exists(name):
            print(f"Network '{name}' already exists")
            return True
        
        if name not in self.networks:
            print(f"Unknown network: {name}")
            return False
        
        config = self.networks[name]
        command = [
            "docker", "network", "create",
            "--driver", "bridge",
            "--subnet", config["subnet"],
            "--ip-range", config["ip_range"],
            "--gateway", config["gateway"],
            name
        ]
        
        success, output, error = self.run_command(command)
        if success:
            print(f"Created network: {name}")
            return True
        else:
            print(f"Failed to create network '{name}': {error}")
            return False

    def create_all_networks(self) -> bool:
        """Create all BPO networks"""
        print("Creating Docker networks for BPO Project...")
        success = True
        
        for name in self.networks:
            if not self.create_network(name):
                success = False
        
        if success:
            print("\nAll networks created successfully!")
            self.show_network_status()
        else:
            print("\nSome networks failed to create")
        
        return success

    def remove_network(self, name: str) -> bool:
        """Remove a network"""
        if not self.network_exists(name):
            print(f"Network '{name}' does not exist")
            return True
        
        success, output, error = self.run_command(["docker", "network", "rm", name])
        if success:
            print(f"Removed network: {name}")
            return True
        else:
            print(f"Failed to remove network '{name}': {error}")
            return False

    def remove_all_networks(self) -> bool:
        """Remove all BPO networks"""
        print("Removing BPO networks...")
        success = True
        
        for name in self.networks:
            if not self.remove_network(name):
                success = False
        
        return success

    def show_network_status(self):
        """Show current network status"""
        print("\nCurrent Docker Networks:")
        print("-" * 50)
        
        networks = self.list_networks()
        bpo_networks = [net for net in networks if net['Name'].startswith('bpo-')]
        
        for net in bpo_networks:
            name = net['Name']
            driver = net['Driver']
            scope = net['Scope']
            print(f"{name:<25} {driver:<10} {scope}")
        
        print(f"\nTotal BPO networks: {len(bpo_networks)}")

    def connect_container(self, container: str, network: str) -> bool:
        """Connect a container to a network"""
        if not self.network_exists(network):
            print(f"Network '{network}' does not exist")
            return False
        
        success, output, error = self.run_command(["docker", "network", "connect", network, container])
        if success:
            print(f"Connected '{container}' to '{network}'")
            return True
        else:
            print(f"Failed to connect '{container}' to '{network}': {error}")
            return False

    def show_help(self):
        """Show help information"""
        print("Docker Network Manager for BPO Project")
        print("=" * 40)
        print("Usage: python manage_docker_networks.py [command]")
        print("\nCommands:")
        print("  create     - Create all BPO networks")
        print("  remove     - Remove all BPO networks")
        print("  status     - Show network status")
        print("  help       - Show this help")
        print("\nAvailable networks:")
        for name, config in self.networks.items():
            print(f"  {name:<25} - {config['description']}")

def main():
    manager = DockerNetworkManager()
    
    if len(sys.argv) < 2:
        manager.show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        manager.create_all_networks()
    elif command == "remove":
        manager.remove_all_networks()
    elif command == "status":
        manager.show_network_status()
    elif command == "help":
        manager.show_help()
    else:
        print(f"Unknown command: {command}")
        manager.show_help()

if __name__ == "__main__":
    main()
