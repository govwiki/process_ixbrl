import copy
import os
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from flask import request, jsonify, send_from_directory
from waitress import serve
from weasyprint import HTML, CSS
from ixbrlparse import IXBRL
from werkzeug.utils import secure_filename

from app import app
from ixbrl import XbrliDocument

ALLOWED_EXTENSIONS = set(['html', 'htm'])
try:
    baseDomain = os.environ['BASE_DOMAIN']
except KeyError:
    baseDomain = 'http://localhost:5000/'
uploadDirectory = 'upload/'
uploadDirectoryAbsolutePath = Path('upload').absolute()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload/<path:path>")
def static_dir(path):
    print(path)
    return send_from_directory("upload", path)


def add_page_breaks(html_file_absolute_path: str) -> str:
    # Open and parse the HTML file
    # TODO: Detect file encoding as it may be different
    with open(html_file_absolute_path, encoding="us-ascii") as html_to_parse_file:
        soup = BeautifulSoup(html_to_parse_file, 'html.parser')

    # Save the last page that contains "Reconciliation of Operating Income (Loss)
    # to Net Cash Provided (Used) by Operating Activities" table
    last_page = copy.copy(soup)

    # Delete the first div that contains the financial tables
    last_page.find('div', id=lambda x: x and x.startswith('t_ft_')).decompose()

    # Get a list of the two main divs (the first contains the financial
    # tables and the second contains the table saved in `last_page`)
    all_divs = soup.find_all('div', id=lambda x: x and x.startswith('t_ft_'))

    # Delete the table already saved in `last_page`
    all_divs[1].decompose()

    # Delete `colgroup` tag because it forces the columns width
    all_divs[0].find('colgroup').decompose()

    # Get all trs in the first div (containing the similar financial tables)
    # The HTML file contains one <table> that contains all the trs of all
    # the tables (not a standard way of using an HTML <table>).
    all_trs = all_divs[0].find_all('tr')

    # This variable saves each block of trs that contains rows related
    # to a single financial table.
    all_blocks_of_trs = []

    # An empty list that will save the next block of trs
    new_block_of_trs = []
    for tr in all_trs:
        # Use the tds that contain the word "COUNTY" as a separator
        if tr.find(lambda x: x.name == "td" and "COUNTY" in x.text):
            # Each time we find the word "COUNTY", we append the previous
            # block of trs and start a new one.
            # We need to check the length of the list because the first
            # block will be empty when the first row contains the word
            # "COUNTY".
            if len(new_block_of_trs) > 0:
                all_blocks_of_trs.append(new_block_of_trs)
            new_block_of_trs = []

        # In both cases (either starting a new block or continuing in the
        # same block), we need to append the current tr.
        new_block_of_trs.append(tr)

    # Each page contains the whole HTML markup but with
    # altered trs (only the trs related to the current
    # financial table should be left).
    all_pages = []
    for block_of_trs in all_blocks_of_trs:
        # We clone the original BeautifulSoup object for each
        # new page.
        new_page = copy.copy(soup)

        # `tbody` is the tag that contains all the trs. It should be
        # first cleared.
        tbody_element = new_page.find('div', id=lambda x: x and x.startswith('t_ft_')).find('tbody')
        tbody_element.clear()

        # We assign the current block of trs to the `tbody`
        tbody_element.contents = block_of_trs

        # We append the current page
        all_pages.append(new_page
                         .find('div', id=lambda x: x and x.startswith('t_ft_'))
                         .prettify())

    # The last page is special because its table is not
    # included with the first financial tables (inspect the HTML input
    # to understand the difference).
    all_pages.append(last_page
                     .find('div', id=lambda x: x and x.startswith('t_ft_'))
                     .prettify())

    # Join all the pages
    return '\n'.join(all_pages)


