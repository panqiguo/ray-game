.PHONY: web web-stage web-serve web-package web-upload web-clean

WEB_STAGE_DIR := build/sincity
WEB_DIST_DIR := build/web
WEB_ITCH_ZIP := build/sincity-itch.zip
BUTLER ?= butler
ITCH_CHANNEL ?= html5

# Prepare a minimal app folder for pygbag.
# We intentionally avoid packaging the repository root because that pulls in
# local-only files such as .venv, build caches, and platform-specific binaries.
web-stage:
	rm -rf $(WEB_STAGE_DIR)
	mkdir -p $(WEB_STAGE_DIR)/src
	rsync -a main.py font.ttf $(WEB_STAGE_DIR)/
	rsync -a src/sincity $(WEB_STAGE_DIR)/src/

# Build web version for itch.io.
# Output: build/web/ (contains index.html, tar.gz, and all assets ready for itch.io)
# Note: pygbag generates both .apk and .tar.gz; we keep both for compatibility.
web:
	uv sync --group web
	$(MAKE) web-stage
	uv run python -m pygbag --build $(WEB_STAGE_DIR)
	rm -rf $(WEB_DIST_DIR)
	mkdir -p $(WEB_DIST_DIR)
	rsync -a $(WEB_STAGE_DIR)/build/web/ $(WEB_DIST_DIR)/
	uv run python scripts/fix_web_index.py $(WEB_DIST_DIR)/index.html
	@echo "✓ Web build complete: $(WEB_DIST_DIR)/"
	@echo "  Contains: index.html, sincity.tar.gz, sincity.apk"
	@echo "  Ready to upload to itch.io"

# Create the final itch.io upload zip from build/web.
# Files are zipped at the archive root so itch can serve index.html directly.
web-package: web
	rm -f $(WEB_ITCH_ZIP)
	cd $(WEB_DIST_DIR) && zip -r ../$(notdir $(WEB_ITCH_ZIP)) .
	@echo "✓ itch.io upload zip ready: $(WEB_ITCH_ZIP)"

# Upload the final web package to itch.io with butler.
# Usage:
#   make web-upload ITCH_USER=<itch-user> ITCH_GAME=<itch-game>
# Optional:
#   make web-upload ITCH_USER=<itch-user> ITCH_GAME=<itch-game> ITCH_CHANNEL=html5
web-upload: web-package
	@test -n "$(ITCH_USER)" || (echo "Missing ITCH_USER. Usage: make web-upload ITCH_USER=<itch-user> ITCH_GAME=<itch-game>"; exit 1)
	@test -n "$(ITCH_GAME)" || (echo "Missing ITCH_GAME. Usage: make web-upload ITCH_USER=<itch-user> ITCH_GAME=<itch-game>"; exit 1)
	@command -v $(BUTLER) >/dev/null || (echo "Missing butler. Install it from https://itch.io/docs/butler/"; exit 1)
	$(BUTLER) push $(WEB_ITCH_ZIP) $(ITCH_USER)/$(ITCH_GAME):$(ITCH_CHANNEL)

# Remove intermediate build outputs and old debug artefacts.
# Keeps the final web build plus the itch upload zip.
web-clean:
	rm -rf build/web-cache build/web-app build/sincity web_probe_pyray/build
	find build -name '.DS_Store' -delete
	rm -f build/web.zip

# Serve the built web version locally (for testing before uploading to itch.io)
web-serve:
	@echo "Serving at http://127.0.0.1:8000/"
	uv run python -m http.server 8000 --bind 127.0.0.1 --directory $(WEB_DIST_DIR)
