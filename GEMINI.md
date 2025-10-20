# Platform IDE

## Project Overview

This is a monorepo for **Platform IDE**, an integrated learning platform. It consists of a web-based application for interactive learning and a VSCode extension to connect the learning experience with the local development environment. The project also includes a sophisticated Python-based content generation pipeline.

### Key Components:

*   **`web-learner`**: A Next.js application that provides an online, interactive learning environment. It features a code editor, AI-assisted learning, and renders content from Markdown.
    *   **Framework**: Next.js
    *   **UI**: Tailwind CSS, Radix UI
    *   **State Management**: Zustand
*   **`learn-linker`**: A VSCode extension that integrates with the web platform. It allows users to get AI-powered code explanations and sync learning content.
    *   **Framework**: VSCode Extension API
    *   **Bundler**: Webpack
*   **Content Generation**: A collection of Python scripts in the `scripts/` directory that automatically generate learning outlines. This system uses a set of predefined "archetypes" and "switches" to create structured, high-quality educational content. The templates for this are in `prompt_archetype_templates.md`.

## Building and Running

The project uses `pnpm` as a package manager and for workspace management.

### Installation

```bash
# Install all dependencies for all packages
pnpm install
```

### Development

```bash
# Run both the web app and the VSCode extension in development mode
pnpm dev

# Run only the web app
pnpm dev:web

# Run only the VSCode extension in watch mode
pnpm dev:ext
```

### Building

```bash
# Build all packages
pnpm build

# Build only the web app
pnpm build:web

# Build only the VSCode extension
pnpm build:ext
```

### Content Generation

The content generation scripts are located in the `scripts/` directory. For example, to generate a learning outline:

```bash
# Generate an outline using the pipeline
python scripts/generate_outline_pipeline.py --topic "LangGraph 入门" --depth core --pretty
```

## Development Conventions

*   **Monorepo Management**: The project is a monorepo using `pnpm` workspaces. The configuration is in `pnpm-workspace.yaml`.
*   **TypeScript**: A base `tsconfig.base.json` is used for shared TypeScript settings.
*   **Styling**: The `web-learner` project uses Tailwind CSS for styling.
*   **VSCode Extension**: The `learn-linker` extension has its own build process using webpack, configured in `learn-linker/webpack.config.js`.
*   **Shared Packages**: The `packages/` directory is intended for code that can be shared between the web app and the VSCode extension.
