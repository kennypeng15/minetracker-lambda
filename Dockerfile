FROM public.ecr.aws/lambda/python:3.11 as build

# install chrome and our chrome driver, necessary for web scraping
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chromedriver-linux64.zip" && \
    curl -Lo "/tmp/chrome-linux64.zip" "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chrome-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    unzip /tmp/chrome-linux64.zip -d /opt/

# install some other necessary packages
FROM public.ecr.aws/lambda/python:3.11
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

# copy our requirements.txt file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# install the packages in requirements.txt
RUN pip install -r requirements.txt

# copy over chrome and chromedriver to desired locations
COPY --from=build /opt/chrome-linux64 /opt/chrome
COPY --from=build /opt/chromedriver-linux64 /opt/

# copy function code and the .env file 
COPY main.py ${LAMBDA_TASK_ROOT}
COPY .env ${LAMBDA_TASK_ROOT}

# set the CMD properly
CMD [ "main.handler" ]