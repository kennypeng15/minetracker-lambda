# minetracker-lambda
---

## Overview and Design
An AWS Lambda function that scrapes and persists (to DynamoDB) data about minesweeper.online games from a URL provided in an SNS event payload.

The `selenium` library is used to scrape the URL provided via SNS. After scraping, relevant data is parsed out, 
converted to any necessary data types, and then written to DynamoDB using `boto3`. 
Along with scraped game data, the timestamp passed in as part of the SNS event payload is also written to DynamoDB.
Only data from games >= 50% solved is persisted, to avoid noise.

Validation of the scraped URLs takes place to verify that games were played by the intended user.

This code is intended to be built as a Docker image, which is then published to Amazon ECR (private), where it then 
serves as the base image for a Lambda function invoked from SNS.

The Docker image (and thus Dockerfile) includes the aforementioned `boto3` and `selenium` libraries, as well as `python-dotenv` for secrets.
More importantly, it also includes a Chrome for Linux binary and a corresponding Chromedriver (necessary for 
programatically accessing and scraping URLs), as pre-packaged Lambda images do not have those available.

## Inspiration and Credits
The Dockerfile of this repository is largely based on [umihico's](https://github.com/umihico) 
[docker-selenium-lambda](https://github.com/umihico/docker-selenium-lambda) repository.

Inspiration was also drawn froom AWS documentation (https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions).

## Updating the Lambda:
Steps (i.e., specific command line instructions) for updating ECR and thus the Lambda function in AWS itself are available 
on the AWS ECR private page. In essence:
- After source code is updated, (and ideally, pushed to GitHub), build a Docker image locally.
- Authenticate with the AWS ECR private repository; tag and push the built image to ECR.
- From the Lambda console, redeploy the image (Lambda function page -> Image tab -> Deploy new image).
- Delete the local image and the old image in ECR.

If any new Chrome or Chromedriver versions must be used, a list is available at https://googlechromelabs.github.io/chrome-for-testing/ .

## Configuring the Lambda
A `.env` file is expected.

The Lambda is currently configured with the following:
- Ephemeral storage: 512MB (default)
- Memory: 1024MB
- Retries: 1
- Timeout: 20s
- Invoked from SNS
- Failures sent to an SQS deadletter queue.

Note: personally, I have CloudWatch log groups NOT set for permanent retention.


## Future Work and Considerations
Debate: should retries be 1? 0? or 2?
- there are 3 main kinds of errors that pop up:
- timeout errors (which just happen, and can lead to actual data loss)
- element not found errors (which mean that the game actually wasn't played)
- webdriver exception errors (oopsie on the webdriver side) (can lead to actual dats loss as well)
- so if we set to 1 and just assume that the true number of element not founds is true, maybe we'll have more success ...
- changed to 1.
- still, some things slip through the cracks - could consider upping to 2 ...

Future work could involve writing a programmatic way to deal with things that end up in the SQS deadletter queue.
