# minetracker-lambda
AWS Lambda function that scrapes and persists (to DynamoDB) minesweeper.online game data from a URL provided in an SNS event payload.

# credits:
- To [umihico's](https://github.com/umihico) [docker-selenium-lambda](https://github.com/umihico/docker-selenium-lambda) repository, which served as the basis for this code's Dockerfile
- AWS documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions