PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
SKILLDIR ?= $(HOME)/.codex/skills/mfano-labctl

.PHONY: install-local install-skill check test

# Keep the command connected to this checkout, including its hashes and evidence.
install-local:
	@test -x "$(CURDIR)/labctl" || { printf '%s\n' 'labctl must be executable.' >&2; exit 1; }
	@mkdir -p "$(DESTDIR)$(BINDIR)"
	@if [ -e "$(DESTDIR)$(BINDIR)/labctl" ] || [ -L "$(DESTDIR)$(BINDIR)/labctl" ]; then \
		[ "$$(readlink -f -- "$(DESTDIR)$(BINDIR)/labctl")" = "$(CURDIR)/labctl" ] || \
		{ printf '%s\n' 'A different labctl already exists; choose another BINDIR.' >&2; exit 1; }; \
	else \
		ln -s -- "$(CURDIR)/labctl" "$(DESTDIR)$(BINDIR)/labctl"; \
	fi
	@printf 'Installed %s\n' "$(DESTDIR)$(BINDIR)/labctl"

install-skill:
	@test ! -e "$(SKILLDIR)" || { printf '%s\n' 'Skill directory already exists; review it before replacing it.' >&2; exit 1; }
	@mkdir -p "$(SKILLDIR)"
	@cp -- "cli/skills/mfano-labctl/SKILL.md" "$(SKILLDIR)/SKILL.md"

check:
	bash -n labctl
	bash -n cli/lib/core.sh
	bash -n cli/lib/ui.sh
	jq -e . cli/challenges.json >/dev/null
	shellcheck -x labctl
	python3 -B -c 'import ast; from pathlib import Path; ast.parse(Path("linux-files/lab.py").read_text())'

test:
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider tests/test_bash_cli.py
