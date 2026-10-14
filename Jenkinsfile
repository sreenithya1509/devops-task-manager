pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }
    parameters {
        string(name: 'GITHUB_REPO_URL', defaultValue: 'https://github.com/sreenithya1509/devops-task-manager.git', description: 'Trusted HTTPS GitHub repository URL')
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch to deploy')
        string(name: 'GITHUB_CREDENTIALS_ID', defaultValue: '', description: 'Optional username/token credential ID for private repositories')
        string(name: 'DOCKER_IMAGE', defaultValue: 'sree1509/devops-task-manager', description: 'Docker Hub username/repository without a tag')
        booleanParam(name: 'PUBLISH_LATEST', defaultValue: true, description: 'Also publish latest from main after tests and container verification pass')
        booleanParam(name: 'DEPLOY_TO_KUBERNETES', defaultValue: false, description: 'Enable only after Minikube access and minikube-kubeconfig credential are verified')
    }
    environment {
        DOCKERHUB_CREDENTIALS_ID = 'dockerhub-credentials'
        KUBE_CREDENTIALS_ID = 'minikube-kubeconfig'
        KUBE_CONTEXT = 'minikube'
    }
    stages {
        stage('Checkout') {
            steps {
                script {
                    if (!(params.GITHUB_REPO_URL ==~ /https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(?:\.git)?/)) {
                        error('Set GITHUB_REPO_URL to an HTTPS GitHub repository URL.')
                    }
                    if (!(params.DOCKER_IMAGE ==~ /[a-z0-9]+(?:[._-][a-z0-9]+)*\/[a-z0-9]+(?:[._-][a-z0-9]+)*/)) {
                        error('Set DOCKER_IMAGE to your Docker Hub username/repository, without a tag.')
                    }
                    if (!params.GIT_BRANCH.trim()) { error('Set GIT_BRANCH, normally main.') }
                    deleteDir()
                    def remote = [url: params.GITHUB_REPO_URL]
                    if (params.GITHUB_CREDENTIALS_ID.trim()) { remote.credentialsId = params.GITHUB_CREDENTIALS_ID.trim() }
                    checkout([$class: 'GitSCM', branches: [[name: params.GIT_BRANCH]], userRemoteConfigs: [remote]])
                    env.IMAGE_NAME = params.DOCKER_IMAGE
                    env.IMAGE_TAG = "build-${env.BUILD_NUMBER}-${sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()}"
                    env.FULL_IMAGE = "${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                    env.UPDATE_LATEST = (params.PUBLISH_LATEST && params.GIT_BRANCH == 'main').toString()
                }
            }
        }
        stage('Check Build Environment') {
            steps {
                sh '''
                    set -eu
                    command -v python3
                    command -v git
                    command -v docker
                    python3 --version
                    if ! docker info > /dev/null; then
                        echo 'Jenkins cannot access Docker Desktop. Configure the socket mount and matching socket group; see README section 8.'
                        exit 1
                    fi
                    docker buildx version
                '''
                script {
                    if (params.DEPLOY_TO_KUBERNETES) {
                        withCredentials([file(credentialsId: env.KUBE_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
                            sh 'kubectl --context "$KUBE_CONTEXT" --request-timeout=15s get nodes'
                        }
                    }
                }
            }
        }
        stage('Install Dependencies') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }
        stage('Test') {
            steps { sh '.venv/bin/python -m pytest -q --junitxml=reports/pytest.xml' }
            post { always { junit testResults: 'reports/pytest.xml', allowEmptyResults: true } }
        }
        stage('Build Docker Image') {
            steps { sh 'docker version && docker build --build-arg APP_VERSION="$IMAGE_TAG" -t "$FULL_IMAGE" .' }
        }
        stage('Verify Docker Image') {
            steps {
                sh '''
                    set -eu
                    container_id=$(docker run -d "$FULL_IMAGE")
                    trap 'docker logs "$container_id" || true; docker rm -f "$container_id" >/dev/null 2>&1 || true' EXIT
                    # No host port or workspace bind mount: Docker is a sibling daemon.
                    docker exec "$container_id" python -c 'import json,sys,time,urllib.request
for attempt in range(30):
    try:
        health=json.load(urllib.request.urlopen("http://127.0.0.1:5000/health",timeout=2))
        version=json.load(urllib.request.urlopen("http://127.0.0.1:5000/version",timeout=2))
    except (OSError,ValueError):
        time.sleep(1)
        continue
    assert health["status"]=="healthy", health
    assert version["version"]==sys.argv[1], version
    print("Container health and version verified:",version["version"])
    break
else:
    raise SystemExit("Container did not become healthy within 30 attempts")' "$IMAGE_TAG"
                '''
            }
        }
        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS_ID, usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        set +x
                        set -eu
                        test -n "$DOCKERHUB_USER" && test -n "$DOCKERHUB_TOKEN" || { echo 'Docker Hub credentials are empty.'; exit 1; }
                        export DOCKER_CONFIG="$(mktemp -d)"
                        trap 'docker logout >/dev/null 2>&1 || true; rm -rf "$DOCKER_CONFIG"' EXIT
                        printf '%s' "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
                        docker push "$FULL_IMAGE"
                        docker buildx imagetools inspect "$FULL_IMAGE"
                        if [ "$UPDATE_LATEST" = true ]; then
                            docker tag "$FULL_IMAGE" "$IMAGE_NAME:latest"
                            docker push "$IMAGE_NAME:latest"
                            docker buildx imagetools inspect "$IMAGE_NAME:latest"
                        fi
                    '''
                }
            }
        }
        stage('Deploy to Kubernetes') {
            when { expression { return params.DEPLOY_TO_KUBERNETES } }
            steps {
                withCredentials([file(credentialsId: env.KUBE_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
                    sh '''
                        set -eu
                        kubectl --context "$KUBE_CONTEXT" get nodes
                        .venv/bin/python scripts/deploy.py --context "$KUBE_CONTEXT" --image "$FULL_IMAGE" --dry-run server
                        .venv/bin/python scripts/deploy.py --context "$KUBE_CONTEXT" --image "$FULL_IMAGE"
                    '''
                }
            }
        }
        stage('Verify Deployment') {
            when { expression { return params.DEPLOY_TO_KUBERNETES } }
            steps {
                withCredentials([file(credentialsId: env.KUBE_CREDENTIALS_ID, variable: 'KUBECONFIG')]) {
                    sh '''
                        set -eu
                        kubectl --context "$KUBE_CONTEXT" rollout status deployment/task-manager --timeout=180s
                        kubectl --context "$KUBE_CONTEXT" get pods,svc -l app=task-manager
                        kubectl --context "$KUBE_CONTEXT" port-forward service/task-manager 15000:5000 > /tmp/task-manager-forward-$$.log 2>&1 &
                        forward_pid=$!
                        trap 'kill "$forward_pid" 2>/dev/null || true; wait "$forward_pid" 2>/dev/null || true; rm -f /tmp/task-manager-forward-$$.log' EXIT
                        curl --fail --retry 15 --retry-connrefused --retry-delay 1 --max-time 5 http://127.0.0.1:15000/health
                        .venv/bin/python -c 'import json,os,urllib.request; actual=json.load(urllib.request.urlopen("http://127.0.0.1:15000/version",timeout=5))["version"]; expected=os.environ["IMAGE_TAG"]; assert actual==expected, (actual,expected); print("Verified version:",actual)'
                    '''
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'reports/*.xml', allowEmptyArchive: true
            // Removes only this job's workspace, including its virtual environment.
            deleteDir()
        }
        failure { echo 'Pipeline failed. Check the first failed stage; confirm tool access and credential IDs dockerhub-credentials / minikube-kubeconfig.' }
    }
}
