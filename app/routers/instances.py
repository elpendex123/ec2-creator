from fastapi import APIRouter, BackgroundTasks, Query, HTTPException, status
from app.models.instance import InstanceCreateRequest, InstanceResponse, InstanceListResponse
from app.config import settings
from app.services.db import db
from app.services.aws_cli import aws_cli_backend
from app.services.terraform import terraform_backend
from app.services.notifications import send_notification
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/instances", tags=["instances"])


def validate_free_tier(instance_type: str, ami: str, region: str = None) -> bool:
    """Validate if instance meets free tier requirements."""
    return settings.validate_free_tier(instance_type, ami, region)


def get_backend(backend_param: Optional[str] = None):
    """Get the appropriate backend based on query parameter or default."""
    backend = backend_param or settings.BACKEND
    if backend == "terraform":
        return terraform_backend
    elif backend == "awscli":
        return aws_cli_backend
    else:
        raise ValueError(f"Unknown backend: {backend}")


@router.post("", response_model=InstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_instance(
    request: InstanceCreateRequest,
    background_tasks: BackgroundTasks,
    backend: Optional[str] = Query(None, description="Backend to use: terraform or awscli"),
):
    """Create a new EC2 instance."""
    # Validate free tier
    if not validate_free_tier(request.instance_type, request.ami):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Instance type '{request.instance_type}' or AMI '{request.ami}' "
                "not allowed. Only t3.micro and t4g.micro instance types are "
                "free tier eligible."
            ),
        )

    # Get backend
    try:
        service = get_backend(backend)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Create instance
    try:
        result = service.create(
            request.name,
            request.ami,
            request.instance_type,
            request.storage_gb,
        )
        instance_id = result["id"].strip().split('\n')[-1]
        public_ip = result.get("public_ip", "").strip()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create instance: {str(e)}",
        )

    # Build SSH string
    ssh_string = f"ssh -i ~/.ssh/your-key.pem ec2-user@{public_ip}" if public_ip else ""

    # Store in database
    instance_data = {
        "id": instance_id,
        "name": request.name,
        "public_ip": public_ip,
        "ssh_string": ssh_string,
        "state": "running",
        "ami": request.ami,
        "instance_type": request.instance_type,
        "backend_used": backend or settings.BACKEND,
    }

    db.create_instance_record(instance_data)

    # Send notification in background
    background_tasks.add_task(send_notification, "create", instance_data)

    return InstanceResponse(
        id=instance_id,
        name=request.name,
        public_ip=public_ip,
        ssh_string=ssh_string,
        state="running",
        ami=request.ami,
        instance_type=request.instance_type,
        backend_used=backend or settings.BACKEND,
        created_at=datetime.utcnow(),
    )


@router.get("", response_model=InstanceListResponse)
async def list_instances(backend: Optional[str] = Query(None)):
    """List all instances."""
    instances = db.list_instances()

    return InstanceListResponse(
        instances=[
            InstanceResponse(
                id=inst["id"],
                name=inst["name"],
                public_ip=inst["public_ip"],
                ssh_string=inst["ssh_string"],
                state=inst["state"],
                ami=inst["ami"],
                instance_type=inst["instance_type"],
                backend_used=inst["backend_used"],
                created_at=inst["created_at"],
            )
            for inst in instances
        ]
    )


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(instance_id: str, backend: Optional[str] = Query(None)):
    """Get details of a specific instance."""
    instance = db.get_instance(instance_id)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance not found: {instance_id}",
        )

    return InstanceResponse(
        id=instance["id"],
        name=instance["name"],
        public_ip=instance["public_ip"],
        ssh_string=instance["ssh_string"],
        state=instance["state"],
        ami=instance["ami"],
        instance_type=instance["instance_type"],
        backend_used=instance["backend_used"],
        created_at=instance["created_at"],
    )


@router.post("/{instance_id}/start", response_model=InstanceResponse)
async def start_instance(
    instance_id: str,
    background_tasks: BackgroundTasks,
    backend: Optional[str] = Query(None),
):
    """Start a stopped instance."""
    # Check if instance exists
    instance = db.get_instance(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance not found: {instance_id}",
        )

    # Get backend
    try:
        service = get_backend(backend or instance["backend_used"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Start instance
    try:
        service.start(instance_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start instance: {str(e)}",
        )

    # Update state
    db.update_instance_state(instance_id, "running")
    updated = db.get_instance(instance_id)

    # Send notification
    background_tasks.add_task(send_notification, "start", updated)

    return InstanceResponse(
        id=updated["id"],
        name=updated["name"],
        public_ip=updated["public_ip"],
        ssh_string=updated["ssh_string"],
        state=updated["state"],
        ami=updated["ami"],
        instance_type=updated["instance_type"],
        backend_used=updated["backend_used"],
        created_at=updated["created_at"],
    )


@router.post("/{instance_id}/stop", response_model=InstanceResponse)
async def stop_instance(
    instance_id: str,
    background_tasks: BackgroundTasks,
    backend: Optional[str] = Query(None),
):
    """Stop a running instance."""
    # Check if instance exists
    instance = db.get_instance(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance not found: {instance_id}",
        )

    # Get backend
    try:
        service = get_backend(backend or instance["backend_used"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Stop instance
    try:
        service.stop(instance_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop instance: {str(e)}",
        )

    # Update state
    db.update_instance_state(instance_id, "stopped")
    updated = db.get_instance(instance_id)

    # Send notification
    background_tasks.add_task(send_notification, "stop", updated)

    return InstanceResponse(
        id=updated["id"],
        name=updated["name"],
        public_ip=updated["public_ip"],
        ssh_string=updated["ssh_string"],
        state=updated["state"],
        ami=updated["ami"],
        instance_type=updated["instance_type"],
        backend_used=updated["backend_used"],
        created_at=updated["created_at"],
    )


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy_instance(
    instance_id: str,
    background_tasks: BackgroundTasks,
    backend: Optional[str] = Query(None),
):
    """Destroy/terminate an instance."""
    # Check if instance exists
    instance = db.get_instance(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance not found: {instance_id}",
        )

    # Get backend
    try:
        service = get_backend(backend or instance["backend_used"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Destroy instance
    try:
        service.destroy(instance_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to destroy instance: {str(e)}",
        )

    # Update state
    db.update_instance_state(instance_id, "terminated")
    updated = db.get_instance(instance_id)

    # Send notification
    background_tasks.add_task(send_notification, "destroy", updated)

    # Delete from database
    db.delete_instance_record(instance_id)

    return None
