def assert_eq(a, b, msg=""):
    assert a == b, f"{repr(a)} != {repr(b)}" + (": " + msg) if len(msg) > 0 else ""
