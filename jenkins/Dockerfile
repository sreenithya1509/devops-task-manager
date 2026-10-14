FROM docker:28-cli AS dockercli
FROM jenkins/jenkins:lts-jdk21
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv curl ca-certificates git && rm -rf /var/lib/apt/lists/*
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
ARG KUBECTL_VERSION=v1.35.0
RUN case "$(dpkg --print-architecture)" in amd64) arch=amd64;; arm64) arch=arm64;; *) exit 1;; esac \
    && curl -fsSLo /tmp/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${arch}/kubectl" \
    && curl -fsSLo /tmp/kubectl.sha256 "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${arch}/kubectl.sha256" \
    && cd /tmp && echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check \
    && install -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl kubectl.sha256
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY --from=dockercli /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins
USER jenkins
