FROM continuumio/miniconda3

ARG GITHUB_DEV_TOKEN
ENV CONTAINER_NAME "dashi-plm-container0"
ENV PATH "/home/nauts/.local/bin:/opt/conda/bin:${PATH}"
ENV NAUTS_HOME /user/nauts
ENV NAUTS_LOCAL_ROOT ""
ENV ARROW_LIBHDFS_DIR=$HADOOP_HOME/../usr/lib

WORKDIR ${NAUTS_HOME}

COPY resources resources/
COPY experiments/nauts/resources experiments/nauts/resources/
COPY src/dashi dashi/
COPY nauts_infer.yml .

RUN apt-get update && apt-get -y install gcc

RUN useradd -U -s /bin/bash -u 2002 -m nauts && chown -R nauts:nauts ${NAUTS_HOME} && chown -R nauts:nauts /opt/conda
USER nauts


RUN echo "source /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
RUN echo "conda env create -n nauts_infer -f nauts_infer.yml" >> ~/.bashrc
RUN echo "conda activate nauts_infer" >> ~/.bashrc

# TODO for bitbucket
# RUN echo "pip install git+https://${GITHUB_DEV_TOKEN}@github.com/[YOUR_TEAM_NAME]/tunip.git@v0.0.14" >> ~/.bashrc
# RUN echo "pip install git+https://${GITHUB_DEV_TOKEN}@github.com/[YOUR_TEAM_NAME]/tweak.git@v0.0.1" >> ~/.bashrc

# for github
RUN echo "pip install git+https://${GITHUB_DEV_TOKEN}@github.com/[YOUR_TEAM_NAME]/tunip.git@v0.0.14" >> ~/.bashrc
RUN echo "pip install git+https://${GITHUB_DEV_TOKEN}@github.com/[YOUR_TEAM_NAME]/tweak.git@v0.0.1" >> ~/.bashrc

ENTRYPOINT uvicorn dashi.pl_model.runner:app --host 0.0.0.0 --port 8080
# RUN /bin/bash -C 
