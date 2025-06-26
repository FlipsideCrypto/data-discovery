import os
import aws_cdk as cdk
from ddm_stack import DataDiscoveryStack

current_env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

env_map = {
    "490041342817": "dev",
    "704693948482": "stg",
    "924682671219": "prod",
}

stage = env_map.get(current_env.account, "sbx")

app = cdk.App()
DataDiscoveryStack(app, f"ddm-{stage}-stack", stage=stage, env=current_env)
app.synth()