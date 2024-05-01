PYTEST = pytest -v
COV_FLAGS = --cov=codemodder --cov=core_codemods
XDIST_FLAGS = --numprocesses auto

test:
	COVERAGE_CORE=sysmon ${PYTEST} ${COV_FLAGS} tests ${XDIST_FLAGS} && coverage json && coverage-threshold

integration-test:
	COVERAGE_CORE=sysmon ${PYTEST} integration_tests --cov=core_codemods ${XDIST_FLAGS}  && coverage json && coverage-threshold --line-coverage-min 80

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
