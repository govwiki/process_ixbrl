from asyncio import subprocess
import os
import string
from unittest import result
from urllib import response
from app import app
from flask import Flask, request, redirect, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
from importlib.resources import path
from fileinput import filename
import subprocess 
from weasyprint import HTML,CSS
from io import StringIO  # Python3
from importlib.resources import path
from nturl2path import url2pathname
import pandas as pd
import sys
from pandas import Series, DataFrame, Index
from decimal import Decimal
from ixbrl import XbrliDocument



try:
	ALLOWED_EXTENSIONS = set(['html','htm'])
	baseDomain = 'http://localhost:5000/'
	uploadDirectory = 'upload/'
	uploadDirectoryAbsolutePath = Path('upload').absolute()
 

	def allowed_file(filename):
		return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

	@app.route("/upload/<path:path>")
	def static_dir(path):
		print(path)
		return send_from_directory("upload", path)

	@app.route('/file-upload', methods=['POST'])

	def upload_file():
		try:
			# check if the post request has the file part
			if 'file' not in request.files:
				resp = jsonify({'message' : 'No file part in the request'})
				resp.status_code = 400
				return resp
			file = request.files['file']
			
			
			if file.filename == '':
				resp = jsonify({'message' : 'No file selected for uploading'})
				resp.status_code = 400
				return resp
			if file and allowed_file(file.filename):
				# Save HTM file
				htmlFileNameWithExt = secure_filename(file.filename)
				htmlFileNameWithoutExt = os.path.splitext(os.path.basename(htmlFileNameWithExt))[0]

				file.save(os.path.join(uploadDirectoryAbsolutePath, htmlFileNameWithExt))
				
				# Veriify HTM file
				htmlFileAbsolutePath=str(uploadDirectoryAbsolutePath)+"/"+htmlFileNameWithExt
				finalCommand = 'python3 Arelle-master/arelleCmdLine.py -f "https://raw.githubusercontent.com/xbrlus/acfr/v1.0RC11/acfr_all_2021-05-01.xsd" -i '+htmlFileAbsolutePath+' -v'
				print(finalCommand)
				os.system(finalCommand)				
				#output=subprocess.run([finalCommand],capture_output=True,text=True)
				#print(output.stdout)
				#print(output.stderr)	

				#logFileName = htmlFileNameWithoutExt+'.txt'
				#logFileAbsolutePath=str(uploadDirectoryAbsolutePath)+"/"+logFileName
				
				# Save PDF file
				pdfFileAbsolutePath=str(uploadDirectoryAbsolutePath)+"/"+htmlFileNameWithoutExt+'.pdf'
				css = CSS(string=''' @page {size: A1; margin: 0in 0.44in 0.2in 0.44in;} ''')
				HTML(htmlFileAbsolutePath).write_pdf(pdfFileAbsolutePath, stylesheets=[css])

				
				# Geenerate CSV file
				context = pd.DataFrame(columns=['contextref','dimension1','memberstring1','dimension2','memberstring2','instant','StartDate','EndDate'])
				ixdata = pd.DataFrame(columns=['document','itemname','contextref','value'])

				def display(text):

					''' Returns a display-friendly version of the text. '''
					return text.replace('acfr:','').replace('Axis','').replace('Member','')

				ixbrlDoc = XbrliDocument(path=htmlFileAbsolutePath)
				for contextObj in ixbrlDoc.contexts.values():
					dimension1 = dimension2 = dimension3 = memberstring1 = memberstring2 = memberstring3 = ''
					for index, explicitmember in enumerate(contextObj.explicit_members.values()):
						if index == 0:
							dimension1 = display(explicitmember.dimension)
							memberstring1 = display(explicitmember.string)
						if index == 1:
							dimension2 = display(explicitmember.dimension)
							memberstring2 = display(explicitmember.string)
						if index == 2:
							dimension3 = display(explicitmember.dimension)
							memberstring3 = display(explicitmember.string)
					tdimension1 = tdimension2 = tdimension3 = tmemberstring1 = tmemberstring2 = tmemberstring3 = ''
					for index, typedmember in enumerate(contextObj.typed_members.values()):
						if index == 0:
							tdimension1 = display(typedmember.dimension)
							tmemberstring1 = display(typedmember.string)
						if index == 1:
							tdimension2 = display(typedmember.dimension)
							tmemberstring2 = display(typedmember.string)
						if index == 2:
							tdimension3 = display(typedmember.dimension)
							tmemberstring3 = display(typedmember.string)
					context = context.append({'contextref': contextObj.id, 
												'dimension1': dimension1, 
												'memberstring1': memberstring1, 
												'dimension2': dimension2, 
												'memberstring2': memberstring2,
												'dimension3': dimension3, 
												'memberstring3': memberstring3,
												'tdimension1': tdimension1, 
												'tmemberstring1': tmemberstring1, 
												'tdimension2': tdimension2, 
												'tmemberstring2': tmemberstring2,
												'tdimension3': tdimension3, 
												'tmemberstring3': tmemberstring3,
												'instant': contextObj.instant, 
												'StartDate': contextObj.start_date, 
												'EndDate': contextObj.end_date}, ignore_index=True)
					
					# context = pd.concat([context, pd.Series([contextObj.id, 
					# 							dimension1, 
					# 							memberstring1, 
					# 							dimension2, 
					# 							memberstring2,
					# 							dimension3, 
					# 							memberstring3,
					# 							tdimension1, 
					# 							tmemberstring1, 
					# 							tdimension2, 
					# 							tmemberstring2,
					# 							tdimension3, 
					# 							tmemberstring3,
					# 							contextObj.instant, 
					# 							contextObj.start_date, 
					# 							contextObj.end_date])]);

				for ix_element in ixbrlDoc.ix_elements:
					if ix_element.tag.name.startswith('ix:non'):
						ixdata = ixdata.append({'document': htmlFileAbsolutePath[41:],  # Replace with NameOfGovernment When Available
												'itemname': display(ix_element.name), 
												'contextref' : ix_element.contextref, 
												'value': ix_element.string}, ignore_index=True)


						# ixdata = pd.concat([ixdata, pd.Series([htmlFileAbsolutePath[41:], 
						# 									display(ix_element.name), 
						# 									ix_element.contextref, 
						# 									ix_element.string])])
						

				#context.to_csv('context.csv', index=False)
				#ixdata.to_csv('ixdata.csv', index=False)
				#taxonomy_extract = pd.read_csv('TaxonomyExtract.csv', encoding='windows-1252')
				all_statements = pd.read_csv('AllStatements.csv', encoding='windows-1252')
				output=ixdata.merge(context, on='contextref').merge(all_statements, on='itemname').sort_values(by = ['document','itemname'])
				output.drop_duplicates(keep='first',inplace=True) 

				# delete duplicate linkages between government-wide and proprietary fund concepts
				output["StatementAndMember1"] = output["Statement"] + "|" + output["memberstring1"]
				#output.set_index('StatementAndMember1', inplace=True)
				#output.to_csv('output.csv', index=False)

				output = output.loc[output['StatementAndMember1'] != 'Statement of Net Position|ProprietaryFunds']
				output = output.loc[output['StatementAndMember1'] != 'Statement of Net Position|']
				output = output.loc[output['StatementAndMember1'] != 'Statement of Activities|ProprietaryFunds']
				output = output.loc[output['StatementAndMember1'] != 'Statement of Activities|']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|GovernmentalActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|BusinessTypeActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|PrimaryGovernmentActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|ComponentUnitDiscretelyPresented']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|GovernmentalActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|BusinessTypeActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|PrimaryGovernmentActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|ComponentUnitDiscretelyPresented']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|GovernmentalActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|BusinessTypeActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|PrimaryGovernmentActivities']
				output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|ComponentUnitDiscretelyPresented']

				csvFileAbsolutePath=str(uploadDirectoryAbsolutePath)+"/"+htmlFileNameWithoutExt+'.csv'
				output.to_csv(csvFileAbsolutePath, index=False, columns=['document','Statement','itemname','value','memberstring1','instant','StartDate','EndDate'])
				
				csvFileName = htmlFileNameWithoutExt+'.csv'
				pdfFileName = htmlFileNameWithoutExt+'.pdf'
				logFileName = htmlFileNameWithoutExt+'.txt'

				csvFileURL = baseDomain + uploadDirectory + csvFileName
				pdfFileURL = baseDomain + uploadDirectory + pdfFileName
				logFileURL = baseDomain + uploadDirectory + logFileName

				resp = jsonify({'message' : 'File successfully uploaded', 'csv':csvFileURL, 'pdf':pdfFileURL, 'log':logFileURL})
				resp.status_code = 201
				
				# logfile = subprocess.check_output([sys.executable, './main.py'])
				# with open('upload/'+logFileName, 'wb') as outfile:
				# 		outfile.write(logfile)

		
				return resp

			else:
				resp = jsonify({'message' : 'Allowed file types are html and htm'})
				resp.status_code = 400
				return resp
		except Exception as e:
				resp = jsonify({'message' : 'Sorry exception occurs'})
				resp.status_code = 400
				print(e)
				return resp


	if __name__ == "__main__":
		app.run()

except Exception as e:
	print(e)