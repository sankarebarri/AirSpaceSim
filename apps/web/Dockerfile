# AirSpaceSim web image (build context: apps/web).
#
#   docker build --build-arg VITE_API_BASE_URL=https://api.example.com \
#     -t airspacesim-web apps/web
#
# Stage 1 builds the static bundle; stage 2 serves it with nginx and the
# SPA fallback so browser refresh works on any route. For static hosting
# platforms, deploy apps/web/dist/ directly instead (dist/_redirects
# carries the same fallback rule for hosts that understand it).

FROM node:20-alpine AS build
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html
EXPOSE 80
