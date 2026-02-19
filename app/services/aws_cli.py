import subprocess
import json
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AwsCliBackend:
    def __init__(self, scripts_dir: str = "aws_cli_bash_scripts"):
        self.scripts_dir = scripts_dir

    def _run_script(self, script_name: str, args: List[str] = None) -> Dict[str, Any]:
        """Run a bash script and return parsed output."""
        script_path = os.path.join(self.scripts_dir, script_name)

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        cmd = [script_path]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.error(f"Script error: {result.stderr}")
                raise RuntimeError(f"Script failed: {result.stderr}")

            return {"output": result.stdout.strip(), "error": None}

        except subprocess.TimeoutExpired:
            raise RuntimeError("Script execution timed out")
        except Exception as e:
            logger.error(f"Failed to execute script: {str(e)}")
            raise

    def create(self, name: str, ami: str, instance_type: str, storage_gb: int) -> Dict[str, str]:
        """Create an EC2 instance via AWS CLI."""
        result = self._run_script("create_instance.sh", [name, ami, instance_type, str(storage_gb)])
        output = result["output"]

        # Parse output: expected format "instance_id|public_ip"
        try:
            parts = output.split("|")
            instance_id = parts[0].strip()
            public_ip = parts[1].strip() if len(parts) > 1 else ""
            return {"id": instance_id, "public_ip": public_ip}
        except Exception as e:
            logger.error(f"Failed to parse create output: {output}")
            raise RuntimeError(f"Failed to parse instance creation response: {str(e)}")

    def list_instances(self) -> List[Dict[str, str]]:
        """List all EC2 instances."""
        result = self._run_script("list_instances.sh")
        output = result["output"]

        # Parse AWS CLI JSON output
        try:
            # AWS CLI describe-instances returns JSON
            data = json.loads(output)
            instances = []

            for reservation in data.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append({
                        "id": instance.get("InstanceId", ""),
                        "state": instance.get("State", {}).get("Name", ""),
                        "public_ip": instance.get("PublicIpAddress", ""),
                        "instance_type": instance.get("InstanceType", ""),
                        "ami": instance.get("ImageId", ""),
                        "launch_time": instance.get("LaunchTime", ""),
                    })

            return instances
        except Exception as e:
            logger.error(f"Failed to parse list output: {output}")
            raise RuntimeError(f"Failed to parse instances list: {str(e)}")

    def get_instance(self, instance_id: str) -> Dict[str, str]:
        """Get details of a specific instance."""
        instances = self.list_instances()
        for inst in instances:
            if inst["id"] == instance_id:
                return inst
        raise RuntimeError(f"Instance not found: {instance_id}")

    def start(self, instance_id: str) -> Dict[str, str]:
        """Start a stopped EC2 instance."""
        self._run_script("start_instance.sh", [instance_id])
        return {"state": "running", "id": instance_id}

    def stop(self, instance_id: str) -> Dict[str, str]:
        """Stop a running EC2 instance."""
        self._run_script("stop_instance.sh", [instance_id])
        return {"state": "stopped", "id": instance_id}

    def destroy(self, instance_id: str) -> Dict[str, str]:
        """Terminate an EC2 instance."""
        self._run_script("destroy_instance.sh", [instance_id])
        return {"state": "terminated", "id": instance_id}


aws_cli_backend = AwsCliBackend()
