FROM ubuntu:16.04

ENV LAST_UPDATE=2019-10-19

# Install.
RUN \
  apt-get -y update && \
  apt-get -y upgrade && \
  apt-get -y install git wget default-jdk
RUN apt-get -y install curl wget nfs-common cifs-utils smbclient sshpass gettext libfontconfig git
RUN apt-get -y install python python-pip
RUN pip install pyyaml requests flask sqlalchemy
RUN \
  wget -O cfcli.tgz "https://cli.run.pivotal.io/stable?release=linux64-binary&source=github" && \
  tar -xvzf cfcli.tgz && \
  chmod 755 cf && \
  mv cf /usr/bin
RUN \
  wget -O jq "https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64" && \
  chmod 755 ./jq && \
  mv ./jq /usr/bin
RUN \
  wget "https://github.com/concourse/concourse/releases/download/v5.5.1/fly-5.5.1-linux-amd64.tgz" -O fly.tgz && \
  tar xvf fly.tgz && \
  chmod 755 ./fly && \
  mv ./fly /usr/local/bin/fly
RUN \
  wget -O phantomjs.tar.bz2 "https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2" && \
  tar -xvjf phantomjs.tar.bz2 && \
  cd phantomjs-2.1.1-linux-x86_64/bin && \
  chmod 755 ./phantomjs && \
  mv ./phantomjs /usr/bin
RUN \
  curl -LO https://github.com/pivotal-cf/pivnet-cli/releases/download/v0.0.76/pivnet-linux-amd64-0.0.76 && \
  mv pivnet-* pivnet && \
  chmod a+x pivnet && \
  mv ./pivnet /usr/bin
RUN \
  curl -LO https://github.com/cloudfoundry/bosh-cli/releases/download/v6.1.1/bosh-cli-6.1.1-linux-amd64 && \
  mv bosh-cli-* bosh && \
  chmod a+x bosh && \
  mv ./bosh /usr/bin
ADD https://github.com/krishicks/yaml-patch/releases/download/v0.0.9/yaml_patch_linux /usr/local/bin/yaml-patch
RUN chmod u+x /usr/local/bin/yaml-patch
RUN \
  wget -O hugo_0.38.tar.gz "https://github.com/gohugoio/hugo/releases/download/v0.38/hugo_0.38_Linux-64bit.tar.gz" && \
  tar -xvzf hugo_0.38.tar.gz && \
  chmod 755 ./hugo && \
  mv ./hugo /usr/bin
RUN wget https://github.com/open-policy-agent/opa/releases/download/v0.18.0/opa_linux_amd64 && mv opa_linux_amd64 /usr/local/bin/opa && chmod 755 /usr/local/bin/opa
RUN \
  mkdir -p /goroot && \
  curl https://storage.googleapis.com/golang/go1.7.6.linux-amd64.tar.gz | tar xvzf - -C /goroot --strip-components=1
ENV GOROOT /goroot
ENV GOPATH /gopath
ENV PATH $GOROOT/bin:$GOPATH/bin:$PATH
