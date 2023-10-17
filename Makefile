PYTEST = pytest -v
COV_FLAGS = --cov-fail-under=95 --cov=codemodder --cov=core_codemods
XDIST_FLAGS = --numprocesses auto

test:
	${PYTEST} ${COV_FLAGS} tests ${XDIST_FLAGS}

integration-test:
	${PYTEST} integration_tests

pygoat-test:
	${PYTEST} -v ci_tests/test_pygoat_findings.py

lint:
	pylint -v codemodder core_codemods tests integration_tests

radon:
	radon cc codemodder --min A --total-average

# threshold for pipeline to fail if we go below average, module, or block complexity
# https://github.com/rubik/xenon
xenon:
	xenon codemodder --max-average A --max-modules C --max-absolute C
