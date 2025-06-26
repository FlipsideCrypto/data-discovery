# infrastructure/stack.py
import os
from aws_cdk import (
    Stack,
    Tags,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct

class DataDiscoveryStack(Stack):
    """
    Data Discovery Stack
    """
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        self.stage = kwargs.pop("stage", "sbx") 
        super().__init__(scope, id, **kwargs)

        # vpc = ec2.Vpc(self, f"ddm-{self.stage}-ecs-vpc", max_azs=2, nat_gateways=1)

        vpc = ec2.Vpc.from_lookup(
            self,
            "ExistingVpc",
            tags={"Namespace": "clusters"} 
        )

        cluster = ecs.Cluster(self, f"ddm-{self.stage}-ecs-cluster", vpc=vpc)

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, f"ddm-{self.stage}-ecs-svc",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=1,
            load_balancer_name=f"ddm-{self.stage}-alb",
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
                    "MAX_PROJECTS": "50",
                    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")
                },
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix=f"ddm-{self.stage}",
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

        self._add_tags(stage=self.stage)

    def _add_tags(
            self,
            stage: str,
            custom_tags: dict = None,
        ) -> None:
            """
            Adds tags to all constructs/resources in the stack
            """
            stack = Stack.of(self)

            project_tags = {
                "owner": "data-platform",
                "project": "ddm",
                "environment": stage,
            }

            if custom_tags:
                project_tags.update(custom_tags)

            # Add the tags to the stack
            for key, value in project_tags.items():
                Tags.of(stack).add(key, value)