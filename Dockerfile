# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.7}

FROM python:${INSTALL_PYTHON_VERSION}-slim-buster AS base

RUN sed -i "s#deb http://security.debian.org/debian-security stretch/updates main#deb http://deb.debian.org/debian-security stretch/updates main#g" /etc/apt/sources.list

RUN apt-get update

RUN apt-get install -y \
    gcc \
    curl \
    git \
    wget


ARG INSTALL_NODE_VERSION=${INSTALL_NODE_VERSION:-12}
RUN curl -sL https://deb.nodesource.com/setup_${INSTALL_NODE_VERSION}.x | bash -
RUN apt-get install -y \
    nodejs \
    && apt-get -y autoclean

WORKDIR /app
COPY requirements requirements

COPY . .

RUN useradd -m sid
RUN chown -R sid:sid /app
USER sid

ENV PATH="/home/sid/miniconda3/bin:${PATH}"
ARG PATH="/home/sid/miniconda3/bin:${PATH}"
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /home/sid/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh \

RUN echo 'export PATH=/home/sid/miniconda3/bin/:$PATH' >> ~/.bashrc

RUN echo "python version: " && which python
RUN python -c "import sys; print(sys.version)"

ENV PATH="/home/sid/.local/bin:${PATH}"
RUN npm install
RUN conda install -c ome omero-py

# ================================= DEVELOPMENT ================================
FROM base AS development
RUN pip install --user -r requirements/dev.txt
EXPOSE 2992
EXPOSE 5020
CMD [ "npm", "start" ]

# ================================= PRODUCTION =================================
FROM base AS production
RUN pip install --user -r requirements/prod.txt
COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY supervisord_programs /etc/supervisor/conf.d
EXPOSE 5020
ENTRYPOINT ["/bin/bash", "shell_scripts/supervisord_entrypoint.sh"]
CMD ["-c", "/etc/supervisor/supervisord.conf"]

# =================================== MANAGE ===================================
FROM base AS manage
RUN pip install --user -r requirements/dev.txt
ENTRYPOINT [ "flask" ]
