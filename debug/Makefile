IMAGENAME=registry.vantage6.local/omop-cohort-diagnostics-debug

#
# builds the debug image, after checking that the CohortDiagnostics directory exists
#
image: CohortDiagnostics FeatureExtraction CohortGenerator
	docker rmi -f ${IMAGENAME}
	# enable docker system prune when you want to be absolutely sure the image is being rebuilt completely
	#docker system prune -f
	docker build -t ${IMAGENAME} . 2>&1 | tee docker-build.log

#
# build image and make it available
# 
publish: image
	docker push ${IMAGENAME}
	$(MAKE) enable

#
# pushes the image to the local vantage6 instance (best to have a clean instance running, eg by running the test script there (`test/runsetup.sh`)
#
enable:
ifndef REQUESTS_CA_BUNDLE
	$(error Environment Variable REQUESTS_CA_BUNDLE should point to the .pem file of the local vantage6 installation)
endif
	python enable-debug-image.py

#
# do the user a favor if the R CohortDiagnostics package was not cloned yet
# v3.2.5 is the version currently in use by the vantage6 cohort_diagnostics base image
# 
CohortDiagnostics:
	git clone https://github.com/OHDSI/CohortDiagnostics.git
	cd CohortDiagnostics && git checkout v3.2.5

FeatureExtraction:
	git clone https://github.com/OHDSI/FeatureExtraction.git
	cd FeatureExtraction && git checkout v3.5.2

CohortGenerator:
	git clone https://github.com/OHDSI/CohortGenerator.git
	cd CohortGenerator && git checkout v0.9.0

clean:
	rm -rf CohortDiagnostics FeatureExtraction CohortGenerator
