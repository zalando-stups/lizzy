test:
	python3 -m pytest --cov lizzy --cov-report term-missing

verbose-test:
	python3 -m pytest --cov lizzy \
	                  --cov-report term-missing \
	                  --cov-report xml \
	                  -v

ci-checks: verbose-test
	@:
