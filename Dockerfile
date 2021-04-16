# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.7}

FROM condaforge/mambaforge AS base


RUN apt-get update

RUN apt-get install -y \
    gcc \
    wget


RUN mamba install -c ome omero-py
ARG INSTALL_NODE_VERSION=${INSTALL_NODE_VERSION:-12}
RUN mamba install nodejs=${INSTALL_NODE_VERSION}


WORKDIR /app
COPY requirements requirements

COPY . .

RUN useradd -m sid
RUN chown -R sid:sid /app
USER sid

RUN echo "python version: " && which python
RUN python -c "import sys; print(sys.version)"

ENV PATH="/home/sid/.local/bin:${PATH}"
RUN npm install

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
