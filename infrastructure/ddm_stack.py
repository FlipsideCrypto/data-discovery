# infrastructure/stack.py
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct

class DataDiscoveryStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create VPC
        vpc = ec2.Vpc(self, "DataDiscoveryVPC", max_azs=2)

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "DataDiscoveryCluster", vpc=vpc)

        # Create Fargate Service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "DataDiscoveryService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="../",
                    platform=ecr_assets.Platform.LINUX_AMD64
                ),
                container_port=8000,
                environment={
                    "DEPLOYMENT_MODE": "api",
                    "DEBUG_MODE": "false",
                    "LOG_LEVEL": "INFO",
                    "MAX_PROJECTS": "50"
                },
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="data-discovery",
                    log_retention=logs.RetentionDays.ONE_WEEK
                )
            ),
            public_load_balancer=True
        )

        # Configure health check
        fargate_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200"
        )

        # Output the ALB URL
        self.load_balancer_url = fargate_service.load_balancer.load_balancer_dns_name