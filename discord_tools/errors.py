from typing import Optional, Union, Any

from tls_client.response import Response


class DiscordException(Exception):
    """
    discord.py의 기본 예외 클래스

    이상적으로는, 이 라이브러리에서 발생하는 모든 예외를 처리하기 위해 이 예외를 잡을 수 있습니다.
    """
    pass


class ClientException(DiscordException):
    """
    클라이언트(:class:`Client`)에서 작업이 실패할 때 발생하는 예외.

    보통 이 예외는 사용자 입력으로 인해 발생한 예외입니다.
    """
    pass


class GatewayNotFound(DiscordException):
    """Discord에 대한 게이트웨이를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self):
        message = "디스코드에 연결할 게이트웨이를 찾을 수 없습니다."
        super().__init__(message)


def _flatten_error_dict(d: dict[str, Any], key: str = '') -> dict[str, str]:
    items: list[tuple[str, str]] = []

    if '_errors' in d:
        items.append(('miscallenous', ' '.join(x.get('message', '') for x in d['_errors'])))
        d.pop('_errors')

    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors: list[dict[str, Any]] = v['_errors']
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DiscordException):
    """HTTP 요청 작업이 실패할 때 발생하는 예외.

    속성
    ------------
    response: :class:`aiohttp.ClientResponse`
        실패한 HTTP 요청의 응답입니다. 이는 :class:`aiohttp.ClientResponse` 인스턴스입니다.
        일부 경우에는 :class:`requests.Response` 일 수도 있습니다.
    text: :class:`str`
        오류의 텍스트입니다. 빈 문자열일 수 있습니다.
    status: :class:`int`
        HTTP 요청의 상태 코드입니다.
    code: :class:`int`
        실패에 대한 Discord 특정 오류 코드입니다.
    json: :class:`dict`
        원시 오류 JSON입니다.

        .. versionadded:: 2.0
    payment_id: Optional[:class:`int`]
        계속하려면 확인이 필요한 결제의 ID입니다.

        .. versionadded:: 2.0
    """
    
    def __init__(self, response: Response, message: Optional[Union[str, dict[str, Any]]]) -> None:
        self.response = response
        self.status: int = response.status_code
        
        self.code: int
        self.text: str
        self.json: dict[str, Any]
        self.payment_id: Optional[int]
        
        if isinstance(message, dict):
            self.json = message
            self.code = message.get("code", 0)
            
            base = message.get("message", "")
            errors = message.get("errors")
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = "\n".join(f"In {key}: {value}" for key, value in errors.items())
                
                self.text = base + '\n' + helpful
            
            else:
                self.text = base
        
        else:
            self.text = message or ""
            self.code = 0
            self.json = {}
            self.payment_id = None

        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt += ": {2}"
        
        super().__init__(fmt.format(self.response, self.code, self.text))


class RateLimited(DiscordException):
    """
    상태 코드 429가 발생하고 타임아웃이 :class:`Client`에서 설정된 최대 시간보다 클 때 발생하는 예외.

    이는 글로벌 레이트리미트 도중에는 발생하지 않습니다.

    때때로 요청이 만들어지기 전에 미리 중단되기 때문에,
    이 예외는 :exc:`HTTPException`의 서브클래스가 **아닙니다**.

    .. versionadded:: 2.0

    속성
    ------------
    retry_after: :class:`float`
        요청을 다시 시도하기 전에 클라이언트가 기다려야 하는 시간(초)입니다.
    """

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Too many requests. Retry in {retry_after:.2f} seconds.")


class Forbidden(HTTPException):
    """
    상태 코드 403이 발생할 때 발생하는 예외.

    :exc:`HTTPException`의 서브클래스
    """
    pass


class NotFound(HTTPException):
    """
    상태 코드 404가 발생할 때 발생하는 예외.

    :exc:`HTTPException`의 서브클래스
    """
    pass


class DiscordServerError(HTTPException):
    """
    500 범위 상태 코드가 발생할 때 발생하는 예외.

    :exc:`HTTPException`의 서브클래스.

    .. versionadded:: 1.5
    """
    pass


class CaptchaRequired(HTTPException):
    """
    캡차가 필요하고 처리되지 않았을 때 발생하는 예외.

    :exc:`HTTPException`의 서브클래스.

    .. versionadded:: 2.0
    """
    def __init__(self, response: Response, message: dict[str, any]):
        super().__init__(response, {"code": -1, "message": "Captcha required"})
        self.json = message


class InvalidData(ClientException):
    """
    라이브러리가 Discord로부터 알 수 없는 또는 잘못된 데이터를 받을 때 발생하는 예외.
    """
    pass


class LoginFailure(ClientException):
    """
    :meth:`Client.login` 함수가
    잘못된 자격 증명이나 기타 원인으로 인해 로그인에 실패할 때 발생하는 예외.
    """
    pass


AuthFailure = LoginFailure


