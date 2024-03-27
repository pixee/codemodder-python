PYTEST = pytest -v
COV_FLAGS = --cov-fail-under=93.5 --cov=codemodder --cov=core_codemods
XDIST_FLAGS = --numprocesses auto

test:
	COVERAGE_CORE=sysmon ${PYTEST} ${COV_FLAGS} tests ${XDIST_FLAGS}

integration-test:
	${PYTEST} integration_tests ${XDIST_FLAGS}

pygoat-test:
	${PYTEST} -v ci_tests/test_pygoat_findings.py

lint:
	ruff check  src tests integration_tests --exclude tests/samples/

radon:
	radon cc codemodder --min A --total-average

# threshold for pipeline to fail if we go below average, module, or block complexity
# https://github.com/rubik/xenon
xenon:
	xenon codemodder --max-average A --max-modules C --max-absolute C
