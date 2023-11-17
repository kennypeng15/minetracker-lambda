# minetracker-lambda
AWS Lambda function that scrapes and persists (to DynamoDB) minesweeper.online game data from a URL provided in an SNS event payload.

# credits:
- To [umihico's](https://github.com/umihico) [docker-selenium-lambda](https://github.com/umihico/docker-selenium-lambda) repository, which served as the basis for this code's Dockerfile
- AWS documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions

# considerations:
- only games that have >= 50% solve percentage are persisted, to avoid noise.

# updating steps:
- (these are largely available from the AWS ECR page, but here as a reference)
- after code is updated, save, and build a docker image locally
- tag and push the image to ECR
- from the Lambda console, redeploy the image, testing if desired
- (cleanup): delete the old local image and old image in ECR

# important lambda configuration values:
- ephemeral storage: left as default 512MB
- memory: 1024 MB
- set retries to 1
    - debate: should this be 1? or 0? or 2?
    - there are 3 main kinds of errors that pop up:
    - timeout errors (which just happen, and can lead to actual data loss)
    - element not found errors (which mean that the game actually wasn't played)
    - webdriver exception errors (oopsie on the webdriver side) (can lead to actual dats loss as well)
    - so if we set to 1 and just assume that the true number of element not founds is true, maybe we'll have more success ...
    - changed to 1.
    - still, some things slip through the cracks - could consider upping to 2 ...
- timeout: 20s
- be sure to configure the cloudwatch log group for your lambda to not have permanent retention!

# debugging:
- failures are dumped into an SQS queue, where they can be inspected manually
- future work could involve a programmatic way to deal with these SQS events