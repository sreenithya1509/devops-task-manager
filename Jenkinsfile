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
        string(name: 'GITHUB_REPO_URL', defaultValue: '', description: 'HTTPS GitHub repository URL (required)')
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch to deploy')
        string(name: 'GITHUB_CREDENTIALS_ID', defaultValue: '', description: 'Optional username/token credential ID for private repositories')
        string(name: 'DOCKER_IMAGE', defaultValue: '', description: 'Docker Hub username/repository (required; public repository)')
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
                    '''
                }
            }
        }
        stage('Deploy to Kubernetes') {
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
