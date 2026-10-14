# Verification record — 14 October 2026

## Passed

- Python 3.12.6 and Git available; empty initial workspace inspected.
- Project dependencies installed in `.venv`; `python -m pip check` reports no broken requirements.
- `.venv\Scripts\python.exe -m pytest -q --junitxml=reports/pytest.xml`: **20 passed**; XML generated.
- `node --check static/script.js`: passed.
- Real HTTP smoke test using a temporary Werkzeug server on localhost port 5055: homepage 200, health 200, version 1.0.0, creation 201, listing 200, completion 200, deletion 204, empty list afterward. Server stopped after verification.
- Kubernetes YAML parsed with PyYAML 6.0.2; Deployment/Service kinds, matching selectors, single replica, image substitution, health probes, and read-only filesystem fields checked.
- Deployment renderer rejects malformed images and `latest`.
- PowerShell parser reports no syntax errors for `scripts/export-kubeconfig.ps1`.
- Host-accessible browser preview succeeded: created a task, marked it complete, verified counts 1 total / 0 pending / 1 completed, deleted it, and verified the empty state and zero counts. Screenshot: `reports/browser-preview.jpg`.

## Environment limits / still to run

- WSL command exists, but `wsl --status` reports WSL is not installed.
- Docker, kubectl, and Minikube executables are unavailable; Docker Desktop directory was not found.
- Dockerfiles are implemented but **not built or run** here. Non-root Gunicorn startup and container health must still be verified with the README commands.
- YAML parsing is **not** Kubernetes API-schema validation. `scripts/deploy.py --dry-run server` remains to run after cluster installation.
- Jenkinsfile is implemented and manually reviewed; no Jenkins controller is available to validate Declarative syntax or execute stages.
- Jenkins-to-Minikube networking/certificates and socket group access have an explicit preflight in README, but remain untested on this machine.
- No GitHub repository URL, Docker Hub repository/account token, or Jenkins credential bindings were provided. No repository or image was published; no credentials were created.
- End-to-end pipeline, Docker Hub push, deployment, polling/webhook trigger, and second-version rollout are **not verified**.
- Initial browser preview and cross-process HTTP requests to the sandboxed server timed out. Retrying with a host-accessible server succeeded, as did the same-process HTTP smoke test. Desktop layout inspected; narrow mobile viewport remains untested.

## Resume

### Phase 1 follow-up inspection

Latest host environment inspection:

- Windows 11 Home Single Language, 64-bit, build 26200.
- AMD Ryzen 7 5700U; firmware virtualization enabled; HypervisorPresent=True; approximately 15.3 GiB RAM. CPU VM monitor/SLAT fields returned False under the active hypervisor, so these fields alone are not a failed virtualization diagnosis.
- winget v1.29.380; Git 2.51.2.windows.1; Java 23.0.1 verified. Jenkins will use its image's JDK 21 rather than host Java.
- Host `wsl --version`, `wsl --status`, and `wsl --list --verbose` all report WSL is not installed.
- Docker, kubectl, and Minikube are not on host PATH; Docker Desktop was absent from the checked system and user installation locations.
- Latest application test run: **20 passed in 1.23 seconds**.
- No installers, administrator operations, restarts, or system-setting changes have been executed. WSL installation requires the user's administrator authorization and may require a restart.

- Re-ran the existing suite: **20 passed in 1.11 seconds**.
- Checked Docker/Gunicorn port 5000, worker count, Kubernetes selectors, deployment image rendering, credential IDs, and Jenkins tool setup for consistency.
- Added `timestamper` to `jenkins/plugins.txt`: the Jenkinsfile uses `timestamps()`, which requires that plugin. No application or test files changed.
- Installation remains user-guided, with verification output required before advancing. Docker builds, API-server validation, and Jenkins execution remain pending.

Follow README sections 1–9 in order: install WSL/Docker/kubectl/Minikube, verify a local container, configure public repositories, start the cluster, run server dry-run/deploy, build Jenkins, validate network access, upload credentials, run the pipeline, enable polling, and push a version/UI change. Record real build numbers, image tags, rollout outputs, and `/version` before presenting the end-to-end lab as complete.
