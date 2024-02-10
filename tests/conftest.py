
# check if another TL has been specified
def pytest_addoption(parser):
    parser.addoption("--tl", action="store", default="None", help="Specifies the transport layer.")
