# Language Learner Frontend

A modern React application for language learning, built with TypeScript and Vite. Features include transcription, translation, and AI-powered language assistance using Google's Gemini API.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite 7** - Build tool and dev server
- **React Router** - Client-side routing
- **Lucide React** - Icon library
- **React Markdown** - Markdown rendering
- **React Player** - Audio/video playback

## Prerequisites

- **Node.js** >= 18.0.0
- **npm** >= 9.0.0

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   Copy `.env.template` to `.env` and add your API keys:
   ```bash
   cp .env.template .env
   ```
   
   Fill in the required variables in `.env`:
   ```
   VITE_TRANSCRIBE_API_KEY=your_whisper_api_key_here
   ```

## Development

Start the development server with hot module replacement (HMR):

```bash
npm run dev
```

The application will be available at `http://localhost:5173` by default.

**Features:**
- Fast refresh on code changes
- Type checking with TypeScript
- ESLint for code quality

### Linting

Check code for style and quality issues:

```bash
npm run lint
```

## Building for Production

### Build the application:

```bash
npm run build
```

This command:
1. Runs TypeScript compilation (`tsc -b`)
2. Optimizes the code with Vite
3. Outputs the production build to the `dist/` directory

The build is minified and ready for deployment.

### Preview the production build locally:

```bash
npm run preview
```

This serves the built files from the `dist/` directory at `http://localhost:5173`.

## Deployment

### Deploying to Production

The optimized build is located in the `dist/` directory. Deploy by:

1. **Using a hosting service** (Vercel, Netlify, etc.):
   - Connect your git repository
   - Set build command to: `npm run build`
   - Set publish directory to: `dist`

2. **Manual deployment to a static host**:
   ```bash
   npm run build
   # Upload contents of dist/ folder to your hosting
   ```

3. **Using Docker**:
   ```dockerfile
   # Build stage
   FROM node:18 AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   RUN npm run build

   # Runtime stage
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

### Environment Configuration

For production deployments, ensure:
- Set `VITE_TRANSCRIBE_API_KEY` as a secure environment variable (never commit actual keys)
- Configure CORS if the backend is on a different domain
- Use HTTPS in production
- Configure proper caching headers for static assets

### Performance Optimization

The production build includes:
- Code splitting and lazy loading
- Asset minification
- Tree-shaking of unused code
- Optimized dependency bundling

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   ├── pages/          # Page components
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── public/             # Static assets
├── dist/               # Production build (generated)
├── vite.config.ts      # Vite configuration
├── tsconfig.json       # TypeScript configuration
└── package.json        # Dependencies and scripts
```

## Troubleshooting

- **Port already in use**: Change the dev server port with `npm run dev -- --port 3000`
- **Build fails**: Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- **API key errors**: Verify `.env` file is set up correctly and restart the dev server

## Additional Resources

- [Vite Documentation](https://vite.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
