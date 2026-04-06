.PHONY: web web-serve

# Build web version for itch.io
# Output: build/web/ (contains index.html, tar.gz, and all assets ready for itch.io)
# Note: pygbag generates both .apk and .tar.gz; we keep both for compatibility
web:
	mkdir -p build/web
	uv sync --group web
	uv run python -m pygbag .
	@echo "✓ Web build complete: build/web/"
	@echo "  Contains: index.html, ray-game.tar.gz, ray-game.apk"
	@echo "  Ready to upload to itch.io"

# Serve the built web version locally (for testing before uploading to itch.io)
web-serve:
	@echo "Serving at http://localhost:8000/"
	python -m http.server 8000 --directory build/web
