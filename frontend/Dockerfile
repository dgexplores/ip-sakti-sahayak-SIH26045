FROM node:20-alpine
WORKDIR /app

# Copy the lockfile too, and use `npm ci`. This used to `COPY package.json ./`
# and run `npm install`, so the image resolved fresh ranges on every build and
# a container could ship a different dependency tree than the one the repo
# pins — with no way to tell the two apart afterwards.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000
# The compose service overrides the command with `npm run dev` for local work.
# Standing on its own, the image should serve a production build.
RUN npm run build
CMD ["npm", "run", "start"]
