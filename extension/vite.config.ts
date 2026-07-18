import { defineConfig } from "vite";
import { resolve, join, dirname } from "path";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from '@tailwindcss/vite'
import JSZip from "jszip";
import { writeFileSync, readdirSync, statSync, readFileSync, mkdirSync } from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

import manifest from "./public/manifest.json";
const version = manifest.version;

// Custom plugin to zip dist contents
function zipDistContents() {
  return {
    name: 'zip-dist-contents',
    writeBundle() {
      const distPath = resolve(__dirname, "dist");
      const zipPath = resolve(__dirname, "zip");
      const zipName = `pdf-editor${version}.zip`;
      
      const zip = new JSZip();
      
      function addFilesToZip(dirPath: string, zipFolder: JSZip) {
        const items = readdirSync(dirPath);
        
        for (const item of items) {
          const itemPath = join(dirPath, item);
          const stat = statSync(itemPath);
          
          if (stat.isDirectory()) {
            const folder = zipFolder.folder(item);
            if (folder) {
              addFilesToZip(itemPath, folder);
            }
          } else {
            const content = readFileSync(itemPath);
            zipFolder.file(item, content);
          }
        }
      }
      
      addFilesToZip(distPath, zip);
      
      zip.generateAsync({ type: "nodebuffer" }).then((content) => {
        // Ensure zip directory exists
        try {
          readdirSync(zipPath);
        } catch {
          mkdirSync(zipPath, { recursive: true });
        }
        
        writeFileSync(join(zipPath, zipName), content);
        console.log(`✅ Created ${zipName} with dist contents`);
      });
    }
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), zipDistContents()],
  build: {
    rollupOptions: {
      input: {
        options: resolve(__dirname, "options.html"),
        editor: resolve(__dirname, "editor.html"),
        service_worker: resolve(__dirname, "src/service_worker.ts")
      },
      output: {
        chunkFileNames: "[name].[hash].js",
        assetFileNames: "[name].[hash].[ext]",
        entryFileNames: "[name].js",
        dir: "dist",
      },
    },
  },
});
