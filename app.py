import aws_cdk as cdk
from aws_cdk import App
from aws_cdk import Stack
from aws_cdk import aws_appconfig
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedTaskImageOptions

from aws_cdk.aws_ecs import AwsLogDriverMode
from aws_cdk.aws_ecs import CfnService
from aws_cdk.aws_ecs import ContainerImage
from aws_cdk.aws_ecs import DeploymentCircuitBreaker
from aws_cdk.aws_ecs import Secret
from aws_cdk.aws_ecs import LogDriver
from aws_cdk.aws_ec2 import Vpc
from aws_cdk.aws_iam import Role
from aws_cdk.aws_iam import PolicyStatement
from constructs import Construct


ENVIRONMENT = cdk.Environment(account="618537831167", region="us-west-2")

class AppconfigStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.__application_name = None
        self.__environment_name = None
        self.__configuration_profile_name = None

        self.application = aws_appconfig.CfnApplication(
                self,
                "TestingCfnApplication",
                name="testappconf",
                description="appconfig test application",
                tags=[aws_appconfig.CfnApplication.TagsProperty(
                    key="some",
                    value="tag"
                    )
                ]
        )
        self.application.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        self.environment_ = aws_appconfig.CfnEnvironment(
                self,
                "TestingCfnEnvironment",
                name="testingenv",
                application_id=self.application.ref
        )
        self.environment_.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        self.configuration_profile = aws_appconfig.CfnConfigurationProfile(
                self,
                "TestingCfnConfigurationProfile",
                application_id=self.application.ref,
                name="testconfprofile",
                location_uri="hosted"
        )
        self.configuration_profile.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        self.hosted_configuration_version = aws_appconfig.CfnHostedConfigurationVersion(
                self,
                "TestingCfnHostedConfigurationVersion",
                application_id=self.application.ref,
                configuration_profile_id=self.configuration_profile.ref,
                content_type="application/json",
                content='{"transform_reverse": true, "transform_allcaps": false}'
        )
        self.hosted_configuration_version.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        self.deployment_strategy = aws_appconfig.CfnDeploymentStrategy(
                self,
                "TestingCfnDeploymentStrategy",
                deployment_duration_in_minutes=1,
                growth_factor=100,
                name="testingdeploymentstrategy",
                replicate_to="NONE",
                final_bake_time_in_minutes=1
        )
        self.deployment_strategy.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        self.deployment = aws_appconfig.CfnDeployment(self,
                "TestingCfnDeployment",
                application_id=self.application.ref,
                configuration_profile_id=self.configuration_profile.ref,
                configuration_version=self.hosted_configuration_version.ref,
                deployment_strategy_id=self.deployment_strategy.ref,
                environment_id=self.environment_.ref
        )

    @property
    def application_name(self):
        if self.__application_name is not None:
            return self.__application_name
        else:
            self.__application_name = self.application.name
            return self.__application_name

    @property
    def environment_name(self):
        if self.__environment_name is not None:
            return self.__environment_name
        else:
            self.__environment_name = self.environment_.name
            return self.__environment_name

    @property
    def configuration_profile_name(self):
        if self.__configuration_profile_name is not None:
            return self.__configuration_profile_name
        else:
            self.__configuration_profile_name = self.configuration_profile.name
            return self.__configuration_profile_name


class FarGateTestApp(Stack):
    def __init__(self,
            scope: Construct,
            construct_id: str,
            *,
            appconf_app_name: str,
            appconf_env_name: str,
            appconf_conf_prof_name: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.fargate_service = ApplicationLoadBalancedFargateService(
            self,
            "Fargate",
            vpc=Vpc.from_lookup(self, "VPC", vpc_id="vpc-ea3b6581"),
            cpu=256,
            desired_count=1,
            circuit_breaker=DeploymentCircuitBreaker(rollback=True),
            task_image_options=ApplicationLoadBalancedTaskImageOptions(
                container_name="testapp",
                environment={
                    "APPCONF_APP_NAME": appconf_app_name,
                    "APPCONF_ENV_NAME": appconf_env_name,
                    "APPCONF_CONF_PROF_NAME": appconf_conf_prof_name,
                },
                image=ContainerImage.from_registry("ojolanki/testapp"),
                log_driver=LogDriver.aws_logs(
                    stream_prefix="testapp",
                    mode=AwsLogDriverMode.NON_BLOCKING
                )
            ),
            memory_limit_mib=512,
            public_load_balancer=True,
            assign_public_ip=True,
        )
        self.fargate_service.task_definition.add_to_task_role_policy(
                PolicyStatement(
                    actions=[
                        "appconfig:StartConfigurationSession",
                        "appconfig:GetLatestConfiguration",
                    ],
                    resources=["*"]
                )
        )

app = App()
appconfigstack = AppconfigStack(
    app,
    "AppconfigStack",
    env=ENVIRONMENT,
)
testappstack= FarGateTestApp(
    app,
    "TestAppStack",
    appconf_app_name=appconfigstack.application_name,
    appconf_env_name=appconfigstack.environment_name,
    appconf_conf_prof_name=appconfigstack.configuration_profile_name,
    env=ENVIRONMENT,
)
app.synth()
