#!/usr/bin/env python3
import aws_cdk as cdk
from ddm_stack import DataDiscoveryStack

app = cdk.App()
DataDiscoveryStack(app, "DataDiscoveryStack")
app.synth()