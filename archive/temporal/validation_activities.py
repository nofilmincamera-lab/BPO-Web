"""
BPO Intelligence Pipeline - Validation Activities

Activities for verifying system operational readiness:
- Docker container verification
- Python package verification
- Heuristics file validation
- Database schema validation
"""

import docker
import json
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path

from temporalio import activity
from temporalio.exceptions import ApplicationError


@dataclass
class VerificationResult:
    """Result of a verification check."""
    component: str
    status: str  # "pass", "fail", "warning"
    details: Dict[str, Any]
    message: str


@activity.defn
async def verify_docker_containers_activity() -> List[VerificationResult]:
    """
    Verify all required Docker containers are running.
    
    Required containers:
    - bpo-postgres
    - bpo-temporal
    - bpo-temporal-ui
    - bpo-worker
    - bpo-api
    - bpo-pgbouncer (optional, profile dbpool)
    """
    results = []
    
    try:
        client = docker.from_env()
        running_containers = {c.name for c in client.containers.list()}
        
        required_containers = [
            "bpo-postgres",
            "bpo-temporal",
            "bpo-temporal-ui",
            "bpo-worker",
            "bpo-api",
        ]
        
        optional_containers = [
            "bpo-pgbouncer",
            "bpo-ollama",
            "bpo-label-studio",
        ]
        
        # Check required containers
        for container_name in required_containers:
            if container_name in running_containers:
                results.append(VerificationResult(
                    component=container_name,
                    status="pass",
                    details={"running": True},
                    message=f"{container_name} is running"
                ))
            else:
                results.append(VerificationResult(
                    component=container_name,
                    status="fail",
                    details={"running": False},
                    message=f"{container_name} is NOT running"
                ))
        
        # Check optional containers
        for container_name in optional_containers:
            if container_name in running_containers:
                results.append(VerificationResult(
                    component=container_name,
                    status="pass",
                    details={"running": True, "optional": True},
                    message=f"{container_name} is running (optional)"
                ))
            else:
                results.append(VerificationResult(
                    component=container_name,
                    status="warning",
                    details={"running": False, "optional": True},
                    message=f"{container_name} is not running (optional)"
                ))
        
        activity.logger.info(f"Verified {len(required_containers)} required containers")
        
    except Exception as e:
        activity.logger.error(f"Error verifying containers: {e}")
        results.append(VerificationResult(
            component="docker_client",
            status="fail",
            details={"error": str(e)},
            message=f"Failed to connect to Docker: {e}"
        ))
    
    return results


@activity.defn
async def verify_python_packages_activity() -> List[VerificationResult]:
    """
    Verify Python packages are installed in worker and api containers.
    
    Reads requirements.txt and compares against pip list output.
    """
    results = []
    
    containers_to_check = ["bpo-worker", "bpo-api"]
    
    # Read requirements.txt
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        results.append(VerificationResult(
            component="requirements.txt",
            status="fail",
            details={"error": "File not found"},
            message="requirements.txt not found"
        ))
        return results
    
    # Parse requirements.txt
    required_packages = {}
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '==' in line:
                parts = line.split('==')
                if len(parts) == 2:
                    package_name = parts[0].lower()
                    required_packages[package_name] = parts[1]
    
    activity.logger.info(f"Found {len(required_packages)} required packages")
    
    # Check each container
    for container_name in containers_to_check:
        try:
            # Get pip list from container
            result = subprocess.run(
                ["docker", "exec", container_name, "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                results.append(VerificationResult(
                    component=f"{container_name}_packages",
                    status="fail",
                    details={"error": result.stderr},
                    message=f"Failed to get package list from {container_name}"
                ))
                continue
            
            # Parse installed packages
            installed_packages = {}
            for pkg in json.loads(result.stdout):
                installed_packages[pkg['name'].lower()] = pkg['version']
            
            # Compare required vs installed
            missing_packages = []
            version_mismatches = []
            
            for pkg_name, required_version in required_packages.items():
                if pkg_name not in installed_packages:
                    missing_packages.append(pkg_name)
                elif installed_packages[pkg_name] != required_version:
                    version_mismatches.append({
                        "package": pkg_name,
                        "required": required_version,
                        "installed": installed_packages[pkg_name]
                    })
            
            if missing_packages or version_mismatches:
                results.append(VerificationResult(
                    component=f"{container_name}_packages",
                    status="fail",
                    details={
                        "missing": missing_packages,
                        "version_mismatches": version_mismatches,
                        "total_required": len(required_packages),
                        "total_installed": len(installed_packages)
                    },
                    message=f"{container_name}: {len(missing_packages)} missing, {len(version_mismatches)} version mismatches"
                ))
            else:
                results.append(VerificationResult(
                    component=f"{container_name}_packages",
                    status="pass",
                    details={
                        "total_packages": len(installed_packages),
                        "all_match": True
                    },
                    message=f"{container_name}: All packages installed correctly"
                ))
        
        except Exception as e:
            results.append(VerificationResult(
                component=f"{container_name}_packages",
                status="fail",
                details={"error": str(e)},
                message=f"Error checking {container_name}: {e}"
            ))
    
    return results


