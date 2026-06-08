ARG PYTHON_IMAGE=docker.1ms.run/library/python:3.11-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

ENV MODELSCOPE_CACHE=/root/.cache/modelscope
ENV FUNASR_MODEL=iic/SenseVoiceSmall
ENV FUNASR_VAD_MODEL=fsmn-vad
ENV FUNASR_DEVICE=cpu

RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i \
        -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
        -e 's|http://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
        /etc/apt/sources.list.d/debian.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i \
        -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
        -e 's|http://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
        /etc/apt/sources.list; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt

COPY app ./app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
