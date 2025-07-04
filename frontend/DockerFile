FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install 

# Copy the rest of the application code
COPY . .

# Set the environment 
ARG REACT_APP_HELLO_SERVICE_URL
ARG REACT_APP_PROFILE_SERVICE_URL
ENV REACT_APP_HELLO_SERVICE_URL=$REACT_APP_HELLO_SERVICE_URL
ENV REACT_APP_PROFILE_SERVICE_URL=$REACT_APP_PROFILE_SERVICE_URL
RUN npm run build

# Build the application
EXPOSE 3000

# Start the application
CMD ["npm", "run", "start"]

