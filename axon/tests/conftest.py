def pytest_addoption(parser):
    parser.addoption(
        '--tl', action='store', help='Specify the transport layer under test'
    )