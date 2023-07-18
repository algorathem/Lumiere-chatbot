# Derived from ZenML Seldon integration; source : https://github.com/zenml-io/zenml/blob/release/0.40.3/src/zenml/integrations/seldon/steps/seldon_deployer.py
"""Custom ZenML deployer step for Seldon LLM."""
import os
from typing import cast

from zenml import step
from zenml.environment import Environment
from zenml.exceptions import DoesNotExistException
from zenml.integrations.seldon.constants import (
    SELDON_CUSTOM_DEPLOYMENT,
    SELDON_DOCKER_IMAGE_KEY,
)
from zenml.integrations.seldon.model_deployers.seldon_model_deployer import (
    DEFAULT_SELDON_DEPLOYMENT_START_STOP_TIMEOUT,
    SeldonModelDeployer,
)
from zenml.integrations.seldon.seldon_client import (
    create_seldon_core_custom_spec,
)
from zenml.integrations.seldon.services.seldon_deployment import (
    SeldonDeploymentConfig,
    SeldonDeploymentService,
)
from zenml.io import fileio
from zenml.logger import get_logger
from zenml.steps import (
    STEP_ENVIRONMENT_NAME,
    StepEnvironment,
)
from zenml.steps.step_context import StepContext
from zenml.utils import io_utils, source_utils

logger = get_logger(__name__)
DEFAULT_PT_MODEL_DIR = "hf_pt_model"
DEFAULT_TOKENIZER_DIR = "hf_tokenizer"


def copy_artifact(uri: str, context: StepContext) -> str:
    """Copy an artifact to the output location of the current step.

    Args:
        uri (str): URI of the artifact to copy
        context (StepContext): ZenML step context

    Returns:
        str: URI of the output location

    Raises:
        RuntimeError: if the artifact is not found

    """
    served_artifact_uri = os.path.join(context.get_output_artifact_uri(), "seldon")
    fileio.makedirs(served_artifact_uri)

    if not fileio.exists(uri):
        raise RuntimeError(f"Expected artifact was not found at f {uri}")
    if io_utils.isdir(  # type: ignore[attr-defined]
        uri
    ):  # isdir() is used in the up to date ZenML example
        io_utils.copy_dir(uri, served_artifact_uri)
    else:
        fileio.copy(uri, served_artifact_uri)

    return served_artifact_uri


@step(enable_cache=False, extra={SELDON_CUSTOM_DEPLOYMENT: True})
def seldon_llm_model_deployer_step(  # noqa: PLR0913 # Too many arguments for ruff
    model_uri: str,
    tokenizer_uri: str,
    predict_function: str,
    service_config: SeldonDeploymentConfig,  # New from ZenML v0.40.3
    context: StepContext,
    deploy_decision: bool = True,
    timeout: int = DEFAULT_SELDON_DEPLOYMENT_START_STOP_TIMEOUT,
) -> SeldonDeploymentService:
    """Seldon Core custom model deployer pipeline step for LLM models.

    This step can be used in a pipeline to implement the
    the process required to deploy a custom model with Seldon Core.

    Args:
        model_uri (str): The Huggingface model artifact uri.
        tokenizer_uri (str): The Huggingface tokenizer artifact uri.
        predict_function: Path to Python file containing predict function.
        service_config: Seldon Core deployment service configuration
        context (StepContext): the step context
        deploy_decision (bool): whether to deploy the model or not
        timeout: the timeout in seconds to wait for the deployment to start

    Raises:
        ValueError: if the custom deployer is not defined
        DoesNotExistException: if an entity does not exist raise an exception

    Returns:
        SeldonDeploymentService: Seldon Core deployment service
    """
    # Verify that the predict function is valid
    try:
        loaded_predict_function = source_utils.load(predict_function)
    except AttributeError:
        raise ValueError("Predict function can't be found.")
    if not callable(loaded_predict_function):
        raise TypeError("Predict function must be callable.")

    # get the active model deployer
    model_deployer = cast(
        SeldonModelDeployer, SeldonModelDeployer.get_active_model_deployer()
    )

    # get pipeline name, step name, run id
    step_env = cast(StepEnvironment, Environment()[STEP_ENVIRONMENT_NAME])
    pipeline_name = step_env.pipeline_name
    run_name = step_env.run_name
    step_name = step_env.step_name

    # update the step configuration with the real pipeline runtime information
    service_config.pipeline_name = pipeline_name
    service_config.run_name = run_name
    service_config.pipeline_step_name = step_name
    service_config.is_custom_deployment = True

    # fetch existing services with the same pipeline name, step name and
    # model name
    existing_services = model_deployer.find_model_server(
        pipeline_name=pipeline_name,
        pipeline_step_name=step_name,
        model_name=service_config.model_name,
    )
    # even when the deploy decision is negative if an existing model server
    # is not running for this pipeline/step, we still have to serve the
    # current model, to ensure that a model server is available at all times
    if not deploy_decision and existing_services:
        logger.info(
            f"Skipping model deployment because the model quality does not"
            f" meet the criteria. Reusing the last model server deployed by step "
            f"'{step_name}' and pipeline '{pipeline_name}' for model "
            f"'{service_config.model_name}'..."
        )
        service = cast(SeldonDeploymentService, existing_services[0])
        # even when the deployment decision is negative, we still need to start
        # the previous model server if it is no longer running, to ensure that
        # a model server is available at all times
        if not service.is_running:
            service.start(timeout=timeout)
        return service

    # entrypoint for starting Seldon microservice deployment for custom model
    entrypoint_command = [
        "python",
        "-m",
        "steps.deployment_steps.deploy_model_step.zenml_llm_custom_model",
        "--model_name",
        service_config.model_name,
        "--predict_func",
        predict_function,
    ]

    # verify if there is an active stack before starting the service
    if not context.stack:
        raise DoesNotExistException(
            "No active stack is available. "
            "Please make sure that you have registered and set a stack."
        )

    image_name = step_env.step_run_info.get_image(key=SELDON_DOCKER_IMAGE_KEY)

    # Copy artifacts
    served_model_uri = copy_artifact(model_uri, context)
    copy_artifact(tokenizer_uri, context)

    # prepare the service configuration for the deployment
    service_config = service_config.copy()
    service_config.model_uri = served_model_uri

    # create the specification for the custom deployment
    service_config.spec = create_seldon_core_custom_spec(
        model_uri=service_config.model_uri,
        custom_docker_image=image_name,
        secret_name=model_deployer.kubernetes_secret_name,
        command=entrypoint_command,
    )

    # deploy the service
    service = cast(
        SeldonDeploymentService,
        model_deployer.deploy_model(service_config, replace=True, timeout=timeout),
    )

    logger.info(
        f"Seldon Core deployment service started and reachable at:\n"
        f"    {service.prediction_url}\n"
    )

    return service