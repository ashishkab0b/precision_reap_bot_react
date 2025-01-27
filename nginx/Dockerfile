# Step 1: Build the React App
FROM node:18-alpine as react-build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json and install dependencies
COPY ./react_frontend/package.json ./react_frontend/package-lock.json ./
RUN npm install

# Copy the React app source code and build
COPY ./react_frontend ./
RUN npm run build

# Step 2: Use Nginx to Serve the Built React App
FROM nginx:alpine

# Copy Nginx configuration
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

# Copy built React files to Nginx's static directory
COPY --from=react-build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80
EXPOSE 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]