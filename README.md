# process_ixbrl

A RESTful web service that receives an Inline XBRL file which may have an HTM, HTML or XHTML extension. The processor executes up to four operations based on parameters sent to the web service. These parameters and their associated actions are as follows:

1.  	VALIDATE - Validate the filing and return either a success code or a list of errors. Validation is to be performed against the taxonomy at https://raw.githubusercontent.com/xbrlus/acfr/v1.0RC11/acfr_all_2021-05-01.xsd. The validation algorithm is implemented in the Python open source tool named Arelle. See https://arelle.org/arelle/documentation/command-line-operation/. If errors are detected during the validation, they should be returned to the user.  If no errors are found, return the string “File successfully validated”
2.  	
3.  	STORE - Save the filing to the system that is running the web service
4.  	
5.  	PDF - Convert the Inline XBRL File to a PDF, store in on the server, and return it to the user. One library that can accomplish this is WeasyPrint (https://doc.courtbouillon.org/weasyprint/stable/) but there are several others.
6.  	
7.  	PARSE - Parse the file and output all tagged information as a CSV. Returned columns will include the item name, the value and some concepts derived from the contextRef that is provided in each of the document’s ix:nonFraction and ix:nonNumeric tags. 
