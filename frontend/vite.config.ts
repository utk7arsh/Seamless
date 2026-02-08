import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { execSync } from "child_process";
import { componentTagger } from "lovable-tagger";

const snowflakeMoviesPlugin = () => ({
  name: "snowflake-movies-api",
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url === "/api/movies" && req.method === "GET") {
        try {
          const scriptPath = path.resolve(__dirname, "scripts/snowflake-movies.cjs");
          const stdout = execSync(`node "${scriptPath}" fetch`, {
            encoding: "utf8",
            cwd: __dirname,
            env: { ...process.env },
          });
          res.setHeader("Content-Type", "application/json");
          res.end(stdout);
        } catch (err) {
          res.statusCode = 502;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: "Failed to fetch movies from Snowflake", detail: String(err?.message || err) }));
        }
        return;
      }
      next();
    });
  },
});

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
    proxy: {
      "/api/flowglad": {
        target: "https://app.flowglad.com",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/flowglad/, "/api/v1"),
      },
      "/api/discover": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
  plugins: [react(), snowflakeMoviesPlugin(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
