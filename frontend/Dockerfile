# 컷앤킵 Frontend 이미지 (Vite 빌드 → nginx 정적 서빙)

# --- 빌드 단계 ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# --- 프로덕션 단계 ---
FROM nginx:alpine
# 빌드 산출물(dist) 을 nginx 문서 루트로 복사
COPY --from=builder /app/dist /usr/share/nginx/html
# /api · /health 프록시 설정
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
