# 컷앤킵 Frontend 이미지 (Vite 빌드 → nginx 정적 서빙)

# --- 빌드 단계 ---
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# 개인정보 처리방침 · 이용약관의 운영자 정보 (src/data/legal.ts) — compose 가 .env 의 OPERATOR_* 를 넘긴다
ARG VITE_OPERATOR_NAME=""
ARG VITE_OPERATOR_EMAIL=""
ARG VITE_POLICY_DATE=""
ARG VITE_FEEDBACK_IMAGE_DAYS=""
ENV VITE_OPERATOR_NAME=$VITE_OPERATOR_NAME VITE_OPERATOR_EMAIL=$VITE_OPERATOR_EMAIL VITE_POLICY_DATE=$VITE_POLICY_DATE VITE_FEEDBACK_IMAGE_DAYS=$VITE_FEEDBACK_IMAGE_DAYS
RUN npm run build

# --- 프로덕션 단계 ---
FROM nginx:alpine
# 빌드 산출물(dist) 을 nginx 문서 루트로 복사
COPY --from=builder /app/dist /usr/share/nginx/html
# /api · /health 프록시 설정
COPY nginx.conf /etc/nginx/conf.d/default.conf
# HTTPS 모드에서 Caddy 뒤 실제 IP 설정을 끼워 넣는 자리 (평소엔 비어 있다)
RUN mkdir -p /etc/nginx/snippets
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
