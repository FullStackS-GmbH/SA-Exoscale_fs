from exoscale_audit_helper import *


def inc(x):
    return x + 1


def test_api():
    get_data_from_api()
    assert inc(3) == 4
