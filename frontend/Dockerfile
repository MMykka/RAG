# Stage 1: build the React app with Node
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Nginx serves the built files
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
