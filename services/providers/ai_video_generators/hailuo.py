from typing import Any
from enums import GenerationStatus
from .piapi_base import PiAPIBaseGenerator
from .base_generator import GenerationResult

class HailuoGenerator(PiAPIBaseGenerator):
    """Hailuo (MiniMax) video generator via piAPI."""

    def __init__(self, api_key: str, model: str = "hailuo", sub_model: str = "v2.3-fast"):
        super().__init__(api_key)
        self.model = model
        self.sub_model = sub_model

    async def generate(self, image_path: str, prompt: str, negative_prompt: str | None = None, **kwargs) -> GenerationResult:
        """
        Generate video using Hailuo model.
        """
        # Hailuo specific params can be added to input_params
        input_params = kwargs.get("input_params", {})
        
        # Default duration and resolution for Hailuo 2.3 if not specified
        if "duration" not in input_params:
            input_params["duration"] = 6
        if "resolution" not in input_params:
             input_params["resolution"] = 768
        if "expand_prompt" not in input_params:
            input_params["expand_prompt"] = True
        
        # Hailuo documentation shows model version inside input
        input_params["model"] = self.sub_model
        
        # Ensure model is set
        kwargs["model"] = self.model
        kwargs["input_params"] = input_params
        
        return await super().generate(image_path, prompt, negative_prompt, **kwargs)
