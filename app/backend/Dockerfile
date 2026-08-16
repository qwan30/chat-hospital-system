# -- Stage 1: Build dependencies --------------------------------------
# Alpine keeps the runtime image free of the Debian base packages that are
# not required by this service (including Perl and ncurses utilities).
FROM python:3.11-alpine3.23 AS builder

WORKDIR /build

RUN apk add --no-cache --virtual .build-deps \
    build-base postgresql-dev

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install \
    $(python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(' '.join(d['project']['dependencies']+d['project']['optional-dependencies']['postgres']))")

# -- Stage 2: Production image ----------------------------------------
FROM python:3.11-alpine3.23

WORKDIR /app

RUN apk add --no-cache libpq libstdc++ && \
    addgroup -S appuser && adduser -S -G appuser appuser

RUN mkdir -p /data/storage && chown -R appuser:appuser /data

COPY --from=builder /install /usr/local

# The application does not install packages at runtime. Remove the package
# manager and build helpers from the production image so their bundled
# vulnerabilities cannot ship with the service.
RUN python -m pip uninstall --disable-pip-version-check --no-input --yes \
    pip setuptools wheel && \
    rm -rf /root/.cache/pip /usr/local/bin/pip /usr/local/bin/pip3

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY scripts/ scripts/
COPY data/ data/

# Run as non-root
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.getenv('PORT', '8000') + os.getenv('HOSPITAL_AI_API_V1_PREFIX', '/api/v1') + '/health')" || exit 1

CMD ["sh", "-c", "exec uvicorn hospital_ai.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --app-dir src"]
