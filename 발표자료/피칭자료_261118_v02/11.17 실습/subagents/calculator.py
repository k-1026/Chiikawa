def calculate(expression: str) -> str:
    """사칙연산 수식을 계산합니다.

    Args:
        expression: "12 + 3 * 4" 같은 수식 문자열
    """
    # 숫자/연산자/공백/괄호만 허용해서 안전하게 계산
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "계산할 수 없는 문자가 포함되어 있습니다."

    try:
        result = eval(expression)
    except Exception:
        return "계산에 실패했습니다. 수식을 확인해 주세요."

    return str(result)