@app.route('/file-upload', methods=['POST'])
def upload_file():
    try:
        # check if the post request has the file part
        if 'file' not in request.files:
            resp = jsonify({'status': 'error', 'message': 'No file part in the request'})
            resp.status_code = 400
            return resp
        file = request.files['file']

        if file.filename == '':
            resp = jsonify({'status': 'error', 'message': 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            # Save HTM file
            htmlFileNameWithExt = secure_filename(file.filename)
            htmlFileNameWithoutExt = os.path.splitext(os.path.basename(htmlFileNameWithExt))[0]
            csvFileName = htmlFileNameWithoutExt + '.csv'
            pdfFileName = htmlFileNameWithoutExt + '.pdf'
            logFileName = htmlFileNameWithoutExt + '.txt'

            file.save(os.path.join(uploadDirectoryAbsolutePath, htmlFileNameWithExt))

            # Veriify HTM file
            htmlFileAbsolutePath = str(uploadDirectoryAbsolutePath) + "/" + htmlFileNameWithExt
            logFileAbsolutePath = str(uploadDirectoryAbsolutePath) + "/" + logFileName
            finalCommand = 'python3 Arelle/arelleCmdLine.py -f "https://raw.githubusercontent.com/xbrlus/acfr/v1.0RC11/acfr_all_2021-05-01.xsd" -i ' + htmlFileAbsolutePath + ' -v --logFile ' + logFileAbsolutePath
            print(finalCommand)
            # os.system(finalCommand)

            # This makes `weasyprint` add each financial table in a different page
            html_with_page_breaks = add_page_breaks(htmlFileAbsolutePath)

            # Use a smaller font size (because some tables do not fit horizontally)
            html_with_page_breaks = html_with_page_breaks.replace('font-size: 8pt;', 'font-size: 6pt;')

            # Use a smaller row height (because some tables do not fit vertically)
            html_with_page_breaks = html_with_page_breaks.replace('height: 12px;', 'height: 11px;')

            # Make the first column width 50px smaller (it has a lot of empty space)
            html_with_page_breaks = html_with_page_breaks.replace('width: 325.469px;', 'width: 255.469px;')

            # 780pt is the original table width (1038 in px)
            # Make it 50px smaller (otherwise the first column width will stay the same)
            html_with_page_breaks = html_with_page_breaks.replace('width: 780pt;', 'width: 988px;')

            # Save PDF file
            pdfFileAbsolutePath = str(uploadDirectoryAbsolutePath) + "/" + htmlFileNameWithoutExt + '.pdf'
            css = CSS(string=''' @page {size: letter landscape; margin: 0.1in 0.05in;} ''')
            HTML(string=html_with_page_breaks).write_pdf(pdfFileAbsolutePath, stylesheets=[css])

            # Geenerate CSV file
            context = pd.DataFrame(
                columns=['contextref', 'dimension1', 'memberstring1', 'dimension2', 'memberstring2', 'instant',
                         'StartDate', 'EndDate'])
            ixdata = pd.DataFrame(columns=['document', 'itemname', 'contextref', 'value'])

            def display(text):

                ''' Returns a display-friendly version of the text. '''
                return text.replace('acfr:', '').replace('Axis', '').replace('Member', '')

            ixbrlDoc = XbrliDocument(path=htmlFileAbsolutePath)

            with open(htmlFileAbsolutePath, encoding="us-ascii") as html_to_parse_file:
                parsed_ixbrl = IXBRL(html_to_parse_file)

            for contextObj in parsed_ixbrl.contexts.values():
                dimension1 = dimension2 = dimension3 = memberstring1 = memberstring2 = memberstring3 = ''
                tdimension1 = tdimension2 = tdimension3 = tmemberstring1 = tmemberstring2 = tmemberstring3 = ''
                if contextObj.segments:
                    for index, member in enumerate(contextObj.segments):
                        if member['tag'] == 'explicitmember':
                            explicitmember = member
                            if index == 0:
                                dimension1 = display(explicitmember['dimension'])
                                memberstring1 = display(explicitmember['value'])
                            if index == 1:
                                dimension2 = display(explicitmember['dimension'])
                                memberstring2 = display(explicitmember['value'])
                            if index == 2:
                                dimension3 = display(explicitmember['dimension'])
                                memberstring3 = display(explicitmember['value'])

                        if member['tag'] == "typedmember":
                            typedmember = member
                            if index == 0:
                                tdimension1 = display(typedmember['dimension'])
                                tmemberstring1 = display(typedmember['value'])
                            if index == 1:
                                tdimension2 = display(typedmember['dimension'])
                                tmemberstring2 = display(typedmember['value'])
                            if index == 2:
                                tdimension3 = display(typedmember['dimension'])
                                tmemberstring3 = display(typedmember['value'])

                if not dimension1 or not dimension1.strip():
                    dimension1 = tdimension1
                if not memberstring1 or not memberstring1.strip():
                    memberstring1 = tmemberstring1

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
                                          'StartDate': contextObj.startdate,
                                          'EndDate': contextObj.enddate}, ignore_index=True)

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
                    document_name = os.path.basename(htmlFileAbsolutePath)
                    ixdata = ixdata.append(
                        {'document': document_name,  # Replace with NameOfGovernment When Available
                         'itemname': display(ix_element.name),
                         'contextref': ix_element.contextref,
                         'value': ix_element.string}, ignore_index=True)

                # ixdata = pd.concat([ixdata, pd.Series([htmlFileAbsolutePath[41:],
                # 									display(ix_element.name),
                # 									ix_element.contextref,
                # 									ix_element.string])])

            # context.to_csv('context.csv', index=False)
            # ixdata.to_csv('ixdata.csv', index=False)
            # taxonomy_extract = pd.read_csv('TaxonomyExtract.csv', encoding='windows-1252')
            all_statements = pd.read_csv('AllStatements.csv', encoding='windows-1252')
            output = ixdata.merge(context, on='contextref').merge(all_statements, on='itemname').sort_values(
                by=['document', 'itemname'])
            output.drop_duplicates(keep='first', inplace=True)

            # delete duplicate linkages between government-wide and proprietary fund concepts
            output["StatementAndMember1"] = output["Statement"] + "|" + output["memberstring1"]
            # output.set_index('StatementAndMember1', inplace=True)
            # output.to_csv('output.csv', index=False)

            output = output.loc[output['StatementAndMember1'] != 'Statement of Net Position|ProprietaryFunds']
            output = output.loc[output['StatementAndMember1'] != 'Statement of Net Position|']
            output = output.loc[output['StatementAndMember1'] != 'Statement of Activities|ProprietaryFunds']
            output = output.loc[output['StatementAndMember1'] != 'Statement of Activities|']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Net Position|GovernmentalActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Net Position|BusinessTypeActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Net Position|PrimaryGovernmentActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Net Position|ComponentUnitDiscretelyPresented']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|GovernmentalActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|BusinessTypeActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|PrimaryGovernmentActivities']
            output = output.loc[output[
                                    'StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|ComponentUnitDiscretelyPresented']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|GovernmentalActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|BusinessTypeActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|PrimaryGovernmentActivities']
            output = output.loc[
                output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|ComponentUnitDiscretelyPresented']

            # Keep certain columns only
            output = output[['document', 'itemname', 'value', 'dimension1', 'memberstring1',
                             'dimension2', 'memberstring2', 'instant', 'StartDate', 'EndDate']]

            # Drop duplicates again (this time with the new set of columns)
            output.drop_duplicates(keep='first', inplace=True)

            csvFileAbsolutePath = str(uploadDirectoryAbsolutePath) + "/" + htmlFileNameWithoutExt + '.csv'
            output.to_csv(csvFileAbsolutePath, index=False)

            csvFileURL = baseDomain.rstrip('/') + '/' + uploadDirectory + csvFileName
            pdfFileURL = baseDomain.rstrip('/') + '/' + uploadDirectory + pdfFileName
            logFileURL = baseDomain.rstrip('/') + '/' + uploadDirectory + logFileName

            resp = jsonify({'status': 'success', 'message': 'File successfully uploaded',
                            'data': {'csv': csvFileURL, 'pdf': pdfFileURL, 'log': logFileURL}})
            resp.status_code = 200

            return resp

        else:
            resp = jsonify({'status': 'error', 'message': 'Allowed file types are html and htm'})
            resp.status_code = 400
            return resp
    except Exception as e:
        resp = jsonify({'status': 'error', 'message': 'Sorry exception occurs'})
        resp.status_code = 400
        print(e)
        return resp


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
# app.run(host='0.0.0.0', port=5000)
