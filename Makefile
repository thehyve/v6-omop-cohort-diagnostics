TAG ?= cotopaxi
REGISTRY ?= harbor2.vantage6.ai
PLATFORMS ?= linux/amd64
TAG=latest

BASE ?= 4.5

PUSH_REG ?= false

# We use a conditional (true on any non-empty string) later. To avoid
# accidents, we don't use user-controlled PUSH_REG directly.
# See: https://www.gnu.org/software/make/manual/html_node/Conditional-Functions.html
_condition_push :=
ifeq ($(PUSH_REG), true)
	_condition_push := not_empty_so_true
endif

help:
	@echo "Usage:"
	@echo "  make build"
	@echo "  make help"
	@echo ""
	@echo "Using "
	@echo "  tag:       ${TAG}"
	@echo "  registry:  ${REGISTRY}"
	@echo "  base:      ${BASE}"
	@echo "  platforms: ${PLATFORMS}"

build:
	@echo "Building ${REGISTRY}/blueberry/v6-omop-cohort-diagnostics:${TAG}"
	docker buildx build \
		--tag ${REGISTRY}/blueberry/v6-omop-cohort-diagnostics:${TAG} \
		--tag ${REGISTRY}/blueberry/v6-omop-cohort-diagnostics:latest \
		--platform ${PLATFORMS} \
		--build-arg TAG=${TAG} \
		--build-arg BASE=${BASE} \
		-f ./Dockerfile \
		$(if ${_condition_push},--push .,.)