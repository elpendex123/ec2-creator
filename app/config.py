import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # AWS credentials
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    # SMTP email notifications
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")

    # App config
    BACKEND = os.getenv("BACKEND", "terraform")

    # ECR / EKS
    ECR_REPO = os.getenv("ECR_REPO", "")
    ECR_IMAGE_TAG = os.getenv("ECR_IMAGE_TAG", "latest")
    EKS_CLUSTER_NAME = os.getenv("EKS_CLUSTER_NAME", "")

    # Database
    DB_PATH = os.getenv("DB_PATH", "./data/instances.db")

    # Free tier constants
    ALLOWED_INSTANCE_TYPES = ["t3.micro", "t4g.micro"]

    # Known free-tier AMIs (sample - per region)
    FREE_TIER_AMIS = {
        "us-east-1": [
            "ami-0c02fb55956c7d316",  # Amazon Linux 2 (older)
            "ami-026992d753d5622bc",  # Amazon Linux 2 (current)
            "ami-026ebee89baf5eb77",  # Ubuntu 20.04 LTS
        ],
        "us-east-2": [
            "ami-0ea3c35d6814e3cb6",
            "ami-0229d9f8ca82508cc",
        ],
        "us-west-1": [
            "ami-0fb653ca2d3203ac1",
            "ami-0f4c5fd4dd4dd1051",
        ],
        "us-west-2": [
            "ami-0430580de6244e02b",
            "ami-0e472933a1666f130",
        ],
        "eu-west-1": [
            "ami-0d3d0c0e87e3a77fd",
            "ami-0f1a8f29ed2ad83e2",
        ],
    }

    @classmethod
    def validate_free_tier(cls, instance_type: str, ami: str, region: str = None) -> bool:
        """Validate if instance_type and AMI are free tier eligible."""
        if instance_type not in cls.ALLOWED_INSTANCE_TYPES:
            return False

        if region is None:
            region = cls.AWS_DEFAULT_REGION

        allowed_amis = cls.FREE_TIER_AMIS.get(region, [])
        return ami in allowed_amis


settings = Settings()
