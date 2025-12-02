from typing import Any, Literal, TypedDict

from rest_framework import status as http_status
from rest_framework.renderers import JSONRenderer

StatusCategory = Literal[
    'informational',
    'success',
    'redirect',
    'client_error',
    'server_error',
]


class CustomResponseRenderer(JSONRenderer):
    """
    A custom renderer to wrap the API response in a standard 'template' format.

    {
        "status": "informational" | "success" |
                   "redirect" | "client_error" | "server_error",
        "code": <HTTP_STATUS_CODE>,
        "message": "Optional message",
        "data": <ACTUAL_RESPONSE_DATA>
    }.
    """

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        """Render the API response in the custom format."""
        # Default values
        status_code: int = 200
        response_status: StatusCategory = 'success'
        message: str | None = None

        # Get the response object from the context to access the
        # actual status code
        if renderer_context is not None:
            response = renderer_context.get('response')
            if response is not None:
                status_code = response.status_code

        # Determine status category and error message using DRF helpers
        response_status = self._status_category(status_code)
        if response_status in {'client_error', 'server_error'}:
            message = self._extract_error_message(data)

        # Construct the custom template structure
        custom_response: CustomResponse = {
            'status': response_status,
            'code': status_code,
            'message': message,
            'data': data,
        }

        # Call the superclass render method to serialize our custom
        # dictionary to JSON
        return super().render(
            custom_response, accepted_media_type, renderer_context
        )

    def _status_category(self, code: int) -> StatusCategory:
        """Map HTTP status code to DRF status category name."""
        if http_status.is_informational(code):
            return 'informational'
        if http_status.is_success(code):
            return 'success'
        if http_status.is_redirect(code):
            return 'redirect'
        if http_status.is_client_error(code):
            return 'client_error'
        if http_status.is_server_error(code):
            return 'server_error'
        return 'success'

    def _extract_error_message(self, data: Any) -> str | None:
        """Extract user-friendly error message from DRF error payload."""
        if isinstance(data, dict) and 'detail' in data:
            return data.pop('detail')
        if isinstance(data, list):
            return 'Validation failed'
        return None


class CustomResponse(TypedDict):
    """Type-safe shape of API custom response."""
    status: StatusCategory
    code: int
    message: str | None
    data: Any
