import subprocess
import json
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TerraformBackend:
    def __init__(self, scripts_dir: str = "terraform_bash_scripts", tf_dir: str = "terraform/ec2"):
        self.scripts_dir = scripts_dir
        self.tf_dir = tf_dir

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
                timeout=600,
                cwd=self.tf_dir,
            )

            if result.returncode != 0:
                logger.error(f"Script error: {result.stderr}")
                raise RuntimeError(f"Script failed: {result.stderr}")

            return {"output": result.stdout.strip(), "error": None}

        except subprocess.TimeoutExpired:
            raise RuntimeError("Terraform operation timed out")
        except Exception as e:
            logger.error(f"Failed to execute script: {str(e)}")
            raise

    def create(self, name: str, ami: str, instance_type: str, storage_gb: int) -> Dict[str, str]:
        """Create an EC2 instance via Terraform."""
        result = self._run_script("tf_create.sh", [name, ami, instance_type, str(storage_gb)])
        output = result["output"]

        # Parse output: expected format "instance_id|public_ip"
        try:
            parts = output.split("|")
            instance_id = parts[0].strip()
            public_ip = parts[1].strip() if len(parts) > 1 else ""
            return {"id": instance_id, "public_ip": public_ip}
        except Exception as e:
            logger.error(f"Failed to parse create output: {output}")
            raise RuntimeError(f"Failed to parse Terraform response: {str(e)}")

    def list_instances(self) -> List[Dict[str, str]]:
        """List all EC2 instances managed by Terraform."""
        result = self._run_script("tf_list.sh")
        output = result["output"]

        # Parse terraform show -json output
        try:
            data = json.loads(output)
            instances = []

            # Extract instances from Terraform state
            resources = data.get("values", {}).get("root_module", {}).get("resources", [])
            for resource in resources:
                if resource.get("type") == "aws_instance":
                    values = resource.get("values", {})
                    instances.append({
                        "id": values.get("id", ""),
                        "state": "running",  # Terraform managed instances are running if in state
                        "public_ip": values.get("public_ip", ""),
                        "instance_type": values.get("instance_type", ""),
                        "ami": values.get("ami", ""),
                    })

            return instances
        except Exception as e:
            logger.error(f"Failed to parse list output: {output}")
            raise RuntimeError(f"Failed to parse Terraform state: {str(e)}")

    def get_instance(self, instance_id: str) -> Dict[str, str]:
        """Get details of a specific instance."""
        instances = self.list_instances()
        for inst in instances:
            if inst["id"] == instance_id:
                return inst
        raise RuntimeError(f"Instance not found: {instance_id}")

    def start(self, instance_id: str) -> Dict[str, str]:
        """Start a stopped EC2 instance (delegates to AWS CLI)."""
        self._run_script("tf_start.sh", [instance_id])
        return {"state": "running", "id": instance_id}

    def stop(self, instance_id: str) -> Dict[str, str]:
        """Stop a running EC2 instance (delegates to AWS CLI)."""
        self._run_script("tf_stop.sh", [instance_id])
        return {"state": "stopped", "id": instance_id}

    def destroy(self, instance_id: str) -> Dict[str, str]:
        """Destroy an EC2 instance via Terraform."""
        self._run_script("tf_destroy.sh", [instance_id])
        return {"state": "terminated", "id": instance_id}


terraform_backend = TerraformBackend()
