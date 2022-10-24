# process_ixbrl

A RESTful web service that receives an Inline XBRL file which may have an HTM, HTML or XHTML extension. The processor executes up to four operations based on parameters sent to the web service. These parameters and their associated actions are as follows:

1.  	VALIDATE - Validate the filing and return either a success code or a list of errors. Validation is to be performed against the taxonomy at https://raw.githubusercontent.com/xbrlus/acfr/v1.0RC11/acfr_all_2021-05-01.xsd. The validation algorithm is implemented in the Python open source tool named Arelle. See https://arelle.org/arelle/documentation/command-line-operation/. If errors are detected during the validation, they should be returned to the user.  If no errors are found, return the string “File successfully validated”
2.  	
3.  	STORE - Save the filing to the system that is running the web service
4.  	
5.  	PDF - Convert the Inline XBRL File to a PDF, store in on the server, and return it to the user. One library that can accomplish this is WeasyPrint (https://doc.courtbouillon.org/weasyprint/stable/) but there are several others.
6.  	
7.  	CSV - Parse the file and output all tagged information as a CSV. Returned columns will include the item name, the value and some concepts derived from the contextRef that is provided in each of the document’s ix:nonFraction and ix:nonNumeric tags. 

## Dependencies  
- flask - Rest Framework  
- Waitress - Production grade server  
- arelle - xbrl open source library
- weasyprint - PDF generation library
- pandas - Python library

## Clone this repository

`Arelle` is a Git submodule. A regular `git clone` is not enough to retrieve
the submodule files. Use `git clone --recurse-submodules` instead.

# Docker

You need to make sure that Git submodules were downloaded before running
`docker compose up`.

## Run with Docker Compose

```
DOCKER_BUILDKIT=1 BASE_DOMAIN="http://localhost" docker compose up
```

## Ubuntu Server Setup Commands  
### To setup the ubuntu server execute the below commands  
    sudo apt-get upgrade  
    sudo apt-get update  
    sudo apt-get -y install python3-pip  
    pip3 --version  
    pip3 install Flask  
    pip3 install Flask-Waitress  
    pip3 install weasyprint  
    sudo apt-get install libpangocairo-1.0-0  
    pip3 install pandas  
    pip3 install bs4  
    pip3 install regex  
    pip3 install lxml  
    pip3 install isodate  
    
 # To run the project, execute below commands  
    cd python  
    nohup python3 main.py > log.txt 2>&1 &  
    
# Endpoint URL
    http://ec2-43-205-125-1.ap-south-1.compute.amazonaws.com:5000/file-upload

# Demo Video
    https://www.screencast.com/t/vCgydPNid
