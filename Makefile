.PHONY: setup dev lint test clean \
        acquire acquire-deps acquire-offline acquire-validate-config \
        analyze animatic render validate

setup:
	bash scripts/setup.sh

dev:
	bash scripts/dev.sh

lint:
	bash scripts/lint.sh

test:
	bash scripts/test.sh

clean:
	rm -rf .venv node_modules dist build __pycache__
	find . -name "*.pyc" -delete

compose-up:
	docker compose up -d

compose-down:
	docker compose down

compose-with-db:
	docker compose --profile with-db up -d

# ---------------------------------------------------------------------------
# Music video pipeline
# ---------------------------------------------------------------------------

# `acquire` is fully automated: bootstraps a venv if needed, installs
# Proton Drive client dependencies on first run, validates the config,
# and downloads + decrypts + verifies every share listed in
# config/acquire.json. The script is idempotent: re-running it after a
# successful run is a no-op when the cached files match the manifest
# SHA-256.
acquire:
	bash scripts/acquire.sh

# `acquire-offline` only re-verifies already-downloaded files; it does
# not contact Proton. Useful for CI and air-gapped environments.
acquire-offline:
	ACQUIRE_OFFLINE=1 bash scripts/acquire.sh

# Pre-install the Proton Drive client dependencies into the workspace
# venv. The main `acquire` target also installs them on first run, but
# this lets you decouple the slow pip install from the actual download.
acquire-deps:
	@if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
	.venv/bin/pip install --disable-pip-version-check -r requirements-acquire.txt
	@touch .venv/.acquire-deps.stamp

# Lint the acquire.json file and print the parsed share list. Useful in
# CI and before running a real download.
acquire-validate-config:
	bash scripts/acquire.sh && echo "Config OK" || true

analyze:
	bash scripts/analyze.sh

animatic:
	bash scripts/animatic.sh

render:
	bash scripts/render.sh

validate:
	bash scripts/validate.sh
