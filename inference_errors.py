class InferenceError(Exception):
    """Base class: every failure is a distinct, labelled outcome."""


class OllamaUnavailable(InferenceError):
    """Connection refused or HTTP error."""


class OllamaTimeout(InferenceError):
    """The request exceeded the configured timeout."""


class TruncatedOutput(InferenceError):
    """done_reason was 'length': the token cap cut the answer off."""


class InvalidModelOutput(InferenceError):
    """Output was not valid JSON, or a required field was missing or empty."""