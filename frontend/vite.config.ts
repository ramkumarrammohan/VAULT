import { fileURLToPath, URL } from 'node:url'
import { execSync } from 'node:child_process'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// Resolve the latest git tag in the repo (falls back to `git describe`,
// then the short commit hash, then 'dev')
const getGitVersion = (): string => {
  const run = (command: string) =>
    execSync(command, { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()

  // Highest version-numbered tag (handles v1.2.3 or 1.2.3 style), independent of
  // creation order and of whether the tag is reachable from the current branch
  try {
    const tag = run('git tag --sort=-v:refname').split(/\r?\n/)[0]
    if (tag) return tag
  } catch {
    // not a git repo / git not available
  }

  // Fallback: most recent tag reachable from HEAD
  try {
    const tag = run('git describe --tags --abbrev=0')
    if (tag) return tag
  } catch {
    // no reachable tags
  }

  try {
    return run('git rev-parse --short HEAD')
  } catch {
    return 'dev'
  }
}

// https://vite.dev/config/
export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(getGitVersion()),
  },
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
