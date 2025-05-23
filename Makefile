VANTAGE6_VERSION ?= 4.10.2
REGISTRY ?= registry.vantage6.local
PLATFORMS ?= linux/amd64
TAG ?= =latest
BASE ?= 4.5
IMAGE ?= omop-cohort-diagnostics

# We use a conditional (true on any non-empty string) later. To avoid
# accidents, we don't use user-controlled PUSH_REG directly.
# See: https://www.gnu.org/software/make/manual/html_node/Conditional-Functions.html
PUSH_REG ?= false
_condition_push :=
ifeq ($(PUSH_REG), true)
	_condition_push := not_empty_so_true
endif

help:
	@echo "Usage:"
	@echo "  make help      - show this message"
	@echo "  make image     - build the image"
	@echo ""
	@echo "Using "
	@echo "  registry:  ${REGISTRY}"
	@echo "  image:     ${IMAGE}"
	@echo "  tag:       v6-${VANTAGE6_VERSION}"
	@echo "  base:      ${BASE}"
	@echo "  platforms: ${PLATFORMS}"
	@echo "  vantage6:  ${VANTAGE6_VERSION}"
	@echo ""

image:
	@echo "Building ${REGISTRY}/${IMAGE}:v6-${VANTAGE6_VERSION}"
	@echo "Building ${REGISTRY}/${IMAGE}:latest"
	docker buildx build \
		--tag ${REGISTRY}/${IMAGE}:v6-${VANTAGE6_VERSION} \
		--tag ${REGISTRY}/${IMAGE}:latest \
		--platform ${PLATFORMS} \
		--build-arg TAG=${TAG} \
		--build-arg BASE=${BASE} \
		-f ./Dockerfile \
		$(if ${_condition_push},--push .,.)
