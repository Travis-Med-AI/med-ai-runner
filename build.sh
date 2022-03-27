docker build -f dockerfiles/Dockerfile -t tclarke104/med-ai-runner:0.1 .

docker build -f dockerfiles/worker.Dockerfile -t tclarke104/med-ai-runner-worker:0.1 .
docker build -f dockerfiles/beat.Dockerfile -t tclarke104/med-ai-runner-beat:0.1 .
docker build -f dockerfiles/results.Dockerfile -t tclarke104/med-ai-runner-results:0.1 .

docker build -f dockerfiles/orthanc.Dockerfile -t tclarke104/med-ai-orthanc:0.1 .
docker build -f dockerfiles/orthanc.public.Dockerfile -t tclarke104/med-ai-orthanc-public:0.1 .
