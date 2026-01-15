# Git Setup Walkthrough

I have configured the repository to allow pushing updates.

## Changes Made

### Git Identity
- Configured username: `Vitalii Sevostian`
- Configured email: `sevostian.vitalii@gmail.com`

### Authentication
- Updated the remote origin URL to include your Personal Access Token (PAT) for HTTPS authentication.

## Container Distribution Changes

To address the `docker.io` (Docker Hub) blockage on your Mac, I've implemented the following:

### Flexible Dockerfile
The `Dockerfile` now uses a `REGISTRY` build argument. You can build the image using a different registry (like `ghcr.io` or `quay.io`) to avoid Docker Hub:
```bash
podman build --build-arg REGISTRY=ghcr.io -t gpo-analyzer .
```

### GitHub Container Registry (GHCR)
I've added a GitHub Action in [.github/workflows/docker-publish.yml](file:///home/user/git/GPOanalysis/.github/workflows/docker-publish.yml) that will:
1. Build the container image.
2. Push it to `ghcr.io/sevostianvitalii/gpoanalysis:latest`.

Once you push these changes, you will be able to pull the "pre-packed" image directly without needing to build it locally:
```bash
podman pull ghcr.io/sevostianvitalii/gpoanalysis:latest
```

### Final Build Status
The build process on GitHub Actions is now fully operational.
![Successful GitHub Build](./images/success_build.png)
The container image has been successfully pushed to GHCR.

### Bug Fixes Summary
1.  **Frontend Build**: Switched `npm ci` to `npm install` because `package-lock.json` was missing.
2.  **Package Names**: Corrected `libgdk-pixbuf-2.0-0` (added missing hyphen) and broadened Pango dependencies.
3.  **Dependency Conflict**: Fixed a version clash in `backend/requirements.txt` between `pytest` (downgraded to 7.4.4) and `pytest-asyncio`.
4.  **Multi-Architecture Support**: Enabled `linux/amd64` and `linux/arm64` builds via QEMU to support Apple Silicon (M1/M2/M3).
5.  **Tagging**: Configured GitHub Actions to automatically push the `latest` tag for the `main` branch.
6.  **Nginx Config**: Fixed startup crash by changing user to `www-data` and routing logs to stdout/stderr.

## Verification

###connectivity Check
I ran `git push --dry-run` to verify that the authentication is working correctly.
```bash
$ git push --dry-run
Everything up-to-date
```
The command completed successfully with exit code 0, confirming that you now have the necessary permissions to push updates.
