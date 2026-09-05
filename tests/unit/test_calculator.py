from tools.calculator import calculator


def test_add():
    result = calculator.invoke({"first_num": 2, "second_num": 3, "operation": "add"})
    assert result["result"] == 5


def test_sub():
    result = calculator.invoke({"first_num": 5, "second_num": 3, "operation": "sub"})
    assert result["result"] == 2


def test_mul():
    result = calculator.invoke({"first_num": 4, "second_num": 3, "operation": "mul"})
    assert result["result"] == 12


def test_div():
    result = calculator.invoke({"first_num": 10, "second_num": 4, "operation": "div"})
    assert result["result"] == 2.5


def test_div_by_zero_is_an_error_not_an_exception():
    result = calculator.invoke({"first_num": 1, "second_num": 0, "operation": "div"})
    assert "error" in result


def test_unsupported_operation_is_an_error():
    result = calculator.invoke({"first_num": 1, "second_num": 2, "operation": "pow"})
    assert "error" in result
