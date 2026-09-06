#
# Colors
#

# Define ANSI color codes
RESET_COLOR   = \033[m

BLUE       = \033[1;34m
YELLOW     = \033[1;33m
GREEN      = \033[1;32m
RED        = \033[1;31m
BLACK      = \033[1;30m
MAGENTA    = \033[1;35m
CYAN       = \033[1;36m
WHITE      = \033[1;37m

DBLUE      = \033[0;34m
DYELLOW    = \033[0;33m
DGREEN     = \033[0;32m
DRED       = \033[0;31m
DBLACK     = \033[0;30m
DMAGENTA   = \033[0;35m
DCYAN      = \033[0;36m
DWHITE     = \033[0;37m

BG_WHITE   = \033[47m
BG_RED     = \033[41m
BG_GREEN   = \033[42m
BG_YELLOW  = \033[43m
BG_BLUE    = \033[44m
BG_MAGENTA = \033[45m
BG_CYAN    = \033[46m

# Name some of the colors
COM_COLOR   = $(DBLUE)
OBJ_COLOR   = $(DCYAN)
OK_COLOR    = $(DGREEN)
ERROR_COLOR = $(DRED)
WARN_COLOR  = $(DYELLOW)
NO_COLOR    = $(RESET_COLOR)

OK_STRING    = "[OK]"
ERROR_STRING = "[ERROR]"
WARN_STRING  = "[WARNING]"

define banner
    @echo "  $(WHITE)__________$(RESET_COLOR)"
    @echo "$(WHITE) |$(DWHITE)PALEWIRE⚡$(RESET_COLOR)$(WHITE)|$(RESET_COLOR)"
    @echo "$(WHITE) |&&& ======|$(RESET_COLOR)"
    @echo "$(WHITE) |=== ======|$(RESET_COLOR)  $(DWHITE)This is a $(RESET_COLOR)$(DBLACK)$(BG_WHITE)@palewire$(RESET_COLOR)$(DWHITE) automation$(RESET_COLOR)"
    @echo "$(WHITE) |=== == %%%|$(RESET_COLOR)"
    @echo "$(WHITE) |[_] ======|$(RESET_COLOR)  $(1)"
    @echo "$(WHITE) |=== ===!##|$(RESET_COLOR)"
    @echo "$(WHITE) |__________|$(RESET_COLOR)"
    @echo ""
endef

#
# Python helpers
#

UV ?= env -u UV_ENV_FILE uv
UV_RUN := $(UV) run
PYTHON := $(UV_RUN) python -W ignore -m

define python
    @echo "🐍🤖 $(OBJ_COLOR)Executing Python script $(1)$(NO_COLOR)\r";
    @$(PYTHON) $(1)
endef

#
# Commands
#


download: ## Download data
	$(call banner,    🔽 Downloading data 🔽)
	@$(PYTHON) muckrockbot.download


transform: ## Transforming data
	$(call banner,  🪢 Transforming data 🪢)
	@$(PYTHON) muckrockbot.transform


tweet: ## Tweet new data
	$(call banner,       🐦 Tweeting 🐦)
	@$(PYTHON) muckrockbot.tweet


toot: ## Toot new data
	$(call banner,       🐘 Tooting 🐘)
	@$(PYTHON) muckrockbot.toot

#
# Tests
#

install-dev: ## install locked development dependencies
	$(call banner,     📦 Installing development tools 📦)
	@$(UV) sync --locked --group dev


lint: ## run the linter
	$(call banner,        💅 Linting code 💅)
	@$(UV_RUN) ruff check .


format-check: ## check code formatting
	$(call banner,      🪥 Checking code formatting 🪥)
	@$(UV_RUN) ruff format --check .


type-check: ## run static type checks
	$(call banner,        🔩 Running type checks 🔩)
	@$(UV_RUN) ty check


check: lint format-check type-check ## run all quality checks


test: ## run all tests
	$(call banner,       🤖 Running tests 🤖)
	@$(UV_RUN) pytest -sv --cov=muckrockbot

#
# Extras
#

format: ## automatically format Python code
	$(call banner,       🪥 Cleaning code 🪥)
	@$(UV_RUN) ruff format .


fix: ## automatically fix lint and formatting issues
	$(call banner,       🪥 Fixing code issues 🪥)
	@$(UV_RUN) ruff check --fix .
	@$(UV_RUN) ruff format .


hooks: ## install git hooks
	@$(UV_RUN) pre-commit install --install-hooks
	@$(UV_RUN) pre-commit install --hook-type pre-push


help: ## Show this help. Example: make help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


# Mark all the commands that don't have a target
.PHONY: all \
        download \
        check \
        fix \
        format-check \
        help \
        hooks \
        install-dev \
        format \
        lint \
        test \
        type-check