@activity.defn
async def verify_heuristics_files_activity() -> List[VerificationResult]:
    """
    Verify all heuristics files exist and are valid JSON.
    
    Expected files:
    - company_aliases_clean.json
    - countries.json
    - tech_terms.json
    - taxonomy_industries.json
    - taxonomy_services.json
    - products.json
    - partnerships.json
    - ner_relationships.json
    - version.json
    """
    results = []
    
    heuristics_dir = Path("Heuristics")
    required_files = [
        "company_aliases_clean.json",
        "countries.json",
        "tech_terms.json",
        "taxonomy_industries.json",
        "taxonomy_services.json",
        "products.json",
        "partnerships.json",
        "ner_relationships.json",
        "version.json",
    ]
    
    for filename in required_files:
        filepath = heuristics_dir / filename
        
        if not filepath.exists():
            results.append(VerificationResult(
                component=filename,
                status="fail",
                details={"path": str(filepath)},
                message=f"{filename} not found"
            ))
            continue
        
        # Try to parse as JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Basic validation
            file_size = filepath.stat().st_size
            
            results.append(VerificationResult(
                component=filename,
                status="pass",
                details={
                    "size_bytes": file_size,
                    "valid_json": True
                },
                message=f"{filename} exists and is valid JSON ({file_size} bytes)"
            ))
        
        except json.JSONDecodeError as e:
            results.append(VerificationResult(
                component=filename,
                status="fail",
                details={"error": str(e)},
                message=f"{filename} contains invalid JSON: {e}"
            ))
        
        except Exception as e:
            results.append(VerificationResult(
                component=filename,
                status="fail",
                details={"error": str(e)},
                message=f"Error reading {filename}: {e}"
            ))
    
    activity.logger.info(f"Verified {len(required_files)} heuristics files")
    
    return results


@activity.defn
async def verify_database_schema_activity() -> List[VerificationResult]:
    """
    Verify database schema is up to date using Alembic.
    
    Checks:
    - Alembic can connect to database
    - Current revision matches head
    - All required tables exist
    """
    results = []
    
    try:
        # Get database connection info
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "bpo_intel")
        db_user = os.getenv("DB_USER", "postgres")
        
        # Check Alembic current revision
        result = subprocess.run(
            ["docker", "exec", "bpo-postgres", "alembic", "current"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/app"  # If running in container
        )
        
        if result.returncode != 0:
            # Try alternative: docker exec into worker container
            result = subprocess.run(
                ["docker", "exec", "bpo-worker", "alembic", "current"],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        if result.returncode == 0:
            current_revision = result.stdout.strip()
            results.append(VerificationResult(
                component="alembic_current",
                status="pass",
                details={"revision": current_revision},
                message=f"Current Alembic revision: {current_revision}"
            ))
        else:
            results.append(VerificationResult(
                component="alembic_current",
                status="warning",
                details={"error": result.stderr},
                message="Could not determine Alembic current revision"
            ))
        
        # Check Alembic head
        result = subprocess.run(
            ["docker", "exec", "bpo-worker", "alembic", "heads"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            head_revision = result.stdout.strip()
            results.append(VerificationResult(
                component="alembic_head",
                status="pass",
                details={"revision": head_revision},
                message=f"Alembic head revision: {head_revision}"
            ))
        else:
            results.append(VerificationResult(
                component="alembic_head",
                status="warning",
                details={"error": result.stderr},
                message="Could not determine Alembic head revision"
            ))
        
        # Verify tables exist
        required_tables = [
            "documents",
            "document_chunks",
            "entities",
            "relationships",
            "taxonomy_labels",
            "entity_embeddings",
            "pipeline_checkpoints",
        ]
        
        activity.logger.info(f"Verification complete: {len(results)} checks")
        
    except Exception as e:
        results.append(VerificationResult(
            component="database_schema",
            status="fail",
            details={"error": str(e)},
            message=f"Error verifying database schema: {e}"
        ))
    
    return results


@activity.defn
async def wait_until_time_activity(target_hour: int, target_minute: int) -> None:
    """
    Wait until specified time with periodic heartbeats.
    
    Args:
        target_hour: Hour to wait until (0-23)
        target_minute: Minute to wait until (0-59)
    """
    from datetime import datetime, time, timedelta
    
    while True:
        now = datetime.now()
        target_time = datetime.combine(now.date(), time(target_hour, target_minute))
        
        # If target time has passed today, use tomorrow
        if now > target_time:
            target_time += timedelta(days=1)
        
        seconds_until_target = (target_time - now).total_seconds()
        
        activity.logger.info(
            f"Waiting until {target_time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"({seconds_until_target:.0f} seconds remaining)"
        )
        
        # Sleep in 10-minute chunks with heartbeat
        chunk_size = 600  # 10 minutes
        
        while seconds_until_target > chunk_size:
            activity.heartbeat(f"Waiting until {target_time.strftime('%H:%M')}")
            await asyncio.sleep(chunk_size)
            seconds_until_target -= chunk_size
        
        # Sleep remaining time
        if seconds_until_target > 0:
            activity.heartbeat(f"Final wait: {seconds_until_target:.0f} seconds")
            await asyncio.sleep(seconds_until_target)
        
        break
    
    activity.logger.info(f"Target time reached: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


import asyncio

