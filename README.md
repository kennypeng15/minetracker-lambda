# minetracker-lambda
AWS Lambda function that scrapes and persists (to DynamoDB) minesweeper.online game data from a URL provided in an SNS event payload.

# credits:
- To [umihico's](https://github.com/umihico) [docker-selenium-lambda](https://github.com/umihico/docker-selenium-lambda) repository, which served as the basis for this code's Dockerfile
- AWS documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions

# updating steps:
- (these are largely available from the AWS ECR page, but here as a reference)
- after code is updated, save, and build a docker image locally
- tag and push the image to ECR
- from the Lambda console, redeploy the image, testing if desired
- (cleanup): delete the old local image and old image in ECR

# important lambda configuration values:
- ephemeral storage: left as default 512MB
- memory: 1024 MB
- set retries to 0
- timeout: 20s
