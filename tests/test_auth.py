"""Web-only auth test (HTTP Basic crew-password gate). Not applicable to the
MCP-server build -- the connector handles auth, not a web password. Neutralized
in the port; the original lives in the untouched web project."""
if __name__ == "__main__":
    print("skipped: auth is web-only (MCP build)")
