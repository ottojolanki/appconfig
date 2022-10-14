from appconfig_helper import AppConfigHelper
from fastapi import FastAPI

app = FastAPI()

appconfig = AppConfigHelper(
    "testappconf",
    "testingenv",
    "testconfprofile",
    15,
)


@app.get("/process-string/{input_string}")
def index(input_string):
    if appconfig.update_config():
        print("Received new configuration")
    output_string = input_string
    if appconfig.config.get("transform_reverse", False):
        output_string = "".join(reversed(output_string))
    if appconfig.config.get("transform_allcaps", False):
        output_string = output_string.upper()
    """
    config = {"transform_reverse": True, "transform_allcaps": False}
    output_string = input_string
    if config.get("transform_reverse", False):
        output_string = "".join(reversed(output_string))
    if config.get("transform_allcaps", False):
        output_string = output_string.upper()
    """
    return {
        "output": output_string,
    }
